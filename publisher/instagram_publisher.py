import os
import sys
import json
import time
import requests
from datetime import datetime

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from engine.story_generator import StoryGenerator
from engine.video_generator import ReelsVideoGenerator

class InstagramPublisher:
    def __init__(self, state_file="data/state.json", campaign_file="data/campaign_97_days.json"):
        self.state_file = state_file
        self.campaign_file = campaign_file
        
        # Method 1: Direct Login Credentials (No Meta App / Facebook required)
        self.ig_username = os.environ.get("IG_USERNAME")
        self.ig_password = os.environ.get("IG_PASSWORD")
        self.session_file = "data/ig_session.json"
        
        # Method 2: Meta Graph API (Optional)
        self.account_id = os.environ.get("INSTAGRAM_ACCOUNT_ID")
        self.access_token = os.environ.get("INSTAGRAM_ACCESS_TOKEN")
        
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
        """Direct publishing using Instagram credentials without Meta Developer App."""
        from instagrapi import Client
        
        cl = Client()
        
        # Try loading saved session first to avoid repeated logins
        session_loaded = False
        if os.path.exists(self.session_file):
            try:
                cl.load_settings(self.session_file)
                cl.login(self.ig_username, self.ig_password)
                session_loaded = True
                print("Logged in using existing Instagram session.")
            except Exception as e:
                print(f"Session expired or invalid, logging in fresh: {e}")

        if not session_loaded:
            print(f"Logging in to Instagram as @{self.ig_username}...")
            cl.login(self.ig_username, self.ig_password)
            cl.dump_settings(self.session_file)
            print("Session saved successfully.")

        # Upload Story
        print(f"Uploading Story to @{self.ig_username}...")
        media = cl.photo_upload_to_story(image_path)
        print(f"SUCCESS: Story uploaded live! Media ID: {media.pk}")

        # Optionally Upload Video as Reels
        if video_path and os.path.exists(video_path):
            print(f"Uploading Reels video to @{self.ig_username}...")
            clip = cl.clip_upload(video_path, caption=caption)
            print(f"SUCCESS: Reels uploaded live! Media ID: {clip.pk}")

        return {"status": "success", "story_id": str(media.pk)}

    def publish_via_graph_api(self, image_url):
        """Official Meta Graph API (fallback)."""
        container_url = f"https://graph.facebook.com/v19.0/{self.account_id}/media"
        params = {
            "image_url": image_url,
            "media_type": "STORIES",
            "access_token": self.access_token
        }
        res = requests.post(container_url, data=params).json()
        if "id" not in res:
            raise Exception(f"Failed to create story container: {res}")
            
        creation_id = res["id"]
        time.sleep(3)
        publish_url = f"https://graph.facebook.com/v19.0/{self.account_id}/media_publish"
        pub_res = requests.post(publish_url, data={"creation_id": creation_id, "access_token": self.access_token}).json()
        if "id" not in pub_res:
            raise Exception(f"Failed to publish story: {pub_res}")
        return pub_res

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
        if self.ig_username and self.ig_password:
            print("Using Direct Instagram Login (instagrapi)...")
            publish_result = self.publish_via_instagrapi(story_path, video_path=video_path, caption=caption)
        elif self.account_id and self.access_token:
            print("Using Meta Graph API...")
            public_img_url = f"https://raw.githubusercontent.com/{self.github_repo}/{self.github_ref}/dist/stories/day_{curr_day:03d}.jpg"
            publish_result = self.publish_via_graph_api(public_img_url)
        else:
            print("[DRY-RUN / MOCK MODE]: No Instagram credentials configured.")
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

    publisher.run_daily_publish(publish_video=args.video)
