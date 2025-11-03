import os
import sys
import json
import asyncio
from pathlib import Path
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips
from dotenv import dotenv_values

# Add parent directory to sys.path to import modules
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

# Import your existing modules
from script_gen.script_writer import VideoScriptGenerator
from images.image_fetcher import ImageGenerator
from tts.tts_engine import AudioGenerator

class VideoMaker:
    def __init__(self, topic=None, duration=30):
        """
        topic: user-specified video topic (e.g., 'AI Revolution')
        duration: total video duration in seconds (default 30)
        """
        # -------- Locate main folder --------
        self.BASE_DIR = BASE_DIR
        self.env = dotenv_values(self.BASE_DIR / ".env")

        self.topic = topic or "Default Topic"
        self.duration = duration

        # -------- Read current video number --------
        video_counter_path = self.BASE_DIR / "video_counter.txt"
        if not video_counter_path.exists():
            print("[warning] video_counter.txt not found, creating with value 1")
            with open(video_counter_path, "w") as f:
                f.write("1")
            self.video_number = "1"
        else:
            with open(video_counter_path, "r") as f:
                self.video_number = f.read().strip()

        if not self.video_number.isdigit():
            print("[warning] Invalid video number, defaulting to 1")
            self.video_number = "1"

        # -------- Paths --------
        # Note: Using 'data' (lowercase) to match your structure
        self.data_dir = self.BASE_DIR / "data" / self.video_number
        self.image_dir = self.data_dir / "generated_image"
        self.audio_dir = self.data_dir / "generated_audio"
        self.script_dir = self.data_dir / "video_script"
        self.output_dir = self.data_dir / "generated_video"

        # Create required folders
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.image_dir.mkdir(parents=True, exist_ok=True)
        self.audio_dir.mkdir(parents=True, exist_ok=True)
        self.script_dir.mkdir(parents=True, exist_ok=True)

        print(f"[info] Video Maker initialized for video #{self.video_number}")
        print(f"[info] Topic: {self.topic}")
        print(f"[info] Duration: {self.duration} seconds")

    # -------------------------------------------------
    # 1️⃣ Generate script, images, and audio
    # -------------------------------------------------
    def generate_assets(self):
        print(f"\n{'='*60}")
        print(f"[info] Step 1: Generating script for topic: {self.topic}")
        print(f"{'='*60}\n")
        
        script_writer = VideoScriptGenerator()
        
        # Create user prompt with duration
        user_prompt = f"A {self.duration}-second video about {self.topic}"
        scenes = script_writer.generate_video_script(user_prompt)

        if not scenes:
            print("[error] Failed to generate script!")
            return False

        # Save script JSON
        script_path = self.script_dir / "video_script.json"
        with open(script_path, "w", encoding="utf-8") as f:
            json.dump(scenes, f, indent=2, ensure_ascii=False)
        
        print(f"[success] Script generated with {len(scenes)} scenes")
        print(f"[info] Script saved to: {script_path}\n")

        print(f"{'='*60}")
        print(f"[info] Step 2: Generating images for each scene...")
        print(f"{'='*60}\n")
        
        image_gen = ImageGenerator()
        
        for i, scene in enumerate(scenes, start=1):
            # Use 'visualPrompt' from the script
            visual_prompt = scene.get("visualPrompt", "")
            if visual_prompt:
                print(f"[{i}/{len(scenes)}] Generating image...")
                image_gen.generate_image(visual_prompt, i)
            else:
                print(f"[warning] Scene {i} has no visualPrompt, skipping image")

        print(f"\n{'='*60}")
        print(f"[info] Step 3: Generating audio for each scene...")
        print(f"{'='*60}\n")
        
        audio_gen = AudioGenerator()
        
        # Run audio generation asynchronously
        async def generate_all_audio():
            for i, scene in enumerate(scenes, start=1):
                # Use 'dialogue' from the script
                dialogue = scene.get("dialogue", "")
                if dialogue:
                    print(f"[{i}/{len(scenes)}] Generating audio...")
                    await audio_gen.generate_audio(dialogue, i)
                else:
                    print(f"[warning] Scene {i} has no dialogue, skipping audio")
        
        # Run the async audio generation
        asyncio.run(generate_all_audio())

        print(f"\n{'='*60}")
        print("[✅] All assets generated successfully!")
        print(f"{'='*60}\n")
        return True

    # -------------------------------------------------
    # 2️⃣ Compile everything into a video
    # -------------------------------------------------
    def create_video(self):
        script_path = self.script_dir / "video_script.json"
        
        if not script_path.exists():
            print("[warning] No script found — generating assets now...")
            success = self.generate_assets()
            if not success:
                print("[error] Failed to generate assets. Cannot create video.")
                return

        # Load script
        with open(script_path, "r", encoding="utf-8") as f:
            scenes = json.load(f)

        print(f"\n{'='*60}")
        print(f"[info] Step 4: Compiling video from {len(scenes)} scenes...")
        print(f"{'='*60}\n")

        clips = []
        for i, scene in enumerate(scenes, start=1):
            img_path = self.image_dir / f"{i}.jpg"
            aud_path = self.audio_dir / f"{i}.mp3"

            if not img_path.exists():
                print(f"[warning] Skipping scene {i} - image not found: {img_path}")
                continue
            
            if not aud_path.exists():
                print(f"[warning] Skipping scene {i} - audio not found: {aud_path}")
                continue

            print(f"[{i}/{len(scenes)}] Adding scene to video...")

            try:
                audio_clip = AudioFileClip(str(aud_path))
                image_clip = ImageClip(str(img_path)).set_duration(audio_clip.duration)
                image_clip = image_clip.fadein(0.5).fadeout(0.5).set_audio(audio_clip)
                clips.append(image_clip)
            except Exception as e:
                print(f"[error] Failed to process scene {i}: {e}")
                continue

        if not clips:
            print("[error] No valid clips to compile. Video creation failed.")
            return

        print(f"\n[info] Concatenating {len(clips)} clips...")
        
        try:
            final_video = concatenate_videoclips(clips, method="compose")
            output_path = self.output_dir / f"final_video_{self.video_number}.mp4"

            print(f"[info] Rendering final video to: {output_path}")
            print("[info] This may take a few minutes...\n")

            final_video.write_videofile(
                str(output_path),
                fps=30,
                codec="libx264",
                audio_codec="aac",
                threads=4,
                preset='medium'
            )

            print(f"\n{'='*60}")
            print(f"[🎬] SUCCESS! Final video saved to:")
            print(f"    {output_path}")
            print(f"{'='*60}\n")
            
            # Increment video counter for next run
            self._increment_counter()

        except Exception as e:
            print(f"[error] Failed to create final video: {e}")

    def _increment_counter(self):
        """Increment the video counter for the next video"""
        counter_path = self.BASE_DIR / "video_counter.txt"
        try:
            next_num = int(self.video_number) + 1
            with open(counter_path, "w") as f:
                f.write(str(next_num))
            print(f"[info] Video counter incremented to {next_num}")
        except Exception as e:
            print(f"[warning] Could not increment counter: {e}")


def main():
    """Main entry point with user interaction"""
    print("\n" + "="*60)
    print("🎬 Welcome to AutoTube Video Maker!")
    print("="*60 + "\n")
    
    topic = input("🎤 Enter topic for your video: ").strip()
    if not topic:
        topic = "AI and the Future of Technology"
        print(f"[info] No topic provided, using default: {topic}")
    
    duration_input = input("⏱️  Enter video duration in seconds (default 30): ").strip()
    duration = int(duration_input) if duration_input.isdigit() else 30
    
    # Ensure duration is a multiple of 5
    if duration % 5 != 0:
        duration = ((duration // 5) + 1) * 5
        print(f"[info] Adjusted duration to {duration}s (must be multiple of 5)")
    
    print("\n" + "="*60)
    print("Starting video creation process...")
    print("="*60 + "\n")
    
    maker = VideoMaker(topic=topic, duration=duration)
    maker.generate_assets()
    maker.create_video()


if __name__ == "__main__":
    main()
