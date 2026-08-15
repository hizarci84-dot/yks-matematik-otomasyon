import os
import sys
import json
import asyncio
import edge_tts

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from moviepy import ImageClip, AudioFileClip
from engine.story_generator import StoryGenerator

class ReelsVideoGenerator:
    def __init__(self, output_dir="dist/videos", voice="tr-TR-AhmetNeural"):
        self.output_dir = output_dir
        self.voice = voice
        os.makedirs(self.output_dir, exist_ok=True)
        self.story_gen = StoryGenerator()

    def build_narration_script(self, day_data):
        day_num = day_data["day"]
        title = day_data["title"]
        hook = day_data.get("hook", "")
        history = day_data.get("history", "")
        tyt_links = ", ".join(day_data.get("tyt_ayt_links", []))
        surprising_fact = day_data.get("surprising_fact", "")
        quiz = day_data.get("quiz", {})
        quiz_q = quiz.get("question", "")

        # Natural spoken Turkish narration
        script = (
            f"Müfit Hoca ile Matematik. Kaynak: Riyazihane. "
            f"YKS ve TYT AYT Zihin Haritasında bugün {day_num}. gün: {title}. "
            f"{hook} "
            f"{history} "
            f"Bu kavram TYT ve AYT sınavında {tyt_links} konularının temelini oluşturur. "
            f"Biliyor muydunuz? {surprising_fact}. "
            f"Günün sorusu: {quiz_q}. "
            f"Cevabınızı yorumlarda paylaşın! Unutmayın, matematik sadece formül değil, düşünme sanatıdır."
        )
        return script

    async def generate_voiceover(self, text, audio_path):
        communicate = edge_tts.Communicate(text, self.voice, rate="+5%", pitch="+0Hz")
        await communicate.save(audio_path)

    def generate_video(self, day_data, filename=None):
        day_num = day_data["day"]
        
        # 1. Generate base high-res Story graphic if not already generated
        story_img_path = self.story_gen.generate_story(day_data, filename=f"story_for_video_{day_num:03d}.jpg")
        
        # 2. Generate Voiceover Script & Audio
        script = self.build_narration_script(day_data)
        audio_path = os.path.join(self.output_dir, f"audio_day_{day_num:03d}.mp3")
        
        print(f"Synthesizing Turkish Neural Voiceover for Day {day_num}...")
        asyncio.run(self.generate_voiceover(script, audio_path))
        
        # 3. Create Video with MoviePy v2
        audio_clip = AudioFileClip(audio_path)
        duration = audio_clip.duration
        
        print(f"Rendering 9:16 Reels Video ({duration:.1f}s)...")
        image_clip = ImageClip(story_img_path).with_duration(duration)
        video = image_clip.with_audio(audio_clip)
        
        if filename is None:
            filename = f"reels_day_{day_num:03d}.mp4"
        out_video_path = os.path.join(self.output_dir, filename)
        
        video.write_videofile(
            out_video_path,
            fps=24,
            codec="libx264",
            audio_codec="aac",
            logger=None
        )
        
        # Cleanup temporary audio
        audio_clip.close()
        video.close()
        if os.path.exists(audio_path):
            os.remove(audio_path)
            
        print(f"SUCCESS: Generated Reels Video: {out_video_path}")
        return out_video_path

if __name__ == "__main__":
    with open("data/campaign_97_days.json", "r", encoding="utf-8") as f:
        days = json.load(f)

    reels_gen = ReelsVideoGenerator()
    
    # Test with Day 9 (Babil)
    d9 = next(x for x in days if x["day"] == 9)
    reels_gen.generate_video(d9)
