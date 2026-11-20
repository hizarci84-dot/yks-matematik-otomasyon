import os
import re
import json
import shutil


DEFAULT_YOUTUBE_PROJECT_DIR = r"c:\Users\hizar\OneDrive\Desktop\projeler\YOUTUBE OTOMASYON"
DEFAULT_SHORT_VIDEO_STATE = "data/short_video_state.json"
DEFAULT_DEST_SUBDIR = "HİKAYE SHORTS"
DEFAULT_SYNC_STATE_NAME = "hikaye_sync_state.json"


def format_clean_filename_stem(source_file, fallback_title=""):
    """Turn raw NotebookLM filenames into clean Turkish YouTube titles without extension."""
    stem = os.path.splitext(source_file)[0] if source_file else fallback_title
    stem = stem.replace("__", " - ")
    stem = re.sub(r"_70_i(?=_|$)", " 70'i", stem)
    stem = re.sub(r"Avrupa_ya(?=_|$)", "Avrupa'ya", stem)
    stem = stem.replace("_", " ")
    stem = re.sub(r"\s+", " ", stem).strip(" .-")
    stem = re.sub(r'[\\/:*?"<>|]+', "", stem).strip()
    return stem or "Matematik Hikayesi"


def _get_next_sequence_number(dest_dir):
    max_num = 0
    if os.path.isdir(dest_dir):
        for fname in os.listdir(dest_dir):
            m = re.match(r"^(\d+)", fname)
            if m:
                max_num = max(max_num, int(m.group(1)))
    return max_num + 1


def _load_ordered_story_entries(short_video_state_path):
    if not os.path.exists(short_video_state_path):
        return []
    with open(short_video_state_path, "r", encoding="utf-8") as f:
        state = json.load(f)

    ordered = []
    seen = set()
    for entry in state.get("published_history", []) + state.get("queue", []):
        slug = entry.get("slug")
        if not slug or slug in seen:
            continue
        seen.add(slug)
        ordered.append(entry)
    return ordered


def sync_to_youtube_automation(
    short_video_state_path=DEFAULT_SHORT_VIDEO_STATE,
    youtube_project_dir=DEFAULT_YOUTUBE_PROJECT_DIR,
    dest_subdir=DEFAULT_DEST_SUBDIR,
):
    """Copy processed <60s short videos into YOUTUBE OTOMASYON's HİKAYE SHORTS queue."""
    if not os.path.isdir(youtube_project_dir):
        print(f"YouTube otomasyon klasoru bulunamadi, kopru atlandi: {youtube_project_dir}")
        return {"synced": [], "total_synced": 0}

    dest_dir = os.path.join(youtube_project_dir, dest_subdir)
    sync_state_path = os.path.join(youtube_project_dir, DEFAULT_SYNC_STATE_NAME)
    os.makedirs(dest_dir, exist_ok=True)

    if os.path.exists(sync_state_path):
        with open(sync_state_path, "r", encoding="utf-8") as f:
            sync_state = json.load(f)
    else:
        sync_state = {"synced_slugs": [], "files": {}}

    synced_slugs = set(sync_state.get("synced_slugs", []))
    entries = _load_ordered_story_entries(short_video_state_path)

    newly_synced = []
    next_num = _get_next_sequence_number(dest_dir)

    for entry in entries:
        slug = entry["slug"]
        src_path = entry.get("video_path", "")
        if not src_path or not os.path.exists(src_path):
            continue
        if slug in synced_slugs:
            existing_dest = sync_state.get("files", {}).get(slug)
            if existing_dest and os.path.exists(os.path.join(dest_dir, existing_dest)):
                continue

        clean_stem = format_clean_filename_stem(entry.get("source_file", ""), entry.get("title", slug))
        dest_filename = f"{next_num:02d}-{clean_stem}.mp4"
        dest_path = os.path.join(dest_dir, dest_filename)
        shutil.copy2(src_path, dest_path)

        synced_slugs.add(slug)
        sync_state.setdefault("synced_slugs", [])
        if slug not in sync_state["synced_slugs"]:
            sync_state["synced_slugs"].append(slug)
        sync_state.setdefault("files", {})[slug] = dest_filename

        newly_synced.append(dest_filename)
        next_num += 1
        print(f"  -> YouTube kuyruguna eklendi: {dest_filename}")

    if newly_synced or not os.path.exists(sync_state_path):
        with open(sync_state_path, "w", encoding="utf-8") as f:
            json.dump(sync_state, f, ensure_ascii=False, indent=2)

    print(
        f"YouTube koprusu senkronize: {len(newly_synced)} yeni video eklendi "
        f"(toplam senkronize: {len(sync_state.get('synced_slugs', []))})."
    )
    return {"synced": newly_synced, "total_synced": len(sync_state.get("synced_slugs", []))}


if __name__ == "__main__":
    sync_to_youtube_automation()
