import os
from groq import Groq
from dotenv import dotenv_values
import json
from pathlib import Path

class VideoScriptGenerator:
    def __init__(self):
        # ---------------------------
        # Locate main folder and .env
        # ---------------------------
        self.main_folder = Path(__file__).parent.parent  # parent of scriptgen
        env_path = self.main_folder / ".env"
        counter_path = self.main_folder / "video_counter.txt"

        # Load .env if it exists
        if env_path.exists():
            self.env = dotenv_values(env_path)
        else:
            self.env = {}
            print(f"[warning] .env not found at {env_path}")

        # Fetch Groq API key
        self.GROQ_API_KEY = self.env.get("GROQ_API_KEY") or os.environ.get("GROQ_API_KEY")
        if not self.GROQ_API_KEY:
            raise ValueError("❌ No GROQ_API_KEY found. Place it in the main folder .env")

        # Initialize Groq client
        self.client = Groq(api_key=self.GROQ_API_KEY)
        print("[info] Groq client initialized successfully")

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
        # Prepare folder paths
        # ---------------------------
        self.video_folder = self.main_folder / "data" / self.video_number
        self.script_output_dir = self.video_folder / "video_script"
        self.script_output_dir.mkdir(parents=True, exist_ok=True)

        print(f"[info] Current video: {self.video_number}")
        print(f"[info] Video scripts will be saved to: {self.script_output_dir}")

        # System prompt for structured video script
        self.system_prompt = """
        You are a professional screenwriter and visual director. Generate a structured short video script in strict JSON format.

        REQUIREMENTS:
        - The user will provide the total video duration in seconds.
        - Divide the video into segments of exactly 5 seconds each.
        - Return EXACTLY the number of segments equal to (total_duration / 5) — no more, no less.

        Each segment must contain:
        1. dialogue: A spoken line of around **15-20 words**, crafted to fit approximately 5 seconds of natural speech. The dialogue should sound smooth, cinematic, and contextually meaningful.
        2. visualPrompt: A **richly descriptive** scene description matching the dialogue. Include atmosphere, lighting, setting details, emotions, environment, and visual elements that can guide an AI image generator (e.g., “cinematic sunset over a quiet city skyline with soft warm lighting and clouds drifting”).
        3. voiceTone: The emotional tone or delivery style (e.g., “calm”, “excited”, “mysterious”, “inspirational”, “sad”, etc.).

        Return ONLY a valid JSON array — no explanations, no markdown, no extra commentary.

        Example output for a 15-second video (3 segments):
        [
            {
                "dialogue": "The sun rises over a sleeping city, whispering promises of a brand new day ahead.",
                "visualPrompt": "Cinematic sunrise over a quiet city skyline with warm orange glow, soft clouds, and long shadows.",
                "voiceTone": "hopeful"
            },
            {
                "dialogue": "People begin to wake, dreams fading as footsteps fill the empty streets.",
                "visualPrompt": "Close-up of city streets slowly filling with people, soft morning light, lens flare, gentle motion.",
                "voiceTone": "reflective"
            },
            {
                "dialogue": "Every story begins somewhere, and this one starts with the light.",
                "visualPrompt": "Wide cinematic aerial of the glowing cityscape bathed in golden morning light.",
                "voiceTone": "inspirational"
            }
        ]
        """
        # self.system_prompt = """
        #     You are a professional screenwriter. Generate a structured video script in strict JSON format.

        #     REQUIREMENTS:
        #     - The user will provide the total video duration in seconds.
        #     - Divide the video into segments of 5 seconds each.
        #     - Return EXACTLY the number of segments equal to (total_duration / 5), no more, no less.
        #     - Each segment must contain:
        #         - dialogue: text to be spoken and should be of 15 to 20 words not more than that.
        #         - visualPrompt: description of the visual/background
        #         - voiceTone: tone of speech (e.g., happy, sad, curious)
        #     - Respond ONLY in JSON, no explanations, no markdown, no extra text.

        #     Example output for a 15-second video (3 segments):
        #     [
        #         {"dialogue": "Hello!", "visualPrompt": "Sunny park with birds", "voiceTone": "cheerful"},
        #         {"dialogue": "How are you?", "visualPrompt": "Close-up of face", "voiceTone": "curious"},
        #         {"dialogue": "Let's explore!", "visualPrompt": "Walking through a forest", "voiceTone": "excited"}
        #     ]
        # """


    def generate_video_script(self, user_input: str):
        """Generate structured video script using Groq API."""
        if not user_input.strip():
            return []

        try:
            completion = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_input}
                ],
                temperature=0.7,
                max_tokens=2048,
                stream=True
            )

            # Stream and collect content
            raw_content = ""
            for chunk in completion:
                if chunk.choices[0].delta.content:
                    raw_content += chunk.choices[0].delta.content

            raw_content = raw_content.strip()

            # Parse JSON
            scenes = json.loads(raw_content)
            return scenes

        except Exception as e:
            print(f"[error] Failed to generate video script: {e}")
            return []

    def save_script(self, scenes, filename="video_script.json"):
        """Save generated scenes to JSON inside the folder for the current video."""
        filepath = self.script_output_dir / filename
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(scenes, f, indent=4)
        print(f"[info] Video script saved at: {filepath}")
        return filepath


# ---------------------------
# Example usage
# ---------------------------
if __name__ == "__main__":
    generator = VideoScriptGenerator()
    user_input = "A 30-second video introducing Flying jatt"
    
    scenes = generator.generate_video_script(user_input)
    if scenes:
        print("[info] Generated scenes:")
        for i, scene in enumerate(scenes, 1):
            print(f"Scene {i}: {scene}")
        
        generator.save_script(scenes)
