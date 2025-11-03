import os
import asyncio
from dotenv import dotenv_values
import edge_tts
from pathlib import Path

class AudioGenerator:
    def __init__(self):
        # ---------------------------
        # Setup main folder paths
        # ---------------------------
        self.BASE_DIR = Path(__file__).parent.parent
        self.data_dir = self.BASE_DIR / "Data"

        # Load .env
        env_path = self.BASE_DIR / ".env"
        self.env = dotenv_values(env_path) if env_path.exists() else {}

        # ---------------------------
        # Select a nice storytelling voice
        # ---------------------------
        # en-US-GuyNeural = natural storytelling male voice
        # en-US-JennyNeural = soft storytelling female voice
        self.voice = self.env.get("STORY_VOICE", "en-GB-RyanNeural")

        # Slightly slower rate, deeper pitch
        self.rate = "-5%"  
        self.pitch = "-2Hz"

        # Path to VideoCounter.txt
        self.counter_file = self.BASE_DIR / "video_counter.txt"

    def _get_video_number(self):
        """Fetch or create video counter number"""
        if not self.counter_file.exists():
            with open(self.counter_file, "w") as f:
                f.write("1")

        with open(self.counter_file, "r") as f:
            num = f.read().strip()

        # Default to 1 if empty or invalid
        return num if num.isdigit() else "1"

    async def generate_audio(self, text: str, number: int):
        """Generate audio for given text and save as numbered file"""
        if not text.strip():
            print("[warning] Empty text, skipping audio generation.")
            return

        video_num = self._get_video_number()
        audio_dir = self.data_dir / video_num / "generated_audio"
        audio_dir.mkdir(parents=True, exist_ok=True)

        output_path = audio_dir / f"{number}.mp3"

        print(f"[info] Generating audio: {output_path.name} → {self.voice}")

        try:
            communicate = edge_tts.Communicate(
                text, 
                self.voice, 
                rate=self.rate, 
                pitch=self.pitch
            )
            await communicate.save(str(output_path))
            print(f"[success] Saved audio at: {output_path}")
        except Exception as e:
            print(f"[error] Failed to generate audio: {e}")

# ---------------------------
# Example Usage
# ---------------------------
if __name__ == "__main__":
    text = "There was once a man who lived deep in the jungle, surrounded by the whispers of ancient trees."
    number = 1

    generator = AudioGenerator()
    asyncio.run(generator.generate_audio(text, number))
