import os
import time
import subprocess
import psutil
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

class YoutubeUploader:
    """YouTube upload automation module - STABLE VERSION"""
    
    _upload_driver = None
    _profile_path = r"C:\Users\KIIT\AppData\Local\Google\Chrome\User Data\SeleniumProfile"
    
    @classmethod
    def get_chromedriver_path(cls):
        """Get ChromeDriver path from the chromedriver folder"""
        base_path = Path(__file__).parent.parent
        chromedriver_path = base_path / "chromedriver" / "chromedriver.exe"
        
        if not chromedriver_path.exists():
            print(f"❌ ChromeDriver not found at: {chromedriver_path}")
            return None
        
        return str(chromedriver_path)

    @classmethod
    def kill_existing_chrome(cls):
        """Kill any existing Chrome processes using our profile"""
        print("🔍 Checking for existing Chrome processes...")
        killed = False
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['name'] and 'chrome' in proc.info['name'].lower():
                    if proc.info['cmdline']:
                        cmdline_str = ' '.join(proc.info['cmdline'])
                        if 'SeleniumProfile' in cmdline_str:
                            print(f"   Killing Chrome PID: {proc.info['pid']}")
                            proc.kill()
                            killed = True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        if killed:
            time.sleep(3)
            print("✅ Killed existing Chrome processes")
        else:
            print("✅ No existing Chrome processes found")

    @classmethod
    def create_chrome_driver(cls):
        """Create a new Chrome instance with proper configuration"""
        chromedriver_path = cls.get_chromedriver_path()
        if not chromedriver_path:
            return None

        print("🚀 Creating Chrome driver...")
        
        options = Options()
        options.add_argument(f"--user-data-dir={cls._profile_path}")
        options.add_argument("--start-maximized")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--log-level=3")

        try:
            service = Service(chromedriver_path)
            driver = webdriver.Chrome(service=service, options=options)
            
            # Test the connection
            time.sleep(2)
            driver.get("about:blank")
            time.sleep(1)
            
            print("✅ Chrome driver created successfully")
            return driver
            
        except Exception as e:
            print(f"❌ Failed to create Chrome driver: {e}")
            return None

    @classmethod
    def get_or_create_driver(cls):
        """Get existing driver or create new one"""
        
        # Test existing driver
        if cls._upload_driver:
            try:
                cls._upload_driver.current_url
                print("✅ Using existing Chrome driver")
                return cls._upload_driver
            except:
                print("⚠️ Existing driver is dead, creating new one...")
                try:
                    cls._upload_driver.quit()
                except:
                    pass
                cls._upload_driver = None
        
        # Kill any existing Chrome processes first
        cls.kill_existing_chrome()
        
        # Create new driver
        driver = cls.create_chrome_driver()
        
        if driver:
            cls._upload_driver = driver
            print("✅ YouTube upload Chrome driver ready!")
            return driver
        else:
            print("❌ Failed to create Chrome driver!")
            return None

    @classmethod
    def cleanup_driver(cls):
        """Clean up the upload driver"""
        if cls._upload_driver:
            try:
                cls._upload_driver.quit()
            except:
                pass
            cls._upload_driver = None

    @staticmethod
    def get_latest_video_from_data_folder():
        """Get the latest video based on video_counter.txt"""
        base_path = Path(__file__).parent.parent
        counter_file = base_path / "video_counter.txt"
        
        if not counter_file.exists():
            print("❌ video_counter.txt not found!")
            return None
        
        with open(counter_file, 'r') as f:
            video_num = f.read().strip()
        
        if not video_num.isdigit():
            print("❌ Invalid video counter!")
            return None
        
        video_folder = base_path / "data" / video_num / "generated_video"
        
        if not video_folder.exists():
            print(f"❌ Video folder not found: {video_folder}")
            return None
        
        video_files = list(video_folder.glob("*.mp4"))
        
        if not video_files:
            print(f"❌ No video files found in: {video_folder}")
            return None
        
        latest_video = max(video_files, key=lambda x: x.stat().st_mtime)
        
        print(f"✅ Found video: {latest_video.name}")
        return str(latest_video.absolute())

    @staticmethod
    def get_video_metadata():
        """Get video metadata (title, description) from title_description folder"""
        base_path = Path(__file__).parent.parent
        counter_file = base_path / "video_counter.txt"
        
        with open(counter_file, 'r') as f:
            video_num = f.read().strip()
        
        title_desc_folder = base_path / "data" / video_num / "title_description"
        
        metadata = {
            "title": "Latest News Update",
            "description": "Automated news video generated by Autotube"
        }
        
        # Try to read title
        title_file = title_desc_folder / "title.txt"
        if title_file.exists():
            try:
                with open(title_file, 'r', encoding='utf-8') as f:
                    metadata["title"] = f.read().strip()
                print(f"✅ Loaded title: {metadata['title'][:50]}...")
            except Exception as e:
                print(f"⚠️ Could not read title: {e}")
        
        # Try to read description
        desc_file = title_desc_folder / "description.txt"
        if desc_file.exists():
            try:
                with open(desc_file, 'r', encoding='utf-8') as f:
                    metadata["description"] = f.read().strip()
                print(f"✅ Loaded description")
            except Exception as e:
                print(f"⚠️ Could not read description: {e}")
        
        return metadata

    @staticmethod
    def clean_text_for_upload(text):
        """Remove emojis and special characters that Chrome can't handle"""
        import re
        clean = text.encode('ascii', 'ignore').decode('ascii')
        if not clean.strip():
            clean = re.sub(r'[^\x00-\x7F\u0080-\uFFFF]+', '', text)
        return clean

    @staticmethod
    def upload_video_to_youtube(driver, video_path, title=None, description=None):
        """Upload a single video to YouTube Studio"""
        try:
            # Navigate to YouTube Studio
            print("🌐 Navigating to YouTube Studio...")
            driver.get("https://studio.youtube.com")
            time.sleep(8)

            # Click CREATE button
            print("📤 Looking for CREATE button...")
            create_clicked = False
            
            create_selectors = [
                (By.XPATH, '//button[@aria-label="Create"]'),
                (By.XPATH, '//ytcp-button[@id="create-icon"]'),
                (By.ID, "create-icon"),
                (By.XPATH, '//*[@id="create-icon"]'),
            ]
            
            for by_method, selector in create_selectors:
                try:
                    create_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((by_method, selector))
                    )
                    driver.execute_script("arguments[0].scrollIntoView(true);", create_button)
                    time.sleep(1)
                    driver.execute_script("arguments[0].click();", create_button)
                    create_clicked = True
                    print("✅ CREATE button clicked!")
                    break
                except:
                    continue
            
            if not create_clicked:
                print("❌ Could not find CREATE button!")
                return False
            
            # Wait for dropdown menu, then click "Upload videos"
            print("📤 Looking for 'Upload videos' option in menu...")
            time.sleep(2)
            
            upload_clicked = False
            upload_menu_selectors = [
                (By.XPATH, '//tp-yt-paper-item[@test-id="upload-beta"]'),
                (By.XPATH, '//tp-yt-paper-item[contains(text(), "Upload videos")]'),
                (By.XPATH, '//*[@id="text-item-0"]'),
                (By.XPATH, '//ytcp-ve[contains(text(), "Upload videos")]'),
                (By.XPATH, '//tp-yt-paper-item[@class="style-scope ytcp-text-menu"]'),
            ]
            
            for by_method, selector in upload_menu_selectors:
                try:
                    upload_option = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((by_method, selector))
                    )
                    driver.execute_script("arguments[0].scrollIntoView(true);", upload_option)
                    time.sleep(1)
                    driver.execute_script("arguments[0].click();", upload_option)
                    upload_clicked = True
                    print("✅ 'Upload videos' option clicked!")
                    break
                except:
                    continue
            
            if not upload_clicked:
                print("❌ Could not find 'Upload videos' option in menu!")
                print("⚠️ Trying to find file input directly...")
            
            time.sleep(3)

            # Upload file
            print(f"📁 Selecting video file...")
            
            file_input_selectors = [
                (By.XPATH, '//input[@type="file"]'),
                (By.CSS_SELECTOR, 'input[type="file"]'),
                (By.XPATH, '//input[@name="Filedata"]'),
                (By.XPATH, '//*[@id="content"]/input'),
            ]
            
            file_input = None
            for by_method, selector in file_input_selectors:
                try:
                    file_input = WebDriverWait(driver, 15).until(
                        EC.presence_of_element_located((by_method, selector))
                    )
                    if file_input:
                        print("✅ File input found!")
                        break
                except:
                    continue
            
            if not file_input:
                print("❌ Could not find file input element!")
                return False
            
            file_input.send_keys(video_path)
            print("✅ Video file selected")
            
            # Wait for upload to complete - IMPROVED METHOD
            print("⏳ Waiting for video to upload (this may take 1-3 minutes)...")
            
            max_wait = 300  # 5 minutes
            start_time = time.time()
            upload_complete = False
            
            while (time.time() - start_time) < max_wait:
                try:
                    # Check if textboxes are available (means upload is done)
                    textboxes = driver.find_elements(By.XPATH, '//div[@id="textbox"]')
                    if len(textboxes) > 0:
                        # Try to click first textbox to verify it's ready
                        try:
                            textboxes[0].click()
                            upload_complete = True
                            print("✅ Upload complete - form is ready!")
                            break
                        except:
                            pass
                except:
                    pass
                
                time.sleep(3)
                elapsed = int(time.time() - start_time)
                if elapsed % 20 == 0 and elapsed > 0:
                    print(f"   Still uploading... ({elapsed}s elapsed)")
            
            if not upload_complete:
                print("⚠️ Upload taking longer than expected, proceeding anyway...")
            
            time.sleep(5)

            # Set title - IMPROVED METHOD
            if title:
                clean_title = YoutubeUploader.clean_text_for_upload(title)
                print(f"✍️ Setting title...")
                try:
                    # Find all textboxes
                    textboxes = WebDriverWait(driver, 20).until(
                        EC.presence_of_all_elements_located((By.XPATH, '//div[@id="textbox"]'))
                    )
                    
                    if len(textboxes) > 0:
                        title_input = textboxes[0]
                        
                        # Scroll to it
                        driver.execute_script("arguments[0].scrollIntoView(true);", title_input)
                        time.sleep(1)
                        
                        # Click to focus
                        title_input.click()
                        time.sleep(1)
                        
                        # Clear existing text
                        title_input.send_keys(Keys.CONTROL + "a")
                        time.sleep(0.5)
                        title_input.send_keys(Keys.BACKSPACE)
                        time.sleep(0.5)
                        
                        # Type new title
                        title_input.send_keys(clean_title)
                        time.sleep(1)
                        
                        print(f"✅ Title set: {clean_title[:50]}...")
                    else:
                        print("⚠️ Could not find title textbox")
                        
                except Exception as e:
                    print(f"⚠️ Could not set title: {e}")

            # Set description - IMPROVED METHOD
            if description:
                clean_desc = YoutubeUploader.clean_text_for_upload(description)
                print(f"✍️ Setting description...")
                try:
                    # Find all textboxes (description is the second one)
                    textboxes = driver.find_elements(By.XPATH, '//div[@id="textbox"]')
                    
                    if len(textboxes) > 1:
                        desc_input = textboxes[1]
                        
                        # Scroll to it
                        driver.execute_script("arguments[0].scrollIntoView(true);", desc_input)
                        time.sleep(1)
                        
                        # Click to focus
                        desc_input.click()
                        time.sleep(1)
                        
                        # Type description
                        desc_input.send_keys(clean_desc)
                        time.sleep(1)
                        
                        print("✅ Description set")
                    else:
                        print("⚠️ Could not find description textbox")
                        
                except Exception as e:
                    print(f"⚠️ Could not set description: {e}")

            time.sleep(2)

            # Set "Made for kids"
            print("👶 Setting 'Made for kids' option...")
            try:
                made_for_kids_selectors = [
                    '//tp-yt-paper-radio-button[@name="VIDEO_MADE_FOR_KIDS_MFK"]',
                    '//paper-radio-button[@name="VIDEO_MADE_FOR_KIDS_MFK"]',
                    '//*[contains(text(), "Yes, it\'s made for kids")]/ancestor::tp-yt-paper-radio-button',
                ]
                
                kids_clicked = False
                for selector in made_for_kids_selectors:
                    try:
                        kids_button = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                        kids_button.click()
                        kids_clicked = True
                        print("✅ Selected 'Yes, it's made for kids'")
                        break
                    except:
                        continue
                
                if not kids_clicked:
                    print("⚠️ Could not find 'Made for kids' button")
                
                time.sleep(2)
                
            except Exception as e:
                print(f"⚠️ Error setting 'Made for kids': {e}")

            # Click NEXT - Details to Video elements
            print("➡️ Step 1: Details → Video elements")
            try:
                next_btn = WebDriverWait(driver, 15).until(
                    EC.element_to_be_clickable((By.XPATH, '//*[@id="next-button"]'))
                )
                next_btn.click()
                time.sleep(3)
                print("✅ Step 1 completed")
            except Exception as e:
                print(f"⚠️ Error on step 1: {e}")

            # Click NEXT - Video elements to Checks
            print("➡️ Step 2: Video elements → Checks")
            try:
                next_btn = WebDriverWait(driver, 15).until(
                    EC.element_to_be_clickable((By.XPATH, '//*[@id="next-button"]'))
                )
                next_btn.click()
                time.sleep(5)
                print("✅ Step 2 completed")
            except Exception as e:
                print(f"⚠️ Error on step 2: {e}")

            # Wait for copyright check
            print("⏳ Waiting for copyright check...")
            time.sleep(5)
            
            try:
                copyright_status = WebDriverWait(driver, 30).until(
                    EC.presence_of_element_located((By.XPATH, 
                        '//*[contains(text(), "No issues found") or contains(text(), "Copyright")]'))
                )
                print("✅ Copyright check completed")
            except:
                print("⚠️ Copyright check status unclear, continuing...")
            
            time.sleep(2)

            # Click NEXT - Checks to Visibility
            print("➡️ Step 3: Checks → Visibility")
            try:
                next_btn = WebDriverWait(driver, 15).until(
                    EC.element_to_be_clickable((By.XPATH, '//*[@id="next-button"]'))
                )
                next_btn.click()
                time.sleep(3)
                print("✅ Step 3 completed")
            except Exception as e:
                print(f"⚠️ Error on step 3: {e}")

            # Set to PUBLIC
            print("🌍 Setting visibility to PUBLIC...")
            try:
                public_selectors = [
                    '//tp-yt-paper-radio-button[@name="PUBLIC"]',
                    '//paper-radio-button[@name="PUBLIC"]',
                    '//*[contains(text(), "Public")]/ancestor::tp-yt-paper-radio-button',
                ]
                
                public_clicked = False
                for selector in public_selectors:
                    try:
                        public_radio = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                        public_radio.click()
                        public_clicked = True
                        print("✅ Set to PUBLIC")
                        break
                    except:
                        continue
                
                if not public_clicked:
                    print("⚠️ Could not set PUBLIC visibility")
                
                time.sleep(2)
                
            except Exception as e:
                print(f"⚠️ Error setting visibility: {e}")

            # Click PUBLISH
            print("🚀 Publishing video...")
            try:
                publish_btn = WebDriverWait(driver, 15).until(
                    EC.element_to_be_clickable((By.XPATH, '//*[@id="done-button"]'))
                )
                publish_btn.click()
                time.sleep(5)
                print("🎉 Video published successfully!")
                return True
            except Exception as e:
                print(f"⚠️ Error clicking publish: {e}")
                try:
                    publish_btn = driver.find_element(By.XPATH, '//ytcp-button[@id="done-button"]')
                    publish_btn.click()
                    time.sleep(5)
                    print("🎉 Video published successfully!")
                    return True
                except:
                    print("❌ Could not click publish button")
                    return False

        except Exception as e:
            print(f"❌ Error uploading video: {e}")
            import traceback
            traceback.print_exc()
            return False

    @staticmethod
    def upload_latest_video():
        """Main method to upload the latest video from data folder"""
        try:
            print("\n" + "="*60)
            print("🎬 Starting YouTube Upload Process")
            print("="*60 + "\n")
            
            # Get or create driver
            driver = YoutubeUploader.get_or_create_driver()
            
            if not driver:
                print("❌ Failed to get Chrome driver!")
                return False

            # Get latest video
            video_path = YoutubeUploader.get_latest_video_from_data_folder()
            
            if not video_path:
                print("❌ No video found to upload!")
                return False

            # Get metadata
            metadata = YoutubeUploader.get_video_metadata()
            
            # Upload video
            success = YoutubeUploader.upload_video_to_youtube(
                driver, 
                video_path,
                title=metadata["title"],
                description=metadata["description"]
            )

            if success:
                print("\n" + "="*60)
                print("✅ Upload completed successfully!")
                print("="*60 + "\n")
                return True
            else:
                print("\n" + "="*60)
                print("❌ Upload failed!")
                print("="*60 + "\n")
                return False

        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            import traceback
            traceback.print_exc()
            return False


if __name__ == "__main__":
    print("=" * 60)
    print("🎬 AUTOTUBE - YouTube Video Uploader")
    print("=" * 60)
    
    result = YoutubeUploader.upload_latest_video()
    
    if result:
        print("\n✅ All done!")
    else:
        print("\n❌ Upload failed. Please check the errors above.")
    
    print("\n💡 Chrome will stay open for 10 seconds...")
    time.sleep(10)
    
    print("Cleaning up...")
    YoutubeUploader.cleanup_driver()
    print("✅ Done!")
