# 🎬 Autotube

**Autotube** is an AI-powered agent that automatically generates and uploads short news-style videos to YouTube on trending topics. It fetches trending topics, writes scripts, generates speech and images, merges them into videos, and uploads them—all without human intervention.

## 🚀 Features

- 🔎 **Fetch trending topics** from APIs (NewsAPI, Google Trends, etc.)
- ✍️ **Generate scripts** using AI (OpenAI, Cohere, etc.)
- 🎙️ **Convert text to speech** (gTTS / Coqui TTS)
- 🖼️ **Fetch relevant images** (Unsplash, Pexels, etc.)
- 🎥 **Merge audio + images into video** (MoviePy/FFmpeg)
- 💬 **Auto-generate captions** (Whisper, optional)
- ⬆️ **Upload to YouTube** via YouTube Data API
- 📜 **History tracking** → avoids duplicate topics
- ⏰ **Scheduler** → auto-upload every X minutes/hours

## 📂 Project Structure

```
yt_auto_agent/
│
├── main.py                 # Main entry point
├── .env                    # API keys and config (not committed to GitHub)
├── requirements.txt        # Dependencies
├── README.md               # This file
│
├── fetch_trends/
│   └── trends.py           # Trending topics fetcher
│
├── script_gen/
│   └── script_writer.py    # AI script generation
│
├── tts/
│   └── tts_engine.py       # Text-to-speech conversion
│
├── images/
│   └── image_fetcher.py    # Image sourcing and processing
│
├── video/
│   └── video_maker.py      # Video compilation and editing
│
├── captions/
│   └── captions.py         # Auto-caption generation
│
├── uploader/
│   └── youtube_upload.py   # YouTube API integration
│
├── history/
│   └── history_manager.py  # Topic history and duplicates
│
├── scheduler/
│   └── job_scheduler.py    # Automated scheduling
│
└── output/                 # Generated videos and assets
    ├── videos/
    ├── audio/
    └── images/
```

## ⚙️ Setup

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/Nabin68/Autotube.git
cd Autotube
```

### 2️⃣ Create a Virtual Environment

```bash
python -m venv venv

# macOS/Linux
source venv/bin/activate  

# Windows
venv\Scripts\activate
```

### 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

### 4️⃣ Configure Environment Variables

Create a `.env` file in the root directory:

```env
# News & Trends APIs
NEWS_API_KEY=your_news_api_key_here
GOOGLE_TRENDS_API=your_google_trends_key_here

# AI Services
COHERE_API_KEY=your_cohere_key_here

# Image APIs
UNSPLASH_ACCESS_KEY=your_unsplash_key_here
PEXELS_API_KEY=your_pexels_key_here

# YouTube Upload
YOUTUBE_CLIENT_ID=your_youtube_client_id
YOUTUBE_CLIENT_SECRET=your_youtube_client_secret
YOUTUBE_REFRESH_TOKEN=your_refresh_token

# Directories
OUTPUT_DIR=output
DATA_DIR=data

# Video Settings
VIDEO_LENGTH=60  # seconds
VIDEO_RESOLUTION=1080
UPLOAD_FREQUENCY=3600  # seconds (1 hour)
```

> ⚠️ **Important**: Never commit your `.env` file to version control. Add it to `.gitignore`.

### 5️⃣ Run the Agent

```bash
python main.py
```

## 🔧 Configuration

### YouTube API Setup

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the YouTube Data API v3
4. Create OAuth 2.0 credentials
5. Download the credentials JSON file
6. Run the authentication flow to get your refresh token

### API Keys Required

| Service | Purpose | Required |
|---------|---------|----------|
| NewsAPI | Trending news topics | Yes |
| Cohere | Script generation | Yes |
| Unsplash | Stock images | Yes |
| YouTube Data API | Video uploads | Yes |
| Google Trends | Trending searches | Optional |
| Pexels | Alternative images | Optional |

## ⏰ Scheduling

### Option 1: Python Schedule

```python
import schedule
import time
from main import main

schedule.every(1).hours.do(main)

while True:
    schedule.run_pending()
    time.sleep(60)
```

### Option 2: Cron (Linux/Mac)

```bash
# Edit crontab
crontab -e

# Add this line to run every hour
0 * * * * cd /path/to/Autotube && python main.py
```

### Option 3: Task Scheduler (Windows)

1. Open Task Scheduler
2. Create Basic Task
3. Set trigger (e.g., hourly)
4. Set action to run `python main.py` in your project directory

## 🔮 Roadmap

- [ ] **Direct AI video generation** (when free APIs become available)
- [ ] **Multi-platform support** (Instagram Reels, TikTok, Twitter)
- [ ] **Advanced analytics** (views, engagement, CTR tracking)
- [ ] **Custom templates** for different video styles
- [ ] **Voice cloning** for consistent narration
- [ ] **AI thumbnail generation**
- [ ] **Sentiment analysis** for topic filtering
- [ ] **A/B testing** for titles and thumbnails

## 🛠️ Dependencies

```
openai>=1.0.0
google-api-python-client>=2.0.0
moviepy>=1.0.3
gTTS>=2.3.0
requests>=2.28.0
python-dotenv>=1.0.0
schedule>=1.2.0
whisper-openai>=20231117
Pillow>=10.0.0
numpy>=1.24.0
```

## 📝 Usage Examples

### Basic Usage

```python
from main import AutotubeAgent

agent = AutotubeAgent()
agent.run_once()  # Generate and upload one video
```

### Custom Configuration

```python
agent = AutotubeAgent(
    video_length=90,
    upload_schedule="0 */2 * * *",  # Every 2 hours
    topics_filter=["technology", "science"]
)
agent.start_scheduler()
```

## 🚨 Important Notes

- **Rate Limits**: Be mindful of API rate limits for all services
- **Content Policy**: Ensure generated content complies with YouTube's community guidelines
- **Copyright**: Only use royalty-free images and audio
- **Storage**: Videos are temporarily stored locally before upload and cleanup
- **Monitoring**: Check logs regularly for any errors or failed uploads

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

If you encounter any issues:

1. Check the [Issues](https://github.com/Nabin68/Autotube/issues) page
2. Review the logs in `data/logs/`
3. Ensure all API keys are correctly configured
4. Verify your Python version is 3.8+

For additional help, feel free to open a new issue with detailed error information.

---

**Made with ❤️ by [Nabin](https://github.com/Nabin68)**

> ⭐ If this project helps you, please consider giving it a star on GitHub!
