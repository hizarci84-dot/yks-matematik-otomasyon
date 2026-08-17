import os
import sys
import json
import time
import requests
import traceback
from datetime import datetime

# Configure UTF-8 for console output on Windows
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from engine.multi_slide_generator import MultiSlideStoryGenerator
from engine.video_generator import ReelsVideoGenerator
from instagrapi.types import StoryPoll

class InstagramPublisher:
    def __init__(self, state_file="data/state.json", campaign_file="data/campaign_97_days.json"):
        self.state_file = state_file
        self.campaign_file = campaign_file
        
        # Method 1: Session-based login
        self.session_file = "data/ig_session.json"
        self.ig_sessionid = os.environ.get("IG_SESSIONID", "").strip()
        self.ig_username = os.environ.get("IG_USERNAME", "").strip()
        self.ig_password = os.environ.get("IG_PASSWORD", "").strip()
        
        # Method 2: Meta Graph API (Fallback)
        self.account_id = os.environ.get("INSTAGRAM_ACCOUNT_ID", "").strip()
        self.access_token = os.environ.get("INSTAGRAM_ACCESS_TOKEN", "").strip()
        
        self.github_repo = os.environ.get("GITHUB_REPOSITORY", "user/repo")
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

    def load_day_data(self, day_num):
        with open(self.campaign_file, "r", encoding="utf-8") as f:
            days = json.load(f)
        day_data = next((d for d in days if d["day"] == day_num), None)
        return day_data

    def setup_instagrapi_client(self):
        from instagrapi import Client
        
        cl = Client()
        cl.delay_range = [2, 4]
        cl.set_locale("tr_TR")
        cl.set_country(90)
        cl.set_timezone_offset(3 * 3600)
        
        # Mobile Android profile
        cl.set_device({
            "app_version": "315.0.0.38.109",
            "android_version": 33,
            "android_release": "13.0",
            "dpi": "480dpi",
            "resolution": "1080x2400",
            "manufacturer": "Samsung",
            "device": "SM-G998B",
            "model": "galaxy-s21-ultra",
            "cpu": "exynos2100",
            "version_code": "561657871"
        })
        cl.set_user_agent(
            "Instagram 315.0.0.38.109 Android (33/13.0; 480dpi; 1080x2400; Samsung; SM-G998B; galaxy-s21-ultra; exynos2100; tr_TR; 561657871)"
        )
        return cl

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

    def build_quiz_poll_sticker(self, quiz_data):
        """Construct an interactive poll/quiz sticker for Slide 3."""
        if not quiz_data:
            return None
            
        question = quiz_data.get("question", "Günün Sorusu")
        if len(question) > 60:
            question = "Günün YKS Sorusu:"
            
        options = quiz_data.get("options", [])
        if not options:
            return None

        clean_opts = [f"{lbl}) {opt[:25]}" for lbl, opt in zip(["A", "B", "C", "D"], options)]
        
        # Position the sticker directly over the options area
        poll = StoryPoll(
            question=question,
            options=clean_opts,
            x=0.5,
            y=0.58,
            width=0.86,
            height=0.36,
            is_multi_option=True,
            viewer_can_vote=True
        )
        return poll

    def publish_via_instagrapi(self, slide_paths, day_data=None, video_path=None, caption=""):
        """Publish 3-slide story sequence with interactive Quiz sticker."""
        cl = self.setup_instagrapi_client()
        logged_in = False
        
        # 1. Load session file
        if os.path.exists(self.session_file):
            try:
                print("Loading session from data/ig_session.json...")
                cl.load_settings(self.session_file)
                logged_in = True
                print("Successfully authenticated via cached session settings!")
            except Exception as e:
                print(f"Session file loading error: {e}")

        # 2. Session ID cookie fallback
        if not logged_in and self.ig_sessionid:
            try:
                print("Logging in using IG_SESSIONID cookie...")
                cl.login_by_sessionid(self.ig_sessionid)
                logged_in = True
                print("Session ID login successful!")
            except Exception as e:
                print(f"Session ID login failed: {e}")

        if not logged_in:
            raise Exception("Instagram authentication failed. Please check data/ig_session.json.")

        uploaded_story_ids = []
        max_retries = 3

        # Prepare Quiz Poll Sticker for Slide 3
        quiz_poll = None
        if day_data and "quiz" in day_data:
            quiz_poll = self.build_quiz_poll_sticker(day_data["quiz"])

        # Upload All 3 Slides in Sequence
        for i, slide_path in enumerate(slide_paths, start=1):
            print(f"Uploading Slide {i}/{len(slide_paths)}: {slide_path}...")
            slide_media = None
            
            # Slide 3 gets the interactive quiz poll sticker
            polls_to_attach = [quiz_poll] if (i == 3 and quiz_poll) else []

            for attempt in range(1, max_retries + 1):
                try:
                    time.sleep(2)
                    slide_media = cl.photo_upload_to_story(slide_path, polls=polls_to_attach)
                    print(f"SUCCESS: Slide {i} published live! Media ID: {slide_media.pk}")
                    uploaded_story_ids.append(str(slide_media.pk))
                    break
                except Exception as e:
                    print(f"Slide {i} attempt {attempt}/{max_retries} failed ({e}). Retrying in 4s...")
                    time.sleep(4)
                    if attempt == max_retries:
                        raise e

        # Upload Reels Video (if generated)
        reels_media = None
        if video_path and os.path.exists(video_path):
            print(f"Uploading Reels Video to Profile ({video_path})...")
            for attempt in range(1, max_retries + 1):
                try:
                    time.sleep(3)
                    reels_media = cl.clip_upload(video_path, caption=caption)
                    print(f"SUCCESS: Reels Video published live! Media ID: {reels_media.pk}")
                    break
                except Exception as e:
                    print(f"Reels attempt {attempt} failed: {e}")
                    time.sleep(5)

        return {
            "status": "success",
            "story_ids": uploaded_story_ids,
            "reels_id": str(reels_media.pk) if reels_media else None
        }

    def run_daily_publish(self, publish_video=False):
        state = self.load_state()
        curr_day = state.get("current_day", 1)
        total_days = state.get("total_days", 97)
        
        if curr_day > total_days:
            print(f"Campaign completed! Current day ({curr_day}) > Total days ({total_days}).")
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

        # 4. Publish to Instagram
        publish_result = None
        if os.path.exists(self.session_file) or self.ig_sessionid or self.ig_username:
            publish_result = self.publish_via_instagrapi(slide_paths, day_data=day_data, video_path=video_path, caption=caption)
        else:
            print("[MOCK / DRY-RUN]: No credentials found.")
            publish_result = {"status": "mock_success", "day": curr_day}

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

        print(f"SUCCESS: Day {curr_day} finished. Next run will be Day {curr_day + 1}.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Instagram Daily Campaign Publisher")
    parser.add_argument("--video", action="store_true", help="Also generate and publish Reels video")
    parser.add_argument("--day", type=int, default=None, help="Force specific day number")
    args = parser.parse_args()

    publisher = InstagramPublisher()
    
    if args.day is not None:
        state = publisher.load_state()
        state["current_day"] = args.day
        publisher.save_state(state)

    try:
        publisher.run_daily_publish(publish_video=args.video)
    except Exception as e:
        print("\n" + "="*50)
        print(f"FATAL ERROR IN PUBLISHER: {e}")
        traceback.print_exc()
        print("="*50 + "\n")
        sys.exit(1)
