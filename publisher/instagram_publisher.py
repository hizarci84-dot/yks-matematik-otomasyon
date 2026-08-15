import os
import sys
import json
import time
import requests
import traceback
from datetime import datetime

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from engine.story_generator import StoryGenerator
from engine.video_generator import ReelsVideoGenerator

class InstagramPublisher:
    def __init__(self, state_file="data/state.json", campaign_file="data/campaign_97_days.json"):
        self.state_file = state_file
        self.campaign_file = campaign_file
        
        # Method 1: Session-based login (Bypasses 429 DataCenter IP block completely)
        self.ig_sessionid = os.environ.get("IG_SESSIONID", "").strip()
        self.session_file = "data/ig_session.json"
        
        # Method 2: Username / Password (Fallback)
        self.ig_username = os.environ.get("IG_USERNAME", "").strip()
        self.ig_password = os.environ.get("IG_PASSWORD", "").strip()
        
        # Method 3: Meta Graph API (Fallback)
        self.account_id = os.environ.get("INSTAGRAM_ACCOUNT_ID", "").strip()
        self.access_token = os.environ.get("INSTAGRAM_ACCESS_TOKEN", "").strip()
        
        self.github_repo = os.environ.get("GITHUB_REPOSITORY", "user/repo")
        self.github_ref = os.environ.get("GITHUB_REF_NAME", "main")
        
        self.story_gen = StoryGenerator()
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

    def publish_via_instagrapi(self, image_path, video_path=None, caption=""):
        """Publish using instagrapi with session authentication."""
        from instagrapi import Client
        
        cl = Client()
        cl.delay_range = [2, 4]
        
        # 1. Try Session ID from GitHub Secrets (Most reliable in Cloud)
        logged_in = False
        if self.ig_sessionid:
            print("🔑 Logging in using IG_SESSIONID cookie...")
            try:
                cl.login_by_sessionid(self.ig_sessionid)
                logged_in = True
                print("✅ Successfully authenticated via IG_SESSIONID!")
            except Exception as e:
                print(f"⚠️ Session ID login failed: {e}")

        # 2. Try Cached Session File
        if not logged_in and os.path.exists(self.session_file):
            try:
                print("📁 Loading session from data/ig_session.json...")
                cl.load_settings(self.session_file)
                if self.ig_username and self.ig_password:
                    cl.login(self.ig_username, self.ig_password)
                logged_in = True
                print("✅ Successfully authenticated via ig_session.json!")
            except Exception as e:
                print(f"⚠️ Local session file login failed: {e}")

        # 3. Fallback to Username & Password
        if not logged_in and self.ig_username and self.ig_password:
            print(f"🔑 Attempting standard login for @{self.ig_username}...")
            cl.login(self.ig_username, self.ig_password)
            cl.dump_settings(self.session_file)
            logged_in = True
            print("✅ Login successful!")

        if not logged_in:
            raise Exception("No valid Instagram authentication method found (IG_SESSIONID or ig_session.json).")

        # Upload Story
        print(f"📤 Uploading Story ({image_path})...")
        media = cl.photo_upload_to_story(image_path)
        print(f"🎉 SUCCESS: Story published live! Media ID: {media.pk}")

        # Optionally Upload Reels
        if video_path and os.path.exists(video_path):
            print(f"📤 Uploading Reels video ({video_path})...")
            clip = cl.clip_upload(video_path, caption=caption)
            print(f"🎉 SUCCESS: Reels published live! Media ID: {clip.pk}")

        return {"status": "success", "story_id": str(media.pk)}

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

        # 1. Render High-Resolution Story Image
        story_path = self.story_gen.generate_story(day_data, filename=f"day_{curr_day:03d}.jpg")
        
        # 2. Optionally Render Reels Video
        video_path = None
        if publish_video:
            video_path = self.video_gen.generate_video(day_data, filename=f"reels_day_{curr_day:03d}.mp4")

        # 3. Publish to Instagram
        caption = (
            f"Gün {curr_day} / 97: {day_data['title']}\n\n"
            f"{day_data.get('hook', '')}\n\n"
            f"Müfit Hoca ile Matematik • Kaynak: @riyazihane\n"
            f"#yks #tyt #ayt #matematik #zihinharitası"
        )
        
        publish_result = None
        if self.ig_sessionid or os.path.exists(self.session_file) or (self.ig_username and self.ig_password):
            publish_result = self.publish_via_instagrapi(story_path, video_path=video_path, caption=caption)
        else:
            print("⚠️ [MOCK / DRY-RUN]: No credentials found in environment variables.")
            publish_result = {"status": "mock_success", "day": curr_day}

        # 4. Update State
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
