import os
import requests
from pathlib import Path
from dotenv import dotenv_values

class ImageGenerator:
    def __init__(self):
        # ---------------------------
        # Locate the main folder's .env and VideoCounter.txt
        # ---------------------------
        self.main_folder = Path(__file__).parent.parent  # images/ -> main folder
        env_path = self.main_folder / ".env"
        counter_path = self.main_folder / "video_counter.txt"

        # Load environment
        if env_path.exists():
            self.env = dotenv_values(env_path)
        else:
            self.env = {}
            print(f"[warning] .env not found at {env_path}")

        # Fetch Hugging Face API key
        self.HF_API_KEY = self.env.get("HuggingFaceAPIKey") or os.environ.get("HuggingFaceAPIKey")
        if not self.HF_API_KEY:
            raise ValueError("❌ No HuggingFaceAPIKey found in main folder .env or environment variables.")

        # Hugging Face API setup
        self.API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
        self.headers = {"Authorization": f"Bearer {self.HF_API_KEY}"}

        # ---------------------------
        # Fetch current video number
        # ---------------------------
        if counter_path.exists():
            with open(counter_path, "r") as f:
                counter_value = f.read().strip()
                self.video_number = counter_value if counter_value.isdigit() else "1"
        else:
            print(f"[warning] {counter_path} not found, defaulting to 1")
            self.video_number = "1"

        # ---------------------------
        # Create folders dynamically
        # ---------------------------
        self.video_folder = self.main_folder / "data" / self.video_number
        self.output_dir = self.video_folder / "generated_image"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        print(f"[info] Current video: {self.video_number}")
        print(f"[info] Images will be saved to: {self.output_dir}")

    def generate_image(self, prompt: str, number: int):
        """
        Generate a single image for a given prompt and save it as {number}.jpg
        inside the folder corresponding to the current VideoCounter.txt value.
        """
        payload = {
            "inputs": f"{prompt}, ultra high resolution, cinematic lighting, 8k, news photography"
        }

        try:
            response = requests.post(self.API_URL, headers=self.headers, json=payload)
            if response.status_code == 200:
                image_path = self.output_dir / f"{number}.jpg"
                with open(image_path, "wb") as f:
                    f.write(response.content)
                print(f"[OK] Saved {image_path} for prompt: {prompt}")
            else:
                print(f"[ERR] Error {response.status_code}: {response.text}")

        except Exception as e:
            print(f"[ERR] Failed to generate image for prompt '{prompt}': {e}")


# ---------------------------
# Example usage
# ---------------------------
if __name__ == "__main__":
    generator = ImageGenerator()
    generator.generate_image("Close-up of AI assistant interface", 1)
