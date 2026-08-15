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

    def get_public_url(self, relative_path):
        """Constructs the raw GitHub URL for the image/video so Instagram API can fetch it."""
        # Convert backslashes to slashes
        clean_rel = relative_path.replace("\\", "/")
        if clean_rel.startswith("/"):
            clean_rel = clean_rel[1:]
        raw_url = f"https://raw.githubusercontent.com/{self.github_repo}/{self.github_ref}/{clean_rel}"
        return raw_url

    def publish_story_to_instagram(self, image_url):
        """Official Meta Instagram Graph API for Story Publishing."""
        if not self.account_id or not self.access_token:
            print("[DRY-RUN / MOCK MODE]: INSTAGRAM_ACCOUNT_ID or INSTAGRAM_ACCESS_TOKEN not configured.")
            print(f"[DRY-RUN]: Would publish Story from URL: {image_url}")
            return {"status": "mock_success", "id": "mock_story_id_12345"}

        # Step 1: Create Story Media Container
        container_url = f"https://graph.facebook.com/v19.0/{self.account_id}/media"
        params = {
            "image_url": image_url,
            "media_type": "STORIES",
            "access_token": self.access_token
        }
        
        print(f"Requesting Instagram Story Container for: {image_url}...")
        res = requests.post(container_url, data=params)
        res_data = res.json()
        
        if "id" not in res_data:
            raise Exception(f"Failed to create story container: {res_data}")
            
        creation_id = res_data["id"]
        print(f"Container created with ID: {creation_id}. Waiting for processing...")
        time.sleep(3)

        # Step 2: Publish Container
        publish_url = f"https://graph.facebook.com/v19.0/{self.account_id}/media_publish"
        publish_params = {
            "creation_id": creation_id,
            "access_token": self.access_token
        }
        
        pub_res = requests.post(publish_url, data=publish_params)
        pub_data = pub_res.json()
        
        if "id" not in pub_data:
            raise Exception(f"Failed to publish story: {pub_data}")
            
        print(f"SUCCESS: Story published live on Instagram! Media ID: {pub_data['id']}")
        return pub_data

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
        story_rel_path = f"dist/stories/day_{curr_day:03d}.jpg"
        self.story_gen.generate_story(day_data, filename=f"day_{curr_day:03d}.jpg")
        
        # 2. Optionally Render Reels Video
        if publish_video:
            video_rel_path = f"dist/videos/reels_day_{curr_day:03d}.mp4"
            self.video_gen.generate_video(day_data, filename=f"reels_day_{curr_day:03d}.mp4")

        # 3. Publish to Instagram
        public_img_url = self.get_public_url(story_rel_path)
        publish_result = self.publish_story_to_instagram(public_img_url)

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
