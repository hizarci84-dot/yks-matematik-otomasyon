import os
import re
import sys
import json
import asyncio
import subprocess
from datetime import datetime

# Configure UTF-8 for console output on Windows
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from notebooklm import (
    AuthError,
    NotebookLMClient,
    RateLimitError,
    SourceStatus,
    VideoFormat,
)
from notebooklm.paths import get_storage_path, master_token_path_for

from engine.short_video_processor import (
    process_all_videos,
    slugify_filename,
    sync_short_video_queue,
)
from engine.youtube_bridge import sync_to_youtube_automation

DEFAULT_NOTEBOOK_ID = "34bae0c9-0e63-4362-8113-38dd95e3ed43"
RAW_DIR = "hikaye videolari"
OUTPUT_DIR = "dist/stories/short_videos"
GENERATOR_STATE_FILE = "data/notebooklm_generator_state.json"
SHORT_VIDEO_STATE_FILE = "data/short_video_state.json"
MANIFEST_FILE = "data/short_videos_manifest.json"


def load_json(path, default):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def collect_covered_topics(short_video_state_path, gen_state, existing_videos):
    """Collect titles/slugs of all previously generated or queued videos to avoid repeats."""
    titles = []
    sv_state = load_json(short_video_state_path, {"published_history": [], "queue": []})
    for entry in sv_state.get("published_history", []):
        if entry.get("title"):
            titles.append(entry["title"])
    for entry in sv_state.get("queue", []):
        if entry.get("title"):
            titles.append(entry["title"])
    for entry in gen_state.get("generated_history", []):
        if entry.get("topic_title"):
            titles.append(entry["topic_title"])
    for art in existing_videos:
        if getattr(art, "title", None):
            titles.append(art.title)

    # Deduplicate preserving order
    seen = set()
    unique = []
    for t in titles:
        key = slugify_filename(f"{t}.mp4")
        if key not in seen:
            seen.add(key)
            unique.append(t)
    return unique, seen


def select_candidate_sources(ready_sources, gen_state):
    """Order sources by lowest prior usage count so all 32 sources get explored fairly."""
    usage = gen_state.get("source_usage_counts", {})
    return sorted(ready_sources, key=lambda s: (usage.get(s.id, 0), (s.title or "").lower()))


def parse_topic_response(raw_text, valid_source_ids):
    """Extract JSON topic plan from NotebookLM chat answer and validate source IDs."""
    text = (raw_text or "").strip()
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, flags=re.DOTALL)
    if fenced:
        text = fenced.group(1)
    else:
        brace = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if brace:
            text = brace.group(0)

    data = json.loads(text)
    topic_title = str(data.get("topic_title", "")).strip()
    instructions = str(data.get("instructions", "")).strip()
    raw_ids = data.get("source_ids") or []
    chosen_ids = [sid for sid in raw_ids if isinstance(sid, str) and sid in valid_source_ids]

    if not topic_title or not instructions or not chosen_ids:
        raise ValueError("Incomplete topic plan JSON from NotebookLM chat.")
    return topic_title, chosen_ids[:5], instructions


def fallback_topic_plan(ordered_sources):
    """Deterministic fallback choosing the least-used 3 sources if JSON parsing fails."""
    chosen = ordered_sources[: min(3, len(ordered_sources))]
    names = [s.title or s.id for s in chosen]
    topic_title = f"Matematikte Derin Bakis: {names[0][:42].strip()}"
    instructions = (
        f"Secili kaynaklara ({', '.join(names)}) dayanarak lise ve YKS ogrencileri icin "
        "ezber yerine kavramsal mantigi one cikaran, merak uyandirici bir giris cumlesiyle baslayan "
        "ve gunluk hayat veya sinav baglantisiyla biten kisa bir Turkce anlatim hazirla."
    )
    return topic_title, [s.id for s in chosen], instructions


async def plan_daily_topic(client, notebook_id, ready_sources, covered_titles, covered_slugs, gen_state):
    """Ask NotebookLM to select an uncovered topic and matching source_ids."""
    ordered_sources = select_candidate_sources(ready_sources, gen_state)
    valid_ids = {s.id for s in ready_sources}
    source_catalog = "\n".join(f"- ID: {s.id} | Başlık: {s.title}" for s in ordered_sources)
    covered_block = "\n".join(f"- {t}" for t in covered_titles) if covered_titles else "- (Henüz yok)"

    prompt = (
        "Instagram Hikaye (60 saniyelik Kısa Video) serisi için bu defterdeki kaynaklardan "
        "DAHA ÖNCE İŞLENMEMİŞ yepyeni, tek ve net bir konu seç.\n\n"
        "DAHA ÖNCE İŞLENEN KONULAR (BUNLARI KESİNLİKLE TEKRAR ETME):\n"
        f"{covered_block}\n\n"
        "KULLANILABİLİR KAYNAKLAR (üsttekiler henüz daha az kullanılmış kaynaklardır):\n"
        f"{source_catalog}\n\n"
        "GÖREV:\n"
        "1. Öncelikle daha az kullanılmış kaynaklardan birbirini tamamlayan 2 ile 4 adet kaynak seç.\n"
        "2. Müfit Hoca / Riyazihane yaklaşımıyla (ezber yerine mantık, matematik tarihi, kavramsal düşünme, "
        "TYT-AYT veya eğitim psikolojisi içgörüsü) öğrencilerde merak uyandıran yeni bir başlık belirle.\n"
        "3. Sadece aşağıdaki JSON formatında yanıt ver, başına veya sonuna başka açıklama ekleme:\n"
        "{\n"
        '  "topic_title": "Kısa ve çarpıcı Türkçe video başlığı (en fazla 60 karakter)",\n'
        '  "source_ids": ["secilen_id_1", "secilen_id_2"],\n'
        '  "instructions": "Videolu Özet için Türkçe üretim yönergesi (2-3 cümle: kanca giriş, seçilen kaynaklardan somut örnek ve sade çıkarım)"\n'
        "}"
    )

    try:
        ask_res = await client.chat.ask(notebook_id, prompt)
        topic_title, chosen_ids, instructions = parse_topic_response(ask_res.answer, valid_ids)
        if slugify_filename(f"{topic_title}.mp4") in covered_slugs:
            print("Chat returned an already covered title, switching to fallback selection...")
            return fallback_topic_plan(ordered_sources)
        return topic_title, chosen_ids, instructions
    except Exception as e:
        print(f"Topic planning via chat fell back to deterministic selector ({e})")
        return fallback_topic_plan(ordered_sources)


def safe_raw_filepath(raw_dir, topic_title):
    """Return a clean filesystem path under raw_dir without colliding with existing files."""
    os.makedirs(raw_dir, exist_ok=True)
    cleaned = re.sub(r'[\\/:*?"<>|]+', "_", topic_title).strip().strip(".")
    cleaned = re.sub(r"\s+", "_", cleaned) or f"video_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    candidate = os.path.join(raw_dir, f"{cleaned}.mp4")
    if os.path.exists(candidate):
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        candidate = os.path.join(raw_dir, f"{cleaned}_{stamp}.mp4")
    return candidate


def git_sync_and_push(commit_message):
    """Stage data & processed short videos, commit, rebase onto origin/main, and push."""
    no_win = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    print("\n🚀 Syncing newly queued video with GitHub (origin/main)...")
    subprocess.run(["git", "add", "data/", OUTPUT_DIR], check=True, creationflags=no_win)
    diff_check = subprocess.run(["git", "diff", "--staged", "--quiet"], creationflags=no_win)
    if diff_check.returncode != 0:
        subprocess.run(["git", "commit", "-m", commit_message], check=True, creationflags=no_win)
    subprocess.run(["git", "pull", "--rebase", "--autostash", "origin", "main"], check=True, creationflags=no_win)
    subprocess.run(["git", "push", "origin", "main"], check=True, creationflags=no_win)
    print("✅ GitHub push succeeded!")


async def generate_and_queue_daily_video(
    notebook_id=DEFAULT_NOTEBOOK_ID,
    dry_run=False,
    force=False,
    push=False,
    wait_timeout=900.0,
):
    storage_path = get_storage_path()
    master_path = master_token_path_for(storage_path)
    if (
        not os.environ.get("NOTEBOOKLM_AUTH_JSON")
        and not os.path.exists(storage_path)
        and not os.path.exists(master_path)
    ):
        raise AuthError(
            f"NotebookLM oturum dosyası bulunamadı: {storage_path}\n"
            "Lütfen önce 'NotebookLM_Giris_Yap.bat' dosyasına çift tıklayarak Google hesabınıza 1 kez giriş yapın."
        )

    if push and not dry_run:
        no_win = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        subprocess.run(["git", "pull", "--rebase", "--autostash", "origin", "main"], check=False, creationflags=no_win)

    gen_state = load_json(
        GENERATOR_STATE_FILE,
        {"last_generated_date": None, "source_usage_counts": {}, "generated_history": []},
    )
    today_str = datetime.now().strftime("%Y-%m-%d")
    if not force and not dry_run and gen_state.get("last_generated_date") == today_str:
        print(f"Bugün ({today_str}) için NotebookLM videosu zaten üretildi. Tekrar üretmek için --force kullanın.")
        return 0

    print("==================================================")
    print("🤖 NOTEBOOKLM GÜNLÜK SHORT VİDEO ÜRETİCİ")
    print(f"Notebook ID : {notebook_id}")
    print(f"Tarih       : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("==================================================")

    async with NotebookLMClient.from_storage() as client:
        sources = await client.sources.list(notebook_id)
        ready_sources = [s for s in sources if s.status == SourceStatus.READY]
        if not ready_sources:
            raise RuntimeError("Notebook içinde hazır (READY) kaynak bulunamadı!")

        existing_videos = await client.artifacts.list_video(notebook_id)
        covered_titles, covered_slugs = collect_covered_topics(
            SHORT_VIDEO_STATE_FILE, gen_state, existing_videos
        )

        topic_title, chosen_ids, instructions = await plan_daily_topic(
            client, notebook_id, ready_sources, covered_titles, covered_slugs, gen_state
        )

        source_map = {s.id: (s.title or s.id) for s in ready_sources}
        chosen_titles = [source_map.get(sid, sid) for sid in chosen_ids]

        print(f"\n📌 Seçilen Konu    : {topic_title}")
        print(f"📚 Seçilen Kaynaklar ({len(chosen_ids)} adet):")
        for t in chosen_titles:
            print(f"   - {t}")
        print(f"📝 Üretim Yönergesi : {instructions}\n")

        if dry_run:
            print("🧪 DRY-RUN tamamlandı. Video üretimi başlatılmadı.")
            return 0

        print("🎬 NotebookLM 'Kısa' (Short) video üretimi başlatılıyor (language=tr)...")
        try:
            gen_status = await client.artifacts.generate_video(
                notebook_id,
                source_ids=chosen_ids,
                language="tr",
                instructions=instructions,
                video_format=VideoFormat.SHORT,
            )
        except RateLimitError as e:
            print(f"⚠️ NotebookLM günlük kota / hız limitine ulaşıldı: {e}")
            return 2

        if gen_status.is_rate_limited:
            print(f"⚠️ NotebookLM günlük video kotası dolmuş görünüyor: {gen_status.error}")
            return 2
        if gen_status.is_failed:
            raise RuntimeError(f"Video üretimi başlatılamadı: {gen_status.error} ({gen_status.error_code})")

        print(f"⏳ Üretim görev ID: {gen_status.task_id}. Tamamlanması bekleniyor (max {int(wait_timeout)}s)...")
        final_status = await client.artifacts.wait_for_completion(
            notebook_id,
            gen_status.task_id,
            initial_interval=5.0,
            max_interval=15.0,
            timeout=wait_timeout,
        )

        if final_status.is_rate_limited:
            print(f"⚠️ Video üretimi kota nedeniyle durduruldu: {final_status.error}")
            return 2
        if not final_status.is_complete:
            raise RuntimeError(
                f"Video üretimi tamamlanamadı (status={final_status.status}, error={final_status.error})"
            )

        # Prefer NotebookLM's generated artifact title if present, else our planned title
        updated_videos = await client.artifacts.list_video(notebook_id)
        artifact_obj = next((a for a in updated_videos if a.id == gen_status.task_id), None)
        final_title = (artifact_obj.title.strip() if artifact_obj and artifact_obj.title else "") or topic_title

        raw_path = safe_raw_filepath(RAW_DIR, final_title)
        print(f"⬇️ Video indiriliyor: {raw_path} ...")
        await client.artifacts.download_video(notebook_id, raw_path, artifact_id=gen_status.task_id)
        print(f"✅ İndirildi: {raw_path} ({os.path.getsize(raw_path) / (1024*1024):.2f} MB)")

    # 2. Speed up to <=58.5s and sync queues (Instagram + YouTube)
    print("\n⚙️ FFmpeg ile <60 sn uyarlaması ve kuyruk güncellemesi yapılıyor...")
    items = process_all_videos(input_dir=RAW_DIR, output_dir=OUTPUT_DIR, target_duration=58.5)
    save_json(MANIFEST_FILE, items)
    queue_state = sync_short_video_queue(items, state_path=SHORT_VIDEO_STATE_FILE)
    sync_to_youtube_automation(SHORT_VIDEO_STATE_FILE)

    # 3. Record generator state & source rotation counts
    usage = gen_state.setdefault("source_usage_counts", {})
    for sid in chosen_ids:
        usage[sid] = usage.get(sid, 0) + 1

    processed_slug = os.path.splitext(slugify_filename(os.path.basename(raw_path)))[0]
    processed_item = next((x for x in items if x["slug"] == processed_slug), None)

    gen_state["last_generated_date"] = today_str
    gen_state.setdefault("generated_history", []).append({
        "date": today_str,
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "topic_title": final_title,
        "planned_title": topic_title,
        "artifact_id": gen_status.task_id,
        "source_ids": chosen_ids,
        "source_titles": chosen_titles,
        "raw_video_path": raw_path.replace("\\", "/"),
        "processed_video_path": processed_item["output_path"] if processed_item else None,
        "duration": round(processed_item["output_duration"], 2) if processed_item else None,
        "speed": round(processed_item["speed"], 2) if processed_item else None,
    })
    save_json(GENERATOR_STATE_FILE, gen_state)

    print(
        f"\n✨ TAMAMLANDI! '{final_title}' işlendi ve kuyruğa eklendi. "
        f"Kuyruktaki toplam video: {len(queue_state['queue'])}"
    )

    if push:
        git_sync_and_push(f"feat(auto-gen): NotebookLM günlük video eklendi - {final_title}")

    return 0


class _TeeStream:
    """Mirror stdout/stderr to a persistent log file for scheduled runs."""

    def __init__(self, primary, log_handle):
        self.primary = primary
        self.log_handle = log_handle

    def write(self, data):
        if self.primary is not None:
            self.primary.write(data)
        self.log_handle.write(data)

    def flush(self):
        if self.primary is not None:
            self.primary.flush()
        self.log_handle.flush()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Daily NotebookLM Short Video Generator & Queue Updater")
    parser.add_argument("--notebook-id", default=DEFAULT_NOTEBOOK_ID)
    parser.add_argument("--dry-run", action="store_true", help="Plan next topic/sources without generating video")
    parser.add_argument("--force", action="store_true", help="Generate even if already generated today")
    parser.add_argument("--push", action="store_true", help="Commit & push updated queue and processed mp4 to GitHub")
    parser.add_argument("--timeout", type=float, default=900.0, help="Max wait seconds for NotebookLM video generation")
    parser.add_argument("--log-file", default="notebooklm_daily_run.log")
    args = parser.parse_args()

    orig_stdout, orig_stderr = sys.stdout, sys.stderr
    log_fp = None
    if args.log_file and not args.dry_run:
        log_fp = open(args.log_file, "a", encoding="utf-8")
        log_fp.write(f"\n--- RUN {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---\n")
        sys.stdout = _TeeStream(orig_stdout, log_fp)
        sys.stderr = _TeeStream(orig_stderr, log_fp)

    try:
        exit_code = asyncio.run(
            generate_and_queue_daily_video(
                notebook_id=args.notebook_id,
                dry_run=args.dry_run,
                force=args.force,
                push=args.push,
                wait_timeout=args.timeout,
            )
        )
        sys.exit(exit_code)
    except AuthError as e:
        print(f"\n❌ OTURUM HATASI: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ HATA: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        sys.stdout = orig_stdout
        sys.stderr = orig_stderr
        if log_fp is not None:
            log_fp.flush()
            log_fp.close()
