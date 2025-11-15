import os
import json
from pathlib import Path
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips

class VideoMaker:
    """Video Maker - ONLY compiles images + audio into final video"""
    
    def __init__(self):
        # Get base directory
        self.BASE_DIR = Path(__file__).resolve().parent.parent
        
        # Read current video number
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

        # Set up paths
        self.data_dir = self.BASE_DIR / "data" / self.video_number
        self.image_dir = self.data_dir / "generated_image"
        self.audio_dir = self.data_dir / "generated_audio"
        self.script_dir = self.data_dir / "video_script"
        self.output_dir = self.data_dir / "generated_video"

        # Create output folder
        self.output_dir.mkdir(parents=True, exist_ok=True)

        print(f"[info] Video Maker initialized for video #{self.video_number}")

    def create_video(self):
        """Compile images and audio into final video"""
        script_path = self.script_dir / "video_script.json"
        
        if not script_path.exists():
            print(f"[error] Script not found at: {script_path}")
            return False

        # Load script
        with open(script_path, "r", encoding="utf-8") as f:
            scenes = json.load(f)

        print(f"\n{'='*60}")
        print(f"[info] Compiling video from {len(scenes)} scenes...")
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
            return False

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
            
            return True

        except Exception as e:
            print(f"[error] Failed to create final video: {e}")
            return False


if __name__ == "__main__":
    maker = VideoMaker()
    maker.create_video()
