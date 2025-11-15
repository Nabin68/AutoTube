#script_writer.py module

import os
from groq import Groq
from dotenv import dotenv_values
import json
import re
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
        
        # NEW: Create title_description folder
        self.title_desc_dir = self.video_folder / "title_description"
        self.title_desc_dir.mkdir(parents=True, exist_ok=True)

        print(f"[info] Current video: {self.video_number}")
        print(f"[info] Video scripts will be saved to: {self.script_output_dir}")
        print(f"[info] Title & description will be saved to: {self.title_desc_dir}")

        # System prompt for structured video script
        self.system_prompt = """
        You are a professional screenwriter and visual director. Generate a structured short video script in strict JSON format.

        REQUIREMENTS:
        - The user will provide the total video duration in seconds.
        - Divide the video into segments of exactly 5 seconds each.
        - Return EXACTLY the number of segments equal to (total_duration / 5) — no more, no less.

        Each segment must contain:
        1. dialogue: A spoken line of around **15-20 words**, crafted to fit approximately 5 seconds of natural speech. The dialogue should sound smooth, cinematic, and contextually meaningful.
        2. visualPrompt: A **richly descriptive** scene description matching the dialogue. Include atmosphere, lighting, setting details, emotions, environment, and visual elements that can guide an AI image generator (e.g., "cinematic sunset over a quiet city skyline with soft warm lighting and clouds drifting").
        3. voiceTone: The emotional tone or delivery style (e.g., "calm", "excited", "mysterious", "inspirational", "sad", etc.).

        CRITICAL: Return ONLY a valid JSON array. No markdown, no code blocks, no explanations, no extra text before or after the JSON.

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
        
        # NEW: System prompt for title and description
        self.title_desc_prompt = """
        You are an expert YouTube content strategist specializing in viral, high-CTR titles and descriptions.

        REQUIREMENTS FOR TITLE:
        - Create an EXTREMELY eye-catching, click-worthy title (50-70 characters)
        - Use power words and emotional triggers (Amazing, Shocking, Ultimate, Incredible, Mind-Blowing, Secret, Truth, etc.)
        - Include numbers, questions, or bold claims when relevant
        - Add intrigue or curiosity gap (e.g., "You Won't Believe...", "The Truth About...", "Why Nobody Talks About...")
        - Use capitalization strategically for emphasis
        - Make it informative AND exciting
        - Include emojis if they enhance the title (1-2 max)
        
        REQUIREMENTS FOR DESCRIPTION:
        - Write a compelling description (150-200 words) that includes:
          * Powerful hook in the first line that creates curiosity
          * Brief overview of the video content with exciting language
          * Key topics or highlights with emotional appeal
          * Strong call-to-action (like, subscribe, comment)
          * Relevant hashtags at the end (3-5 hashtags)
        
        Return ONLY a valid JSON object with two fields: "title" and "description"
        No markdown, no code blocks, no explanations.

        Example output:
        {
            "title": "⚡ Iron Man: The SHOCKING Truth Behind Tony Stark's Genius! 🔥",
            "description": "What if I told you Iron Man's greatest power ISN'T his suit? 🤯 Dive deep into the untold story of Tony Stark - the brilliant, flawed genius who revolutionized the Marvel Universe! From his darkest moments in that cave to his ultimate sacrifice, discover the secrets behind the arc reactor, the real inspiration for his tech, and why Iron Man remains the most iconic superhero of our generation. This isn't just another superhero video - it's the COMPLETE truth about the man inside the armor! 💪 Hit LIKE if you're Team Iron Man, SUBSCRIBE for more epic Marvel content, and drop a comment with your favorite Iron Man moment! #IronMan #TonyStark #Marvel #MCU #Superhero"
        }
        """

    def _extract_json_from_response(self, raw_content: str) -> str:
        """Extract JSON from response, handling markdown code blocks and extra text."""
        raw_content = raw_content.strip()
        
        # Remove markdown code blocks if present
        if "```json" in raw_content:
            # Extract content between ```json and ```
            match = re.search(r'```json\s*(.*?)\s*```', raw_content, re.DOTALL)
            if match:
                raw_content = match.group(1).strip()
        elif "```" in raw_content:
            # Extract content between ``` and ```
            match = re.search(r'```\s*(.*?)\s*```', raw_content, re.DOTALL)
            if match:
                raw_content = match.group(1).strip()
        
        # Find the first [ and last ] to extract just the JSON array
        first_bracket = raw_content.find('[')
        last_bracket = raw_content.rfind(']')
        
        if first_bracket != -1 and last_bracket != -1:
            raw_content = raw_content[first_bracket:last_bracket + 1]
        
        return raw_content

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

            # Extract clean JSON
            clean_json = self._extract_json_from_response(raw_content)
            
            # Debug: Print what we're trying to parse
            print(f"[debug] Attempting to parse JSON (first 200 chars): {clean_json[:200]}...")

            # Parse JSON
            scenes = json.loads(clean_json)
            
            # Validate it's a list
            if not isinstance(scenes, list):
                print("[error] Response is not a JSON array")
                return []
            
            print(f"[success] Parsed {len(scenes)} scenes successfully")
            return scenes

        except json.JSONDecodeError as e:
            print(f"[error] JSON parsing failed: {e}")
            print(f"[error] Raw content received:\n{raw_content}")
            return []
        except Exception as e:
            print(f"[error] Failed to generate video script: {e}")
            return []

    def save_script(self, scenes, filename="video_script.json"):
        """Save generated scenes to JSON inside the folder for the current video."""
        filepath = self.script_output_dir / filename
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(scenes, f, indent=4, ensure_ascii=False)
        print(f"[info] Video script saved at: {filepath}")
        return filepath

    # NEW METHOD: Generate title and description
    def generate_title_and_description(self, user_input: str):
        """Generate YouTube title and description using Groq API."""
        if not user_input.strip():
            return None

        try:
            completion = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": self.title_desc_prompt},
                    {"role": "user", "content": user_input}
                ],
                temperature=0.7,
                max_tokens=1024,
                stream=True
            )

            # Stream and collect content
            raw_content = ""
            for chunk in completion:
                if chunk.choices[0].delta.content:
                    raw_content += chunk.choices[0].delta.content

            # Clean the response
            raw_content = raw_content.strip()
            
            # Remove markdown code blocks if present
            if "```json" in raw_content:
                match = re.search(r'```json\s*(.*?)\s*```', raw_content, re.DOTALL)
                if match:
                    raw_content = match.group(1).strip()
            elif "```" in raw_content:
                match = re.search(r'```\s*(.*?)\s*```', raw_content, re.DOTALL)
                if match:
                    raw_content = match.group(1).strip()
            
            # Find JSON object
            first_brace = raw_content.find('{')
            last_brace = raw_content.rfind('}')
            
            if first_brace != -1 and last_brace != -1:
                raw_content = raw_content[first_brace:last_brace + 1]
            
            # Parse JSON
            result = json.loads(raw_content)
            
            # Validate structure
            if not isinstance(result, dict) or "title" not in result or "description" not in result:
                print("[error] Response missing title or description")
                return None
            
            print(f"[success] Generated title and description")
            return result

        except json.JSONDecodeError as e:
            print(f"[error] JSON parsing failed for title/description: {e}")
            print(f"[error] Raw content received:\n{raw_content}")
            return None
        except Exception as e:
            print(f"[error] Failed to generate title and description: {e}")
            return None

    # NEW METHOD: Save title and description
    def save_title_and_description(self, title_desc_data):
        """Save title and description to separate text files."""
        if not title_desc_data:
            print("[warning] No title/description data to save")
            return None
        
        try:
            # Save title
            title_path = self.title_desc_dir / "title.txt"
            with open(title_path, "w", encoding="utf-8") as f:
                f.write(title_desc_data["title"])
            print(f"[info] Title saved at: {title_path}")
            
            # Save description
            desc_path = self.title_desc_dir / "description.txt"
            with open(desc_path, "w", encoding="utf-8") as f:
                f.write(title_desc_data["description"])
            print(f"[info] Description saved at: {desc_path}")
            
            return {"title_path": title_path, "description_path": desc_path}
        
        except Exception as e:
            print(f"[error] Failed to save title/description: {e}")
            return None


# ---------------------------
# Example usage
# ---------------------------
if __name__ == "__main__":
    generator = VideoScriptGenerator()
    user_input = "A 30-second video introducing Iron Man"
    
    # Generate video script
    scenes = generator.generate_video_script(user_input)
    if scenes:
        print("[info] Generated scenes:")
        for i, scene in enumerate(scenes, 1):
            print(f"Scene {i}: {scene}")
        
        generator.save_script(scenes)
    
    # NEW: Generate and save title & description
    title_desc = generator.generate_title_and_description(user_input)
    if title_desc:
        print(f"\n[info] Generated Title: {title_desc['title']}")
        print(f"[info] Generated Description: {title_desc['description'][:100]}...")
        
        generator.save_title_and_description(title_desc)
