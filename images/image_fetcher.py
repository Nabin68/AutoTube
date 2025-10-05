import os
import requests
from pathlib import Path
from dotenv import dotenv_values

class ImageGenerator:
    def __init__(self):
        main_folder = Path(__file__).parent.parent  # images/ -> main folder
        env_path = main_folder / ".env"

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

        # Ensure generated_image folder exists in main_folder/data
        self.output_dir = main_folder / "data" / "generated_image"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        print(f"[info] Images will be saved to: {self.output_dir}")

    def generate_images(self, prompts: list, prefix: str):
        """
        Generate one image per prompt in the list and save as prefix.idx.jpg
        """
        for idx, prompt in enumerate(prompts, start=1):
            payload = {
                "inputs": f"{prompt}, ultra high resolution, cinematic lighting, 8k, news photography"
            }

            try:
                response = requests.post(self.API_URL, headers=self.headers, json=payload)
                if response.status_code == 200:
                    image_path = self.output_dir / f"{prefix}.{idx}.jpg"
                    with open(image_path, "wb") as f:
                        f.write(response.content)
                    print(f"[OK] Saved {image_path} for prompt: {prompt}")
                else:
                    print(f"[ERR] Error {response.status_code}: {response.text}")

            except Exception as e:
                print(f"[ERR] Failed to generate image for prompt '{prompt}': {e}")


# Usage example
if __name__ == "__main__":
    generator = ImageGenerator()
    prompts = [
        "Futuristic city skyline at sunset",
        "Close-up of AI assistant interface",
        "Animated code streaming across black screen"
    ]
    generator.generate_images(prompts, prefix="scene")
