import os
import sys
import json
import time
import random
import requests
import subprocess
import traceback
from datetime import datetime

# Configure UTF-8 for console output on Windows
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

try:
    from dotenv import load_dotenv
    env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
    load_dotenv(dotenv_path=env_path)
except Exception:
    pass

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from engine.multi_slide_generator import MultiSlideStoryGenerator
from engine.video_generator import ReelsVideoGenerator

class InstagramPublisher:
    def __init__(
        self,
        state_file="data/state.json",
        campaign_file="data/campaign_97_days.json",
        short_video_state_file="data/short_video_state.json",
    ):
        self.state_file = state_file
        self.campaign_file = campaign_file
        self.short_video_state_file = short_video_state_file
        
        # Meta Graph API (Official - Safe, permanent, 0% ban risk)
        self.account_id = os.environ.get("INSTAGRAM_ACCOUNT_ID", "").strip()
        self.access_token = os.environ.get("INSTAGRAM_ACCESS_TOKEN", "").strip()
        
        self.github_repo = os.environ.get("GITHUB_REPOSITORY", "hizarci84-dot/yks-matematik-otomasyon")
        self.github_ref = os.environ.get("GITHUB_REF_NAME", "main")
        
        self.multi_slide_gen = MultiSlideStoryGenerator()
        self.video_gen = ReelsVideoGenerator()

    def load_state(self):
        if not os.path.exists(self.state_file):
            return {"current_day": 1, "published_history": []}
        with open(self.state_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def save_state(self, state):
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)

    def load_short_video_state(self):
        if not os.path.exists(self.short_video_state_file):
            return {"last_published_date": None, "published_history": [], "queue": []}
        with open(self.short_video_state_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def save_short_video_state(self, state):
        with open(self.short_video_state_file, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)

    def load_day_data(self, day_num):
        with open(self.campaign_file, "r", encoding="utf-8") as f:
            days = json.load(f)
        day_data = next((d for d in days if d["day"] == day_num), None)
        return day_data

    def push_assets_to_github(self):
        """Pushes rendered slides to GitHub repository so they are instantly accessible via raw.githubusercontent.com."""
        try:
            print("🚀 Committing and pushing rendered slides to GitHub CDN...")
            subprocess.run(["git", "config", "--global", "user.name", "Müfit Hoca Bot"], check=False)
            subprocess.run(["git", "config", "--global", "user.email", "bot@mufithocailematematik.com"], check=False)
            subprocess.run(["git", "add", "dist/"], check=False)
            subprocess.run(["git", "commit", "-m", "chore: upload rendered story assets [skip ci]"], check=False)
            res = subprocess.run(["git", "push", "origin", self.github_ref], check=False, capture_output=True, text=True)
            print(f"Git push result: {res.stdout.strip()} {res.stderr.strip()}")
            time.sleep(3) # Wait for GitHub CDN propagation
        except Exception as e:
            print(f"Git push note: {e}")

    def _require_credentials(self):
        if not self.account_id or not self.access_token:
            raise Exception(
                "❌ HATA: INSTAGRAM_ACCOUNT_ID veya INSTAGRAM_ACCESS_TOKEN bulunamadı!\n"
                "Lütfen GitHub Repo -> Settings -> Secrets and variables -> Actions menüsünden "
                "INSTAGRAM_ACCOUNT_ID ve INSTAGRAM_ACCESS_TOKEN anahtarlarını ekleyin."
            )

    def _create_media_container(self, payload, timeout=30):
        create_url = f"https://graph.facebook.com/v20.0/{self.account_id}/media"
        res = requests.post(create_url, data={**payload, "access_token": self.access_token}, timeout=timeout)
        res_data = res.json()
        if "error" in res_data:
            raise Exception(f"Meta Graph API Create Container Error: {res_data['error']}")
        return res_data["id"]

    def _wait_for_container_ready(self, creation_id, label="Media", max_polls=24, poll_interval=5):
        status_url = f"https://graph.facebook.com/v20.0/{creation_id}"
        for p in range(max_polls):
            time.sleep(poll_interval)
            status_res = requests.get(
                status_url,
                params={"fields": "status_code,status", "access_token": self.access_token},
                timeout=20,
            )
            status_data = status_res.json()
            status_code = status_data.get("status_code", "")
            print(f"     [{label}] Status check {p+1}/{max_polls}: {status_code}")
            if status_code == "FINISHED":
                return True
            if status_code == "ERROR":
                raise Exception(f"{label} container error on Meta servers: {status_data}")
        raise Exception(f"{label} container timed out waiting for FINISHED (id={creation_id})")

    def _publish_media_container(self, creation_id, timeout=30):
        pub_url = f"https://graph.facebook.com/v20.0/{self.account_id}/media_publish"
        pub_res = requests.post(
            pub_url,
            data={"creation_id": creation_id, "access_token": self.access_token},
            timeout=timeout,
        )
        pub_data = pub_res.json()
        if "error" in pub_data:
            raise Exception(f"Meta Graph API Publish Error: {pub_data['error']}")
        return pub_data["id"]

    def upload_to_public_url(self, file_path):
        """Returns direct GitHub Raw URL or fallback uploader."""
        rel_path = os.path.relpath(file_path, start=os.getcwd()).replace("\\", "/")
        github_raw = f"https://raw.githubusercontent.com/{self.github_repo}/{self.github_ref}/{rel_path}"

        # Verify if GitHub Raw is accessible without downloading the full asset
        try:
            r = requests.head(github_raw, timeout=10, allow_redirects=True)
            if r.status_code == 200:
                print(f"  -> GitHub CDN Raw URL verified: {github_raw}")
                return github_raw
        except Exception:
            pass

        # Fallback to Catbox
        try:
            with open(file_path, "rb") as f:
                res = requests.post(
                    "https://catbox.moe/user/api.php",
                    data={"reqtype": "fileupload"},
                    files={"fileToUpload": f},
                    timeout=90,
                )
                if res.status_code == 200 and res.text.startswith("https://"):
                    url = res.text.strip()
                    print(f"  -> Fallback Catbox URL: {url}")
                    return url
        except Exception as e:
            print(f"  -> Catbox fallback note: {e}")

        return github_raw

    def publish_video_story(self, video_path, use_github_cdn=False):
        """Publish a single 9:16 (<60s) MP4 video to Instagram Stories via Meta Graph API."""
        self._require_credentials()
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")

        print("\n==================================================")
        print("🎬 PUBLISHING VIDEO STORY VIA META GRAPH API")
        print(f"Target Account ID: {self.account_id}")
        print(f"Video: {video_path}")
        print("==================================================")

        if use_github_cdn:
            self.push_assets_to_github()

        video_url = self.upload_to_public_url(video_path)
        creation_id = self._create_media_container(
            {"video_url": video_url, "media_type": "STORIES"},
            timeout=30,
        )
        print(f"  -> Story video container created: {creation_id}. Waiting for Meta processing...")
        self._wait_for_container_ready(creation_id, label="Story Video", max_polls=24, poll_interval=5)
        story_media_id = self._publish_media_container(creation_id, timeout=30)
        print(f"  ✅ SUCCESS: Video Story is live! (Media ID: {story_media_id})")

        return {
            "status": "success",
            "method": "official_meta_graph_api",
            "story_ids": [story_media_id],
            "video_url": video_url,
            "reels_id": None,
        }

    def publish_via_meta_graph_api(self, slide_paths, day_data=None, video_path=None, caption=""):
        """Official 100% safe Meta Graph API publishing for Stories and Reels."""
        print("\n==================================================")
        print("🚀 PUBLISHING VIA OFFICIAL META INSTAGRAM GRAPH API")
        print(f"Target Account ID: {self.account_id}")
        print("==================================================")

        # Ensure assets are on GitHub CDN first
        self.push_assets_to_github()

        published_story_ids = []

        # 1. Publish Story Slides in Sequence
        for i, slide_path in enumerate(slide_paths, start=1):
            print(f"\n[Story Slide {i}/{len(slide_paths)}] Processing {slide_path}...")
            image_url = self.upload_to_public_url(slide_path)

            creation_id = self._create_media_container(
                {"image_url": image_url, "media_type": "STORIES"},
                timeout=20,
            )
            print(f"  -> Story container created: {creation_id}")

            time.sleep(3) # Short buffer before publishing container

            story_media_id = self._publish_media_container(creation_id, timeout=20)
            print(f"  ✅ SUCCESS: Slide {i} is live on Instagram Stories! (Media ID: {story_media_id})")
            published_story_ids.append(story_media_id)

            if i < len(slide_paths):
                time.sleep(4)

        # 2. Publish Reels Video (if requested)
        reels_media_id = None
        if video_path and os.path.exists(video_path):
            print(f"\n[Reels Video] Processing {video_path}...")
            video_url = self.upload_to_public_url(video_path)
            try:
                creation_id = self._create_media_container(
                    {
                        "video_url": video_url,
                        "media_type": "REELS",
                        "caption": caption,
                        "share_to_feed": True,
                    },
                    timeout=30,
                )
                print(f"  -> Reels container created: {creation_id}. Waiting for processing...")
                self._wait_for_container_ready(creation_id, label="Reels", max_polls=15, poll_interval=6)
                reels_media_id = self._publish_media_container(creation_id, timeout=30)
                print(f"  ✅ SUCCESS: Reels Video is live! (Media ID: {reels_media_id})")
            except Exception as e:
                print(f"❌ Reels publish error: {e}")

        return {
            "status": "success",
            "method": "official_meta_graph_api",
            "story_ids": published_story_ids,
            "reels_id": reels_media_id
        }

    def build_reels_caption(self, day_data):
        day_num = day_data["day"]
        title = day_data["title"]
        hook = day_data.get("hook", "")
        history = day_data.get("history", "")
        tyt_links = ", ".join(day_data.get("tyt_ayt_links", []))
        surprising_fact = day_data.get("surprising_fact", "")
        quiz = day_data.get("quiz", {})
        quiz_q = quiz.get("question", "")
        quiz_opts = " | ".join([f"[{lbl}] {opt}" for lbl, opt in zip(["A", "B", "C", "D"], quiz.get("options", []))])

        caption = (
            f"📐 YKS & TYT-AYT ZİHİN HARİTASI • GÜN {day_num} / 97\n"
            f"📌 Konu: {title}\n\n"
            f"❓ \"{hook}\"\n\n"
            f"📜 Neden Doğdu? (Mantığı):\n{history}\n\n"
            f"🎯 Sınav Yansıması:\nBu kavram TYT/AYT'de {tyt_links} ünitelerinin temelidir.\n\n"
            f"💡 Şaşırtıcı Bilgi:\n{surprising_fact}\n\n"
            f"✍️ GÜNÜN SORUSU:\n{quiz_q}\n{quiz_opts}\n"
            f"👉 Doğru cevabınızı yorumlara yazın!\n\n"
            f"──────────────────\n"
            f"👨‍🏫 Hazırlayan: @mufithocailematematik\n"
            f"🏛️ Kaynak: @riyazihane (Matematik Deneyim Merkezi)\n"
            f"\"Matematik sadece formül değil; insanlığın düşünme tarihidir.\"\n\n"
            f"#yks #yks2026 #tyt #ayt #tytmatematik #aytmatematik #matematik "
            f"#zihinharitası #ykskampı #mufithocailematematik #riyazihane"
        )
        return caption

    def run_next_short_video(self, use_github_cdn=False):
        """Publish the next queued <60s short video story and advance the queue."""
        sv_state = self.load_short_video_state()
        queue = sv_state.get("queue", [])
        if not queue:
            print("Short video queue completed! No remaining videos in queue.")
            return False

        next_item = queue[0]
        video_path = next_item["video_path"]
        title = next_item.get("title", os.path.basename(video_path))
        print(f"==================================================")
        print(f"STARTING SHORT VIDEO STORY QUEUE: {title}")
        print(f"Remaining in queue (including this): {len(queue)}")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"==================================================")

        publish_result = self.publish_video_story(video_path, use_github_cdn=use_github_cdn)

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        history_entry = {
            "slug": next_item.get("slug"),
            "title": title,
            "source_file": next_item.get("source_file"),
            "sha256": next_item.get("sha256"),
            "video_path": video_path,
            "published_at": now_str,
            "result": publish_result,
        }
        sv_state.setdefault("published_history", []).append(history_entry)
        sv_state["queue"] = queue[1:]
        sv_state["last_published_date"] = now_str
        self.save_short_video_state(sv_state)

        print(f"\n✨ SUCCESS: '{title}' published to Stories! Remaining in queue: {len(sv_state['queue'])}.")
        return True

    def run_daily_publish(self, publish_video=False):
        state = self.load_state()
        curr_day = state.get("current_day", 1)
        total_days = state.get("total_days", 97)
        
        if curr_day > total_days:
            print(f"97-day slide campaign completed (day {curr_day} > {total_days}). Checking short video queue...")
            self.run_next_short_video(use_github_cdn=False)
            return

        print(f"==================================================")
        print(f"STARTING DAILY PUBLISH PIPELINE: DAY {curr_day} / {total_days}")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"==================================================")

        day_data = self.load_day_data(curr_day)
        if not day_data:
            print(f"Error: Day {curr_day} data not found in campaign JSON!")
            return

        # 1. Render 3-Slide Story Suite
        slide_paths = self.multi_slide_gen.generate_day_suite(day_data)
        
        # 2. Optionally Render Reels Video
        video_path = None
        if publish_video:
            video_path = self.video_gen.generate_video(day_data, filename=f"reels_day_{curr_day:03d}.mp4")

        # 3. Build Rich Caption
        caption = self.build_reels_caption(day_data)

        # 4. Publish to Instagram (Meta Official Graph API)
        self._require_credentials()

        publish_result = self.publish_via_meta_graph_api(
            slide_paths, day_data=day_data, video_path=video_path, caption=caption
        )

        # 5. Update State
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        history_entry = {
            "day": curr_day,
            "title": day_data["title"],
            "published_at": now_str,
            "result": publish_result
        }
        
        state["published_history"].append(history_entry)
        state["last_published_date"] = now_str
        state["current_day"] = curr_day + 1
        self.save_state(state)

        print(f"\n✨ SUCCESS: Day {curr_day} finished cleanly. Next run will be Day {curr_day + 1}.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Instagram Daily Campaign Publisher")
    parser.add_argument("--video", action="store_true", help="Also generate and publish Reels video")
    parser.add_argument("--day", type=int, default=None, help="Force specific day number")
    parser.add_argument("--short-video", default=None, help="Publish a standalone <60s 9:16 MP4 video directly to Instagram Stories")
    parser.add_argument("--next-short", action="store_true", help="Publish the next queued short video from data/short_video_state.json")
    parser.add_argument("--github-cdn", action="store_true", help="Commit & push --short-video asset to GitHub CDN before publishing")
    args = parser.parse_args()

    publisher = InstagramPublisher()

    try:
        if args.short_video:
            publisher.publish_video_story(args.short_video, use_github_cdn=args.github_cdn)
        elif args.next_short:
            publisher.run_next_short_video(use_github_cdn=args.github_cdn)
        else:
            if args.day is not None:
                state = publisher.load_state()
                state["current_day"] = args.day
                publisher.save_state(state)
            publisher.run_daily_publish(publish_video=args.video)
    except Exception as e:
        print("\n" + "="*50)
        print(f"FATAL ERROR IN PUBLISHER: {e}")
        traceback.print_exc()
        print("="*50 + "\n")
        sys.exit(1)
