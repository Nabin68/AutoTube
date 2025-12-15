import streamlit as st
import sys
import json
import asyncio
import time
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
        font-size: 3.5rem;
        font-weight: bold;
        text-align: center;
        background: linear-gradient(90deg, #FF0080, #FF8C00, #7928CA);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        text-align: center;
        color: #666;
        margin-bottom: 3rem;
    }
    .mode-card {
        padding: 2rem;
        border-radius: 15px;
        border: 2px solid #ddd;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        text-align: center;
        cursor: pointer;
        transition: transform 0.3s, box-shadow 0.3s;
        height: 100%;
    }
    .mode-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
    }
    .mode-card-manual {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    }
    .mode-card-auto {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
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
        border-radius: 10px;
        color: #155724;
    }
    .info-box {
        padding: 1rem;
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        border-radius: 10px;
        color: #0c5460;
    }
    .topic-option {
        padding: 1.5rem;
        border-radius: 10px;
        border: 2px solid #e0e0e0;
        background: white;
        margin-bottom: 1rem;
        transition: all 0.3s;
    }
    .topic-option h3 {
        color: #1a1a1a !important;
        margin-bottom: 0.5rem;
    }
    .topic-option p {
        color: #666 !important;
        margin: 0;
    }
    .topic-option:hover {
        border-color: #FF0080;
        box-shadow: 0 5px 15px rgba(255,0,128,0.2);
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'mode' not in st.session_state:
    st.session_state.mode = None  # 'manual' or 'automated'
if 'step' not in st.session_state:
    st.session_state.step = 0
if 'news_data' not in st.session_state:
    st.session_state.news_data = None
if 'script_data' not in st.session_state:
    st.session_state.script_data = None
if 'processing' not in st.session_state:
    st.session_state.processing = False
if 'topic_source' not in st.session_state:
    st.session_state.topic_source = None
if 'custom_topic' not in st.session_state:
    st.session_state.custom_topic = None


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


def run_full_pipeline(topic, description, video_duration):
    """Run all steps automatically from script generation to upload"""
    
    status_placeholder = st.empty()
    progress_bar = st.progress(0)
    
    try:
        # STEP 1: Generate Script
        status_placeholder.info("📝 Step 1/5: Generating video script...")
        progress_bar.progress(0.1)
        
        generator = VideoScriptGenerator()
        user_prompt = f"A {video_duration}-second video about {topic}. Context: {description}"
        
        scenes = generator.generate_video_script(user_prompt)
        
        if not scenes:
            status_placeholder.error("❌ Failed to generate script!")
            return False
        
        generator.save_script(scenes)
        title_desc = generator.generate_title_and_description(user_prompt)
        if title_desc:
            generator.save_title_and_description(title_desc)
        
        st.session_state.script_data = {
            'scenes': scenes,
            'title': title_desc.get('title') if title_desc else topic,
            'description': title_desc.get('description') if title_desc else description
        }
        
        status_placeholder.success(f"✅ Script generated with {len(scenes)} scenes!")
        progress_bar.progress(0.25)
        time.sleep(1)
        
        # STEP 2: Generate Images
        status_placeholder.info("🖼️ Step 2/5: Generating images...")
        image_gen = ImageGenerator()
        for i, scene in enumerate(scenes, 1):
            visual_prompt = scene.get("visualPrompt", "")
            if visual_prompt:
                image_gen.generate_image(visual_prompt, i)
                progress_bar.progress(0.25 + (0.15 * i / len(scenes)))
        
        status_placeholder.success(f"✅ Generated {len(scenes)} images!")
        progress_bar.progress(0.4)
        time.sleep(1)
        
        # STEP 3: Generate Audio
        status_placeholder.info("🎙️ Step 3/5: Generating audio...")
        audio_gen = AudioGenerator()
        
        async def generate_all_audio():
            for i, scene in enumerate(scenes, 1):
                dialogue = scene.get("dialogue", "")
                if dialogue:
                    await audio_gen.generate_audio(dialogue, i)
                    progress_bar.progress(0.4 + (0.15 * i / len(scenes)))
        
        asyncio.run(generate_all_audio())
        status_placeholder.success(f"✅ Generated {len(scenes)} audio files!")
        progress_bar.progress(0.55)
        time.sleep(1)
        
        # STEP 4: Create Video
        status_placeholder.info("🎬 Step 4/5: Compiling video... This may take a few minutes...")
        progress_bar.progress(0.6)
        
        maker = VideoMaker()
        success = maker.create_video()
        
        if not success:
            status_placeholder.error("❌ Failed to create video!")
            return False
        
        status_placeholder.success("✅ Video created successfully!")
        progress_bar.progress(0.8)
        time.sleep(1)
        
        # STEP 5: Upload to YouTube
        status_placeholder.info("📤 Step 5/5: Uploading to YouTube... Please wait...")
        progress_bar.progress(0.85)
        
        upload_success = YoutubeUploader.upload_latest_video()
        
        if upload_success:
            status_placeholder.success("🎉 Video uploaded to YouTube successfully!")
            progress_bar.progress(1.0)
            st.balloons()
            increment_video_counter()
            return True
        else:
            status_placeholder.error("❌ Upload failed!")
            return False
    
    except Exception as e:
        status_placeholder.error(f"❌ Error: {e}")
        return False


def main():
    # Header
    st.markdown('<h1 class="main-header">🎬 AutoTube</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">AI-Powered Automated Video Creator & YouTube Uploader</p>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("📊 System Status")
        video_num = get_video_counter()
        st.metric("Current Video #", video_num)
        
        st.divider()
        
        st.header("⚙️ Settings")
        video_duration = st.slider("Video Duration (seconds)", 15, 60, 30, step=5)
        
        st.divider()
        
        if st.button("🏠 Back to Home", type="secondary", use_container_width=True):
            st.session_state.mode = None
            st.session_state.step = 0
            st.session_state.news_data = None
            st.session_state.script_data = None
            st.session_state.processing = False
            st.session_state.topic_source = None
            st.session_state.custom_topic = None
            st.rerun()
        
        if st.button("🗑️ Clear History", type="secondary", use_container_width=True):
            try:
                history_file = BASE_DIR / "history" / "history_manager.txt"
                if history_file.exists():
                    history_file.unlink()
                st.success("History cleared!")
            except Exception as e:
                st.error(f"Error: {e}")

    # ==================== MODE SELECTION ====================
    if st.session_state.mode is None:
        st.markdown("### 🎯 Choose Your Mode")
        st.markdown("Select how you want to create your video:")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            <div class="mode-card mode-card-manual">
                <h2>🎮 Manual Mode</h2>
                <p style="font-size: 1.1rem; margin: 1rem 0;">
                    Full control over each step<br/>
                    Review and customize at every stage<br/>
                    Perfect for learning and fine-tuning
                </p>
                <p style="font-size: 0.9rem; opacity: 0.9;">
                    ✓ Step-by-step control<br/>
                    ✓ Review each output<br/>
                    ✓ Manual approval needed
                </p>
            </div>
            """, unsafe_allow_html=True)
            if st.button("🎮 Choose Manual Mode", type="primary", use_container_width=True, key="manual_btn"):
                st.session_state.mode = 'manual'
                st.rerun()
        
        with col2:
            st.markdown("""
            <div class="mode-card mode-card-auto">
                <h2>🤖 Automated Mode</h2>
                <p style="font-size: 1.1rem; margin: 1rem 0;">
                    One-click video generation<br/>
                    Fully automated pipeline<br/>
                    Perfect for quick results
                </p>
                <p style="font-size: 0.9rem; opacity: 0.9;">
                    ✓ Fully automated<br/>
                    ✓ One-click operation<br/>
                    ✓ Hands-free processing
                </p>
            </div>
            """, unsafe_allow_html=True)
            if st.button("🤖 Choose Automated Mode", type="primary", use_container_width=True, key="auto_btn"):
                st.session_state.mode = 'automated'
                st.rerun()
    
    # ==================== AUTOMATED MODE ====================
    elif st.session_state.mode == 'automated':
        st.markdown("### 🤖 Automated Mode")
        st.info("🚀 One-click video generation with full automation")
        
        # Back to mode selection button
        if st.button("⬅️ Back to Mode Selection", key="auto_back_mode"):
            st.session_state.mode = None
            st.session_state.topic_source = None
            st.session_state.news_data = None
            st.session_state.custom_topic = None
            st.rerun()
        
        # Topic Selection
        if st.session_state.topic_source is None and not st.session_state.processing:
            st.markdown("#### 📝 Choose Your Topic Source:")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("""
                <div class="topic-option">
                    <h3>📰 Latest Tech News</h3>
                    <p>Automatically fetch trending tech news</p>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button("🔍 Fetch Latest News", use_container_width=True, key="auto_news"):
                    with st.spinner("Fetching news..."):
                        try:
                            env = dotenv_values(BASE_DIR / ".env")
                            api_key = env.get('NEWS_API_KEY')
                            
                            if api_key:
                                history_folder = BASE_DIR / "history"
                                history_folder.mkdir(exist_ok=True)
                                manager = NewsHistoryManager(
                                    history_file=str(history_folder / "history_manager.txt"),
                                    api_key=api_key
                                )
                                news = manager.get_latest_tech_news()
                                
                                if news:
                                    st.session_state.news_data = news
                                    st.session_state.topic_source = 'news'
                                    st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
            
            with col2:
                st.markdown("""
                <div class="topic-option">
                    <h3>✍️ Custom Topic</h3>
                    <p>Enter your own video topic</p>
                </div>
                """, unsafe_allow_html=True)
                
                custom_topic = st.text_input("Enter topic:", key="auto_custom_input")
                if st.button("🚀 Use This Topic", use_container_width=True, key="auto_custom"):
                    if custom_topic.strip():
                        st.session_state.custom_topic = custom_topic.strip()
                        st.session_state.topic_source = 'custom'
                        st.rerun()
        
        # Confirm and Generate
        elif st.session_state.topic_source and not st.session_state.processing:
            # Back button
            if st.button("⬅️ Back to Topic Selection", key="auto_back"):
                st.session_state.topic_source = None
                st.session_state.news_data = None
                st.session_state.custom_topic = None
                st.rerun()
            
            if st.session_state.topic_source == 'news':
                st.markdown("#### 📰 Selected News:")
                st.markdown('<div class="success-box">', unsafe_allow_html=True)
                st.markdown(f"**Title:** {st.session_state.news_data['title']}")
                st.markdown(f"**Description:** {st.session_state.news_data['description']}")
                st.markdown(f"**Source:** {st.session_state.news_data['source']}")
                st.markdown(f"**URL:** [{st.session_state.news_data['url']}]({st.session_state.news_data['url']})")
                st.markdown('</div>', unsafe_allow_html=True)
                
                topic = st.session_state.news_data['title']
                description = st.session_state.news_data['description']
            else:
                st.markdown("#### ✍️ Custom Topic:")
                st.markdown('<div class="info-box">', unsafe_allow_html=True)
                st.markdown(f"**Topic:** {st.session_state.custom_topic}")
                st.markdown('</div>', unsafe_allow_html=True)
                
                topic = st.session_state.custom_topic
                description = f"Create an engaging video about {topic}"
            
            st.markdown("---")
            
            col1, col2 = st.columns([3, 1])
            with col1:
                if st.button("🎬 Generate & Upload Video Automatically", type="primary", use_container_width=True):
                    st.session_state.processing = True
                    st.rerun()
            with col2:
                if st.button("🔄 Change", type="secondary", use_container_width=True):
                    st.session_state.topic_source = None
                    st.rerun()
        
        # Processing
        if st.session_state.processing:
            st.markdown("---")
            
            # Determine topic and description BEFORE calling pipeline
            if st.session_state.topic_source == 'news':
                topic = st.session_state.news_data['title']
                description = st.session_state.news_data['description']
            else:
                topic = st.session_state.custom_topic
                description = f"Create an engaging video about {topic}"
            
            # Run the full pipeline with determined values
            success = run_full_pipeline(topic, description, video_duration)
            
            st.session_state.processing = False
            
            if success:
                show_video_result()
    
    # ==================== MANUAL MODE ====================
    elif st.session_state.mode == 'manual':
        st.markdown("### 🎮 Manual Mode")
        st.info("📋 Full control over each step of video creation")
        
        # Back to mode selection button
        if st.button("⬅️ Back to Mode Selection", key="manual_back_mode"):
            st.session_state.mode = None
            st.session_state.topic_source = None
            st.session_state.news_data = None
            st.session_state.custom_topic = None
            st.rerun()
        
        # Topic Selection
        if st.session_state.topic_source is None:
            st.markdown("#### 📝 Choose Your Topic Source:")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("""
                <div class="topic-option">
                    <h3>📰 Latest Tech News</h3>
                    <p>Fetch and review trending tech news</p>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button("🔍 Fetch News", use_container_width=True, key="manual_news"):
                    with st.spinner("Fetching news..."):
                        try:
                            env = dotenv_values(BASE_DIR / ".env")
                            api_key = env.get('NEWS_API_KEY')
                            
                            if api_key:
                                history_folder = BASE_DIR / "history"
                                history_folder.mkdir(exist_ok=True)
                                manager = NewsHistoryManager(
                                    history_file=str(history_folder / "history_manager.txt"),
                                    api_key=api_key
                                )
                                news = manager.get_latest_tech_news()
                                
                                if news:
                                    st.session_state.news_data = news
                                    st.session_state.topic_source = 'news'
                                    st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
            
            with col2:
                st.markdown("""
                <div class="topic-option">
                    <h3>✍️ Custom Topic</h3>
                    <p>Create video from your own topic</p>
                </div>
                """, unsafe_allow_html=True)
                
                custom_topic = st.text_input("Enter topic:", key="manual_custom_input")
                if st.button("✅ Confirm Topic", use_container_width=True, key="manual_custom"):
                    if custom_topic.strip():
                        st.session_state.custom_topic = custom_topic.strip()
                        st.session_state.topic_source = 'custom'
                        st.rerun()
        
        # Manual Steps
        else:
            show_manual_steps(video_duration)


def show_manual_steps(video_duration):
    """Display manual step-by-step process"""
    
    # Show selected topic with back button
    col_back, col_main = st.columns([1, 5])
    with col_back:
        if st.button("⬅️ Back", use_container_width=True):
            st.session_state.topic_source = None
            st.session_state.news_data = None
            st.session_state.custom_topic = None
            st.rerun()
    
    with col_main:
        if st.session_state.topic_source == 'news':
            st.markdown("#### 📰 Selected News:")
            st.markdown('<div class="success-box">', unsafe_allow_html=True)
            st.markdown(f"**Title:** {st.session_state.news_data['title']}")
            st.markdown(f"**Description:** {st.session_state.news_data['description']}")
            st.markdown(f"**Source:** {st.session_state.news_data['source']}")
            st.markdown(f"**URL:** [{st.session_state.news_data['url']}]({st.session_state.news_data['url']})")
            st.markdown('</div>', unsafe_allow_html=True)
            topic = st.session_state.news_data['title']
            description = st.session_state.news_data['description']
        else:
            st.markdown("#### ✍️ Your Topic:")
            st.markdown('<div class="info-box">', unsafe_allow_html=True)
            st.markdown(f"**Topic:** {st.session_state.custom_topic}")
            st.markdown('</div>', unsafe_allow_html=True)
            topic = st.session_state.custom_topic
            description = f"Create video about {topic}"
    
    st.markdown("---")
    
    # Create tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📝 Step 1: Script",
        "🖼️ Step 2: Images",
        "🎙️ Step 3: Audio",
        "🎬 Step 4: Video",
        "📤 Step 5: Upload"
    ])
    
    # Step 1: Generate Script
    with tab1:
        st.markdown("### 📝 Generate Video Script")
        if st.button("Generate Script", type="primary", key="gen_script"):
            with st.spinner("Generating script..."):
                generator = VideoScriptGenerator()
                user_prompt = f"A {video_duration}-second video about {topic}. Context: {description}"
                scenes = generator.generate_video_script(user_prompt)
                
                if scenes:
                    generator.save_script(scenes)
                    title_desc = generator.generate_title_and_description(user_prompt)
                    if title_desc:
                        generator.save_title_and_description(title_desc)
                    
                    st.session_state.script_data = {
                        'scenes': scenes,
                        'title': title_desc.get('title') if title_desc else topic,
                        'description': title_desc.get('description') if title_desc else description
                    }
                    st.success(f"✅ Generated {len(scenes)} scenes!")
        
        if st.session_state.script_data:
            st.markdown("#### 📜 Generated Script:")
            for i, scene in enumerate(st.session_state.script_data['scenes'], 1):
                with st.expander(f"Scene {i}"):
                    st.write(f"**Dialogue:** {scene['dialogue']}")
                    st.write(f"**Visual:** {scene['visualPrompt'][:100]}...")
    
    # Step 2: Generate Images
    with tab2:
        st.markdown("### 🖼️ Generate Images")
        if st.session_state.script_data:
            if st.button("Generate Images", type="primary", key="gen_images"):
                with st.spinner("Generating images..."):
                    image_gen = ImageGenerator()
                    for i, scene in enumerate(st.session_state.script_data['scenes'], 1):
                        image_gen.generate_image(scene['visualPrompt'], i)
                    st.success("✅ Images generated!")
        else:
            st.info("⚠️ Generate script first")
    
    # Step 3: Generate Audio
    with tab3:
        st.markdown("### 🎙️ Generate Audio")
        if st.session_state.script_data:
            if st.button("Generate Audio", type="primary", key="gen_audio"):
                with st.spinner("Generating audio..."):
                    audio_gen = AudioGenerator()
                    async def gen_audio():
                        for i, scene in enumerate(st.session_state.script_data['scenes'], 1):
                            await audio_gen.generate_audio(scene['dialogue'], i)
                    asyncio.run(gen_audio())
                    st.success("✅ Audio generated!")
        else:
            st.info("⚠️ Generate script first")
    
    # Step 4: Create Video
    with tab4:
        st.markdown("### 🎬 Create Final Video")
        if st.button("Compile Video", type="primary", key="create_video"):
            with st.spinner("Creating video..."):
                maker = VideoMaker()
                if maker.create_video():
                    st.success("✅ Video created!")
                    video_num = get_video_counter()
                    video_path = BASE_DIR / "data" / video_num / "generated_video" / f"final_video_{video_num}.mp4"
                    if video_path.exists():
                        st.video(str(video_path))
    
    # Step 5: Upload
    with tab5:
        st.markdown("### 📤 Upload to YouTube")
        if st.button("Upload Video", type="primary", key="upload_video"):
            with st.spinner("Uploading..."):
                if YoutubeUploader.upload_latest_video():
                    st.success("🎉 Uploaded!")
                    increment_video_counter()
                    st.balloons()


def show_video_result():
    """Show the final video result"""
    st.markdown("---")
    st.markdown("### 🎉 Video Complete!")
    
    video_num = str(int(get_video_counter()) - 1)
    video_path = BASE_DIR / "data" / video_num / "generated_video" / f"final_video_{video_num}.mp4"
    
    if video_path.exists():
        st.video(str(video_path))
        st.markdown(f"**Video #{video_num}** | Size: {video_path.stat().st_size / (1024*1024):.2f} MB")
    
    if st.button("🔄 Create Another Video", type="primary", use_container_width=True):
        st.session_state.mode = None
        st.session_state.step = 0
        st.session_state.news_data = None
        st.session_state.script_data = None
        st.session_state.processing = False
        st.session_state.topic_source = None
        st.session_state.custom_topic = None
        st.rerun()


if __name__ == "__main__":
    main()
