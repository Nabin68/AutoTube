import streamlit as st
import sys
import json
import asyncio
from pathlib import Path

# Add base directory to path
BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

# Import all modules
from fetch_trends.trends import NewsHistoryManager
from script_gen.script_writer import VideoScriptGenerator
from images.image_fetcher import ImageGenerator
from tts.tts_engine import AudioGenerator
from video.video_maker import VideoMaker
from uploader.youtube_upload import YoutubeUploader
from dotenv import dotenv_values

# Page config
st.set_page_config(
    page_title="🎬 AutoTube - Automated Video Creator",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        background: linear-gradient(90deg, #FF0080, #FF8C00);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 2rem;
    }
    .step-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #FF0080;
        margin-top: 2rem;
        margin-bottom: 1rem;
        padding: 10px;
        border-left: 5px solid #FF0080;
        background-color: #f0f2f6;
    }
    .success-box {
        padding: 1rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        color: #155724;
    }
    .error-box {
        padding: 1rem;
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 5px;
        color: #721c24;
    }
    .info-box {
        padding: 1rem;
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        border-radius: 5px;
        color: #0c5460;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'step' not in st.session_state:
    st.session_state.step = 0
if 'news_data' not in st.session_state:
    st.session_state.news_data = None
if 'script_data' not in st.session_state:
    st.session_state.script_data = None
if 'video_number' not in st.session_state:
    st.session_state.video_number = None


def get_video_counter():
    """Get current video counter"""
    counter_file = BASE_DIR / "video_counter.txt"
    if not counter_file.exists():
        with open(counter_file, "w") as f:
            f.write("1")
        return "1"
    with open(counter_file, "r") as f:
        num = f.read().strip()
    return num if num.isdigit() else "1"


def increment_video_counter():
    """Increment video counter for next video"""
    counter_file = BASE_DIR / "video_counter.txt"
    current = int(get_video_counter())
    with open(counter_file, "w") as f:
        f.write(str(current + 1))


def main():
    # Header
    st.markdown('<h1 class="main-header">🎬 AutoTube - Automated Video Creator</h1>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("📊 System Status")
        video_num = get_video_counter()
        st.metric("Current Video #", video_num)
        
        st.divider()
        
        st.header("⚙️ Settings")
        video_duration = st.slider("Video Duration (seconds)", 15, 60, 30, step=5)
        
        st.divider()
        
        if st.button("🔄 Reset Pipeline", type="secondary"):
            st.session_state.step = 0
            st.session_state.news_data = None
            st.session_state.script_data = None
            st.rerun()
        
        if st.button("🗑️ Clear History", type="secondary"):
            try:
                history_file = BASE_DIR / "history" / "history_manager.txt"
                if history_file.exists():
                    history_file.unlink()
                st.success("History cleared!")
            except Exception as e:
                st.error(f"Error: {e}")

    # Main content
    st.markdown("### 🚀 Video Generation Pipeline")
    st.progress(st.session_state.step / 5)
    
    # Create tabs for each step
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📰 Step 1: Fetch News",
        "✍️ Step 2: Generate Script",
        "🎨 Step 3: Generate Assets",
        "🎬 Step 4: Create Video",
        "📤 Step 5: Upload to YouTube"
    ])
    
    # ==================== STEP 1: FETCH NEWS ====================
    with tab1:
        st.markdown('<div class="step-header">📰 Step 1: Fetch Latest News</div>', unsafe_allow_html=True)
        
        if st.button("🔍 Fetch Latest Tech News", type="primary", key="fetch_news"):
            with st.spinner("Fetching latest tech news..."):
                try:
                    # Load API key
                    env = dotenv_values(BASE_DIR / ".env")
                    api_key = env.get('NEWS_API_KEY')
                    
                    if not api_key:
                        st.error("❌ NEWS_API_KEY not found in .env file!")
                    else:
                        # Initialize news manager
                        history_folder = BASE_DIR / "history"
                        history_folder.mkdir(exist_ok=True)
                        history_file = history_folder / "history_manager.txt"
                        
                        manager = NewsHistoryManager(
                            history_file=str(history_file),
                            api_key=api_key
                        )
                        
                        news = manager.get_latest_tech_news()
                        
                        if news:
                            st.session_state.news_data = news
                            st.session_state.step = max(st.session_state.step, 1)
                            st.success("✅ Successfully fetched latest news!")
                        else:
                            st.warning("⚠️ No new unique news found. All recent news already processed.")
                
                except Exception as e:
                    st.error(f"❌ Error fetching news: {e}")
        
        # Display fetched news
        if st.session_state.news_data:
            st.markdown('<div class="success-box">', unsafe_allow_html=True)
            st.markdown("#### 📰 Fetched News")
            st.markdown(f"**Title:** {st.session_state.news_data['title']}")
            st.markdown(f"**Description:** {st.session_state.news_data['description']}")
            st.markdown(f"**Source:** {st.session_state.news_data['source']}")
            st.markdown(f"**Published:** {st.session_state.news_data['published_at']}")
            st.markdown(f"**URL:** [{st.session_state.news_data['url']}]({st.session_state.news_data['url']})")
            st.markdown('</div>', unsafe_allow_html=True)
    
    # ==================== STEP 2: GENERATE SCRIPT ====================
    with tab2:
        st.markdown('<div class="step-header">✍️ Step 2: Generate Script</div>', unsafe_allow_html=True)
        
        if st.session_state.news_data is None:
            st.info("⚠️ Please fetch news first (Step 1)")
        else:
            if st.button("📝 Generate Video Script", type="primary", key="gen_script"):
                with st.spinner("Generating video script..."):
                    try:
                        generator = VideoScriptGenerator()
                        
                        # Create prompt
                        topic = st.session_state.news_data['title']
                        description = st.session_state.news_data['description']
                        user_prompt = f"A {video_duration}-second video about {topic}. Context: {description}"
                        
                        # Generate script
                        scenes = generator.generate_video_script(user_prompt)
                        
                        if scenes:
                            # Save script
                            generator.save_script(scenes)
                            
                            # Generate title and description
                            title_desc = generator.generate_title_and_description(user_prompt)
                            if title_desc:
                                generator.save_title_and_description(title_desc)
                            
                            st.session_state.script_data = {
                                'scenes': scenes,
                                'title': title_desc.get('title') if title_desc else topic,
                                'description': title_desc.get('description') if title_desc else description
                            }
                            st.session_state.step = max(st.session_state.step, 2)
                            st.success(f"✅ Successfully generated script with {len(scenes)} scenes!")
                        else:
                            st.error("❌ Failed to generate script!")
                    
                    except Exception as e:
                        st.error(f"❌ Error generating script: {e}")
            
            # Display script
            if st.session_state.script_data:
                st.markdown('<div class="success-box">', unsafe_allow_html=True)
                st.markdown("#### 📜 Generated Script")
                
                # Show title and description
                st.markdown(f"**YouTube Title:** {st.session_state.script_data['title']}")
                st.markdown(f"**YouTube Description:** {st.session_state.script_data['description'][:200]}...")
                
                st.markdown(f"**Total Scenes:** {len(st.session_state.script_data['scenes'])}")
                
                # Show scenes in expander
                with st.expander("View All Scenes"):
                    for i, scene in enumerate(st.session_state.script_data['scenes'], 1):
                        st.markdown(f"**Scene {i}**")
                        st.markdown(f"- **Dialogue:** {scene['dialogue']}")
                        st.markdown(f"- **Visual Prompt:** {scene['visualPrompt']}")
                        st.markdown(f"- **Voice Tone:** {scene['voiceTone']}")
                        st.divider()
                
                st.markdown('</div>', unsafe_allow_html=True)
    
    # ==================== STEP 3: GENERATE ASSETS ====================
    with tab3:
        st.markdown('<div class="step-header">🎨 Step 3: Generate Images & Audio</div>', unsafe_allow_html=True)
        
        if st.session_state.script_data is None:
            st.info("⚠️ Please generate script first (Step 2)")
        else:
            if st.button("🎨 Generate All Assets", type="primary", key="gen_assets"):
                scenes = st.session_state.script_data['scenes']
                
                # Progress tracking
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                total_tasks = len(scenes) * 2  # Images + Audio
                completed = 0
                
                try:
                    # Generate Images
                    status_text.text("🖼️ Generating images...")
                    image_gen = ImageGenerator()
                    
                    for i, scene in enumerate(scenes, 1):
                        visual_prompt = scene.get("visualPrompt", "")
                        if visual_prompt:
                            image_gen.generate_image(visual_prompt, i)
                            completed += 1
                            progress_bar.progress(completed / total_tasks)
                    
                    st.success(f"✅ Generated {len(scenes)} images!")
                    
                    # Generate Audio
                    status_text.text("🎙️ Generating audio...")
                    audio_gen = AudioGenerator()
                    
                    async def generate_all_audio():
                        for i, scene in enumerate(scenes, 1):
                            dialogue = scene.get("dialogue", "")
                            if dialogue:
                                await audio_gen.generate_audio(dialogue, i)
                    
                    asyncio.run(generate_all_audio())
                    completed = total_tasks
                    progress_bar.progress(1.0)
                    
                    st.success(f"✅ Generated {len(scenes)} audio files!")
                    st.session_state.step = max(st.session_state.step, 3)
                    
                    status_text.text("✅ All assets generated successfully!")
                
                except Exception as e:
                    st.error(f"❌ Error generating assets: {e}")
            
            # Display asset status
            video_num = get_video_counter()
            image_dir = BASE_DIR / "data" / video_num / "generated_image"
            audio_dir = BASE_DIR / "data" / video_num / "generated_audio"
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 🖼️ Images")
                if image_dir.exists():
                    images = list(image_dir.glob("*.jpg"))
                    st.metric("Generated Images", len(images))
                else:
                    st.metric("Generated Images", 0)
            
            with col2:
                st.markdown("#### 🎙️ Audio")
                if audio_dir.exists():
                    audios = list(audio_dir.glob("*.mp3"))
                    st.metric("Generated Audio", len(audios))
                else:
                    st.metric("Generated Audio", 0)
    
    # ==================== STEP 4: CREATE VIDEO ====================
    with tab4:
        st.markdown('<div class="step-header">🎬 Step 4: Create Final Video</div>', unsafe_allow_html=True)
        
        if st.session_state.step < 3:
            st.info("⚠️ Please generate assets first (Step 3)")
        else:
            if st.button("🎬 Compile Video", type="primary", key="create_video"):
                with st.spinner("Compiling video... This may take a few minutes..."):
                    try:
                        maker = VideoMaker()
                        success = maker.create_video()
                        
                        if success:
                            st.session_state.step = max(st.session_state.step, 4)
                            st.success("✅ Video created successfully!")
                            
                            # Show video
                            video_num = get_video_counter()
                            video_path = BASE_DIR / "data" / video_num / "generated_video" / f"final_video_{video_num}.mp4"
                            
                            if video_path.exists():
                                st.video(str(video_path))
                        else:
                            st.error("❌ Failed to create video!")
                    
                    except Exception as e:
                        st.error(f"❌ Error creating video: {e}")
            
            # Check if video exists
            video_num = get_video_counter()
            video_path = BASE_DIR / "data" / video_num / "generated_video" / f"final_video_{video_num}.mp4"
            
            if video_path.exists():
                st.markdown('<div class="success-box">', unsafe_allow_html=True)
                st.markdown("#### ✅ Video Ready")
                st.markdown(f"**Path:** `{video_path}`")
                st.markdown(f"**Size:** {video_path.stat().st_size / (1024*1024):.2f} MB")
                st.markdown('</div>', unsafe_allow_html=True)
                
                st.video(str(video_path))
    
    # ==================== STEP 5: UPLOAD TO YOUTUBE ====================
    with tab5:
        st.markdown('<div class="step-header">📤 Step 5: Upload to YouTube</div>', unsafe_allow_html=True)
        
        if st.session_state.step < 4:
            st.info("⚠️ Please create video first (Step 4)")
        else:
            st.warning("⚠️ Make sure you're logged into YouTube in your Chrome profile!")
            
            if st.button("📤 Upload to YouTube", type="primary", key="upload_yt"):
                with st.spinner("Uploading to YouTube... Please wait..."):
                    try:
                        success = YoutubeUploader.upload_latest_video()
                        
                        if success:
                            st.session_state.step = 5
                            st.success("🎉 Video uploaded to YouTube successfully!")
                            st.balloons()
                            
                            # Increment counter for next video
                            increment_video_counter()
                            st.info("✅ Video counter incremented. Ready for next video!")
                        else:
                            st.error("❌ Upload failed! Check console for details.")
                    
                    except Exception as e:
                        st.error(f"❌ Error uploading: {e}")
            
            # Show upload instructions
            with st.expander("📋 Upload Instructions"):
                st.markdown("""
                1. Make sure Chrome profile is set up with YouTube login
                2. Click "Upload to YouTube" button
                3. The script will automatically:
                   - Open YouTube Studio
                   - Click upload button
                   - Select and upload video
                   - Fill in title and description
                   - Click through all steps
                   - Publish video
                4. Wait for confirmation message
                """)
    
    # Footer
    st.divider()
    st.markdown("""
    <div style="text-align: center; color: #666;">
        Made with ❤️ by AutoTube | Powered by AI | Dev: Nabin
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
