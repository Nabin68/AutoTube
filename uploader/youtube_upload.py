import os
import time
import subprocess
import psutil
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

class YoutubeUploader:
    """YouTube upload automation module"""
    
    _upload_driver = None
    _connected_to_existing = False
    
    # Chrome profile settings
    _profile_path = r"C:\Users\KIIT\AppData\Local\Google\Chrome\User Data\SeleniumProfile"
    _debug_port = 9222
    
    @classmethod
    def get_chromedriver_path(cls):
        """Get ChromeDriver path from the chromedriver folder"""
        base_path = Path(__file__).parent.parent  # Go up to AUTOTUBE folder
        chromedriver_path = base_path / "chromedriver" / "chromedriver.exe"
        
        if not chromedriver_path.exists():
            print(f"❌ ChromeDriver not found at: {chromedriver_path}")
            return None
        
        return str(chromedriver_path)

    @classmethod
    def is_chrome_profile_running(cls):
        """Check if Chrome is running with the specific profile"""
        profile_name = os.path.basename(cls._profile_path)
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['name'] and 'chrome' in proc.info['name'].lower():
                    if proc.info['cmdline'] and any(profile_name in arg for arg in proc.info['cmdline']):
                        return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return False

    @classmethod
    def start_chrome_with_remote_debugging(cls):
        """Start Chrome with remote debugging enabled"""
        chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

        cmd = [
            chrome_path,
            f"--user-data-dir={cls._profile_path}",
            f"--remote-debugging-port={cls._debug_port}",
            "--no-first-run",
            "--no-default-browser-check"
        ]

        try:
            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(5)  # Give Chrome more time to start
            return True
        except Exception as e:
            print(f"❌ Failed to start Chrome: {e}")
            return False

    @classmethod
    def connect_to_existing_chrome(cls):
        """Connect to existing Chrome instance"""
        chromedriver_path = cls.get_chromedriver_path()
        if not chromedriver_path:
            return None

        options = Options()
        options.add_experimental_option("debuggerAddress", f"localhost:{cls._debug_port}")
        
        # Add these options to prevent issues
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        try:
            service = Service(chromedriver_path)
            driver = webdriver.Chrome(service=service, options=options)
            cls._connected_to_existing = True
            cls._upload_driver = driver
            return driver
        except Exception as e:
            print(f"❌ Failed to connect to existing Chrome: {e}")
            return None

    @classmethod
    def create_new_chrome_instance(cls):
        """Create new Chrome instance (fallback method)"""
        chromedriver_path = cls.get_chromedriver_path()
        if not chromedriver_path:
            return None

        options = Options()
        options.add_argument(f"--user-data-dir={cls._profile_path}")
        options.add_argument("--no-first-run")
        options.add_argument("--no-default-browser-check")
        options.add_argument("--log-level=3")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        try:
            service = Service(chromedriver_path)
            driver = webdriver.Chrome(service=service, options=options)
            cls._connected_to_existing = False
            cls._upload_driver = driver
            return driver
        except Exception as e:
            print(f"❌ Failed to create new Chrome instance: {e}")
            return None

    @classmethod
    def get_or_create_driver(cls):
        """Get existing upload driver or create new one if needed"""
        # If we already have a driver, return it
        if cls._upload_driver:
            try:
                cls._upload_driver.current_url
                print("✅ Using existing YouTube upload driver!")
                return cls._upload_driver
            except:
                print("⚠️ Existing upload driver is dead, creating new one...")
                cls._upload_driver = None

        driver = None

        # Check if Chrome with our profile is already running
        if cls.is_chrome_profile_running():
            print("🔍 Chrome profile is already running, attempting to connect...")
            driver = cls.connect_to_existing_chrome()

            if driver:
                print("✅ Connected to existing Chrome instance!")
                return driver
            else:
                print("⚠️ Could not connect to existing Chrome, trying fresh start...")

        # If not running or connection failed, start fresh
        print("🚀 Starting new Chrome instance with remote debugging...")
        if cls.start_chrome_with_remote_debugging():
            driver = cls.connect_to_existing_chrome()

        if not driver:
            print("🔄 Falling back to regular Chrome startup...")
            driver = cls.create_new_chrome_instance()

        if not driver:
            print("❌ Failed to create or connect to Chrome driver!")
            return None

        print("✅ YouTube upload Chrome driver ready!")
        return driver

    @classmethod
    def cleanup_driver(cls):
        """Clean up the upload driver"""
        if cls._upload_driver:
            try:
                cls._upload_driver.quit()
            except:
                pass
            cls._upload_driver = None
            cls._connected_to_existing = False

    @staticmethod
    def get_latest_video_from_data_folder():
        """Get the latest video based on video_counter.txt"""
        base_path = Path(__file__).parent.parent
        counter_file = base_path / "video_counter.txt"
        
        # Read current video number
        if not counter_file.exists():
            print("❌ video_counter.txt not found!")
            return None
        
        with open(counter_file, 'r') as f:
            video_num = f.read().strip()
        
        if not video_num.isdigit():
            print("❌ Invalid video counter!")
            return None
        
        # Path to generated video folder
        video_folder = base_path / "data" / video_num / "generated_video"
        
        if not video_folder.exists():
            print(f"❌ Video folder not found: {video_folder}")
            return None
        
        # Get all video files
        video_files = list(video_folder.glob("*.mp4"))
        
        if not video_files:
            print(f"❌ No video files found in: {video_folder}")
            return None
        
        # Get the most recent video
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
    def upload_video_to_youtube(driver, video_path, title=None, description=None):
        """Upload a single video to YouTube Studio"""
        try:
            # Navigate to YouTube Studio
            print("🌐 Navigating to YouTube Studio...")
            driver.get("https://studio.youtube.com")
            time.sleep(8)  # Increased wait time for page to fully load

            # Click upload button - COMPREHENSIVE SELECTOR LIST
            print("📤 Looking for upload button...")
            upload_clicked = False
            
            # Try MANY different selectors
            upload_selectors = [
                # By ID
                (By.ID, "upload-icon"),
                (By.ID, "create-icon"),
                # By ARIA label
                (By.XPATH, '//button[@aria-label="Create"]'),
                (By.XPATH, '//button[@aria-label="Upload videos"]'),
                (By.XPATH, '//*[@aria-label="Create"]'),
                (By.XPATH, '//*[@aria-label="Upload videos"]'),
                # By specific component tags
                (By.XPATH, '//ytcp-button[@id="upload-icon"]'),
                (By.XPATH, '//ytcp-button[@id="create-icon"]'),
                # By class and icon
                (By.XPATH, '//button[contains(@class, "create-icon")]'),
                (By.XPATH, '//ytcp-icon-button[@id="upload-icon"]'),
                # By SVG path (create button icon)
                (By.XPATH, '//button[.//tp-yt-iron-icon]'),
                # Generic but specific
                (By.CSS_SELECTOR, '#upload-icon'),
                (By.CSS_SELECTOR, 'ytcp-button#upload-icon'),
                (By.CSS_SELECTOR, 'button[aria-label="Create"]'),
            ]
            
            for i, (by_method, selector) in enumerate(upload_selectors, 1):
                try:
                    print(f"   Trying selector {i}/{len(upload_selectors)}...")
                    upload_button = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((by_method, selector))
                    )
                    
                    # Scroll into view
                    driver.execute_script("arguments[0].scrollIntoView(true);", upload_button)
                    time.sleep(1)
                    
                    # Try regular click
                    try:
                        upload_button.click()
                    except:
                        # If regular click fails, try JavaScript click
                        driver.execute_script("arguments[0].click();", upload_button)
                    
                    upload_clicked = True
                    print(f"✅ Upload button clicked using selector {i}!")
                    break
                except Exception as e:
                    continue
            
            if not upload_clicked:
                print("❌ Could not find upload button with any selector!")
                print("⚠️ Page source (first 500 chars):")
                print(driver.page_source[:500])
                print("\n⚠️ Trying manual search for CREATE button...")
                
                # Last resort: find ALL buttons and click the one with "Create" or upload icon
                try:
                    all_buttons = driver.find_elements(By.TAG_NAME, "button")
                    print(f"   Found {len(all_buttons)} buttons on page")
                    
                    for btn in all_buttons:
                        try:
                            # Check if button has relevant text or aria-label
                            aria_label = btn.get_attribute("aria-label") or ""
                            btn_text = btn.text or ""
                            btn_id = btn.get_attribute("id") or ""
                            
                            if any(keyword in (aria_label + btn_text + btn_id).lower() 
                                   for keyword in ["create", "upload", "add"]):
                                print(f"   Found potential button: {aria_label or btn_text or btn_id}")
                                driver.execute_script("arguments[0].scrollIntoView(true);", btn)
                                time.sleep(1)
                                driver.execute_script("arguments[0].click();", btn)
                                upload_clicked = True
                                print("✅ Clicked upload button via manual search!")
                                break
                        except:
                            continue
                except Exception as e:
                    print(f"   Manual search failed: {e}")
            
            if not upload_clicked:
                print("\n❌ CRITICAL: Cannot find upload button!")
                print("💡 Please check if you're logged into YouTube Studio")
                return False
            
            time.sleep(3)

            # Upload file
            print(f"📁 Selecting file for upload...")
            
            file_input_selectors = [
                (By.XPATH, '//input[@type="file"]'),
                (By.XPATH, '//*[@id="content"]/input'),
                (By.CSS_SELECTOR, 'input[type="file"]'),
                (By.XPATH, '//input[@name="Filedata"]'),
            ]
            
            file_uploaded = False
            for by_method, selector in file_input_selectors:
                try:
                    file_input = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((by_method, selector))
                    )
                    file_input.send_keys(video_path)
                    file_uploaded = True
                    print("✅ File selected for upload!")
                    break
                except:
                    continue
            
            if not file_uploaded:
                print("❌ Could not find file input element!")
                return False
            
            # CRITICAL: Wait for "Checks complete. No issues found." message
            print("⏳ Waiting for video upload and processing...")
            print("   Looking for 'Checks complete. No issues found.' message...")
            print("   This usually takes 1-2 minutes...")
            
            upload_complete = False
            max_wait_time = 300  # 5 minutes max
            start_time = time.time()
            
            while (time.time() - start_time) < max_wait_time:
                try:
                    # Look for the "Checks complete" message at the bottom
                    # This appears when upload is done and processing is complete
                    check_messages = driver.find_elements(By.XPATH, 
                        '//*[contains(text(), "Checks complete") or contains(text(), "No issues found")]'
                    )
                    
                    if len(check_messages) > 0:
                        print("✅ Found 'Checks complete. No issues found.' message!")
                        print("✅ Video is fully uploaded and processed!")
                        upload_complete = True
                        break
                        
                except Exception as e:
                    pass
                
                # Check every 3 seconds
                time.sleep(3)
                elapsed = int(time.time() - start_time)
                
                # Print progress every 15 seconds
                if elapsed % 15 == 0 and elapsed > 0:
                    print(f"   Still processing... ({elapsed}s elapsed)")
            
            if not upload_complete:
                print("⚠️ Did not see 'Checks complete' message, but proceeding...")
            
            # Small buffer after checks complete
            time.sleep(3)

            # Set title if provided - WITH BETTER WAITS AND FOCUS
            if title:
                # Remove emojis and special characters that ChromeDriver can't handle
                import re
                clean_title = title.encode('ascii', 'ignore').decode('ascii')
                # If title becomes empty after removing emojis, use original but filter
                if not clean_title.strip():
                    # Remove only emojis, keep other unicode
                    clean_title = re.sub(r'[^\x00-\x7F\u0080-\uFFFF]+', '', title)
                
                print(f"✍️ Setting title: {clean_title[:50]}...")
                try:
                    # Wait explicitly for the FIRST textbox (title field)
                    title_input = WebDriverWait(driver, 20).until(
                        EC.presence_of_element_located((By.XPATH, '(//div[@id="textbox" and @contenteditable="true"])[1]'))
                    )
                    
                    # Scroll to element to ensure it's visible
                    driver.execute_script("arguments[0].scrollIntoView(true);", title_input)
                    time.sleep(1)
                    
                    # Click to focus
                    title_input.click()
                    time.sleep(1)
                    
                    # Clear any existing content multiple ways
                    try:
                        title_input.clear()
                    except:
                        pass
                    
                    # Select all and delete
                    title_input.send_keys(Keys.CONTROL + "a")
                    time.sleep(0.5)
                    title_input.send_keys(Keys.DELETE)
                    time.sleep(0.5)
                    
                    # Type the clean title (without emojis)
                    title_input.send_keys(clean_title)
                    time.sleep(1)
                    
                    # Verify title was entered
                    entered_text = title_input.text
                    if len(entered_text) > 0:
                        print(f"✅ Title set successfully: {entered_text[:50]}...")
                    else:
                        print("⚠️ Title field appears empty, retrying...")
                        # Retry once
                        title_input.click()
                        time.sleep(1)
                        title_input.send_keys(clean_title)
                        time.sleep(1)
                        print(f"✅ Title set on retry")
                        
                except Exception as e:
                    print(f"⚠️ Could not set title: {e}")
                    import traceback
                    traceback.print_exc()

            # Wait before moving to description
            time.sleep(2)

            # Set description if provided - WITH BETTER WAITS AND FOCUS
            if description:
                # Remove emojis from description too
                import re
                clean_description = description.encode('ascii', 'ignore').decode('ascii')
                if not clean_description.strip():
                    clean_description = re.sub(r'[^\x00-\x7F\u0080-\uFFFF]+', '', description)
                
                print(f"✍️ Setting description...")
                try:
                    # Wait explicitly for the SECOND textbox (description field)
                    desc_input = WebDriverWait(driver, 20).until(
                        EC.presence_of_element_located((By.XPATH, '(//div[@id="textbox" and @contenteditable="true"])[2]'))
                    )
                    
                    # Scroll to element
                    driver.execute_script("arguments[0].scrollIntoView(true);", desc_input)
                    time.sleep(1)
                    
                    # Click to focus
                    desc_input.click()
                    time.sleep(1)
                    
                    # Clear any existing content
                    try:
                        desc_input.clear()
                    except:
                        pass
                    
                    desc_input.send_keys(Keys.CONTROL + "a")
                    time.sleep(0.5)
                    desc_input.send_keys(Keys.DELETE)
                    time.sleep(0.5)
                    
                    # Type the clean description (without emojis)
                    desc_input.send_keys(clean_description)
                    time.sleep(1)
                    
                    # Verify description was entered
                    entered_text = desc_input.text
                    if len(entered_text) > 10:
                        print(f"✅ Description set successfully ({len(entered_text)} characters)")
                    else:
                        print("⚠️ Description field appears empty, retrying...")
                        desc_input.click()
                        time.sleep(1)
                        desc_input.send_keys(clean_description)
                        time.sleep(1)
                        print(f"✅ Description set on retry")
                        
                except Exception as e:
                    print(f"⚠️ Could not set description: {e}")
                    import traceback
                    traceback.print_exc()

            # Extra wait after filling both fields
            time.sleep(3)

            # Click "Yes, it's made for kids" radio button
            print("👶 Setting 'Made for kids' option...")
            try:
                # Multiple selectors for the "Yes, it's made for kids" radio button
                made_for_kids_selectors = [
                    '//tp-yt-paper-radio-button[@name="VIDEO_MADE_FOR_KIDS_MFK"]',
                    '//paper-radio-button[@name="VIDEO_MADE_FOR_KIDS_MFK"]',
                    '//*[contains(text(), "Yes, it\'s made for kids")]/ancestor::tp-yt-paper-radio-button',
                    '//*[@id="made-for-kids-group"]//tp-yt-paper-radio-button[1]'
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
                    print("⚠️ Could not find 'Made for kids' button, continuing anyway...")
                
                time.sleep(2)
                
            except Exception as e:
                print(f"⚠️ Error setting 'Made for kids': {e}")

            # Click Next button (Step 1: Details → Video elements)
            print("➡️ Step 1: Details → Video elements...")
            try:
                next_button = WebDriverWait(driver, 15).until(
                    EC.element_to_be_clickable((By.XPATH, '//*[@id="next-button"]'))
                )
                next_button.click()
                time.sleep(3)
                print("✅ Step 1 completed")
            except Exception as e:
                print(f"⚠️ Error on step 1: {e}")

            # Click Next button (Step 2: Video elements → Checks)
            print("➡️ Step 2: Video elements → Checks...")
            try:
                next_button = WebDriverWait(driver, 15).until(
                    EC.element_to_be_clickable((By.XPATH, '//*[@id="next-button"]'))
                )
                next_button.click()
                time.sleep(3)
                print("✅ Step 2 completed")
            except Exception as e:
                print(f"⚠️ Error on step 2: {e}")

            # Wait for copyright check to complete
            print("⏳ Waiting for copyright check...")
            time.sleep(5)  # Give it time to process
            
            # Check if copyright check is done
            try:
                # Look for "No issues found" or similar text
                copyright_status = WebDriverWait(driver, 30).until(
                    EC.presence_of_element_located((By.XPATH, '//*[contains(text(), "No issues found") or contains(text(), "Copyright")]'))
                )
                print("✅ Copyright check completed")
            except:
                print("⚠️ Copyright check status unclear, continuing...")
            
            time.sleep(2)

            # Click Next button (Step 3: Checks → Visibility)
            print("➡️ Step 3: Checks → Visibility...")
            try:
                next_button = WebDriverWait(driver, 15).until(
                    EC.element_to_be_clickable((By.XPATH, '//*[@id="next-button"]'))
                )
                next_button.click()
                time.sleep(3)
                print("✅ Step 3 completed")
            except Exception as e:
                print(f"⚠️ Error on step 3: {e}")

            # Select Public visibility
            print("🌍 Setting visibility to Public...")
            try:
                # Multiple selectors for the Public radio button
                public_selectors = [
                    '//tp-yt-paper-radio-button[@name="PUBLIC"]',
                    '//paper-radio-button[@name="PUBLIC"]',
                    '//*[contains(text(), "Public")]/ancestor::tp-yt-paper-radio-button',
                    '//*[@id="privacy-radios"]//tp-yt-paper-radio-button[3]'
                ]
                
                public_clicked = False
                for selector in public_selectors:
                    try:
                        public_button = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                        public_button.click()
                        public_clicked = True
                        print("✅ Selected 'Public' visibility")
                        break
                    except:
                        continue
                
                if not public_clicked:
                    print("⚠️ Could not find Public button, might already be selected")
                
                time.sleep(2)
                
            except Exception as e:
                print(f"⚠️ Error setting visibility: {e}")

            # Click Publish button
            print("🚀 Publishing video...")
            try:
                publish_button = WebDriverWait(driver, 15).until(
                    EC.element_to_be_clickable((By.XPATH, '//*[@id="done-button"]'))
                )
                publish_button.click()
                time.sleep(5)
                print("🎉 Video published successfully!")
                return True
            except Exception as e:
                print(f"⚠️ Error clicking publish: {e}")
                # Try alternative selector
                try:
                    publish_button = driver.find_element(By.XPATH, '//ytcp-button[@id="done-button"]')
                    publish_button.click()
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

            # Upload file
            print(f"📁 Uploading file: {video_path}")
            
            file_input_selectors = [
                (By.XPATH, '//*[@id="content"]/input'),
                (By.CSS_SELECTOR, 'input[type="file"]'),
                (By.XPATH, '//input[@type="file"]')
            ]
            
            file_uploaded = False
            for selector_type, selector in file_input_selectors:
                try:
                    file_input = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((selector_type, selector))
                    )
                    file_input.send_keys(video_path)
                    file_uploaded = True
                    print("✅ File selected for upload")
                    break
                except:
                    continue
            
            if not file_uploaded:
                print("❌ Could not upload file")
                return False
            
            # CRITICAL: Wait for "Checks complete. No issues found." message
            print("⏳ Waiting for video upload and processing...")
            print("   Looking for 'Checks complete. No issues found.' message...")
            print("   This usually takes 1-2 minutes...")
            
            upload_complete = False
            max_wait_time = 300  # 5 minutes max
            start_time = time.time()
            
            while (time.time() - start_time) < max_wait_time:
                try:
                    # Look for the "Checks complete" message at the bottom
                    # This appears when upload is done and processing is complete
                    check_messages = driver.find_elements(By.XPATH, 
                        '//*[contains(text(), "Checks complete") or contains(text(), "No issues found")]'
                    )
                    
                    if len(check_messages) > 0:
                        print("✅ Found 'Checks complete. No issues found.' message!")
                        print("✅ Video is fully uploaded and processed!")
                        upload_complete = True
                        break
                        
                except Exception as e:
                    pass
                
                # Check every 3 seconds
                time.sleep(3)
                elapsed = int(time.time() - start_time)
                
                # Print progress every 15 seconds
                if elapsed % 15 == 0 and elapsed > 0:
                    print(f"   Still processing... ({elapsed}s elapsed)")
            
            if not upload_complete:
                print("⚠️ Did not see 'Checks complete' message, but proceeding...")
            
            # Small buffer after checks complete
            time.sleep(3)

            # Set title if provided - WITH BETTER WAITS AND FOCUS
            if title:
                print(f"✍️ Setting title: {title[:50]}...")
                try:
                    # Wait explicitly for the FIRST textbox (title field)
                    title_input = WebDriverWait(driver, 20).until(
                        EC.presence_of_element_located((By.XPATH, '(//div[@id="textbox" and @contenteditable="true"])[1]'))
                    )
                    
                    # Scroll to element to ensure it's visible
                    driver.execute_script("arguments[0].scrollIntoView(true);", title_input)
                    time.sleep(1)
                    
                    # Click to focus
                    title_input.click()
                    time.sleep(1)
                    
                    # Clear any existing content multiple ways
                    try:
                        title_input.clear()
                    except:
                        pass
                    
                    # Select all and delete
                    title_input.send_keys(Keys.CONTROL + "a")
                    time.sleep(0.5)
                    title_input.send_keys(Keys.DELETE)
                    time.sleep(0.5)
                    
                    # Type the title character by character for reliability
                    for char in title:
                        title_input.send_keys(char)
                        time.sleep(0.02)  # Small delay between characters
                    
                    # Verify title was entered
                    time.sleep(1)
                    entered_text = title_input.text
                    if len(entered_text) > 0:
                        print(f"✅ Title set successfully: {entered_text[:50]}...")
                    else:
                        print("⚠️ Title field appears empty, retrying...")
                        # Retry once
                        title_input.click()
                        time.sleep(1)
                        title_input.send_keys(title)
                        time.sleep(1)
                        print(f"✅ Title set on retry")
                        
                except Exception as e:
                    print(f"⚠️ Could not set title: {e}")
                    import traceback
                    traceback.print_exc()

            # Wait before moving to description
            time.sleep(2)

            # Set description if provided - WITH BETTER WAITS AND FOCUS
            if description:
                print(f"✍️ Setting description...")
                try:
                    # Wait explicitly for the SECOND textbox (description field)
                    desc_input = WebDriverWait(driver, 20).until(
                        EC.presence_of_element_located((By.XPATH, '(//div[@id="textbox" and @contenteditable="true"])[2]'))
                    )
                    
                    # Scroll to element
                    driver.execute_script("arguments[0].scrollIntoView(true);", desc_input)
                    time.sleep(1)
                    
                    # Click to focus
                    desc_input.click()
                    time.sleep(1)
                    
                    # Clear any existing content
                    try:
                        desc_input.clear()
                    except:
                        pass
                    
                    desc_input.send_keys(Keys.CONTROL + "a")
                    time.sleep(0.5)
                    desc_input.send_keys(Keys.DELETE)
                    time.sleep(0.5)
                    
                    # Type the description
                    # For long descriptions, we can type faster
                    desc_input.send_keys(description)
                    time.sleep(1)
                    
                    # Verify description was entered
                    entered_text = desc_input.text
                    if len(entered_text) > 10:
                        print(f"✅ Description set successfully ({len(entered_text)} characters)")
                    else:
                        print("⚠️ Description field appears empty, retrying...")
                        desc_input.click()
                        time.sleep(1)
                        desc_input.send_keys(description)
                        time.sleep(1)
                        print(f"✅ Description set on retry")
                        
                except Exception as e:
                    print(f"⚠️ Could not set description: {e}")
                    import traceback
                    traceback.print_exc()

            # Extra wait after filling both fields
            time.sleep(3)

            # Click "Yes, it's made for kids" radio button
            print("👶 Setting 'Made for kids' option...")
            try:
                # Multiple selectors for the "Yes, it's made for kids" radio button
                made_for_kids_selectors = [
                    '//tp-yt-paper-radio-button[@name="VIDEO_MADE_FOR_KIDS_MFK"]',
                    '//paper-radio-button[@name="VIDEO_MADE_FOR_KIDS_MFK"]',
                    '//*[contains(text(), "Yes, it\'s made for kids")]/ancestor::tp-yt-paper-radio-button',
                    '//*[@id="made-for-kids-group"]//tp-yt-paper-radio-button[1]'
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
                    print("⚠️ Could not find 'Made for kids' button, continuing anyway...")
                
                time.sleep(2)
                
            except Exception as e:
                print(f"⚠️ Error setting 'Made for kids': {e}")

            # Click Next button (Step 1: Details → Video elements)
            print("➡️ Step 1: Details → Video elements...")
            try:
                next_button = WebDriverWait(driver, 15).until(
                    EC.element_to_be_clickable((By.XPATH, '//*[@id="next-button"]'))
                )
                next_button.click()
                time.sleep(3)
                print("✅ Step 1 completed")
            except Exception as e:
                print(f"⚠️ Error on step 1: {e}")

            # Click Next button (Step 2: Video elements → Checks)
            print("➡️ Step 2: Video elements → Checks...")
            try:
                next_button = WebDriverWait(driver, 15).until(
                    EC.element_to_be_clickable((By.XPATH, '//*[@id="next-button"]'))
                )
                next_button.click()
                time.sleep(3)
                print("✅ Step 2 completed")
            except Exception as e:
                print(f"⚠️ Error on step 2: {e}")

            # Wait for copyright check to complete
            print("⏳ Waiting for copyright check...")
            time.sleep(5)  # Give it time to process
            
            # Check if copyright check is done
            try:
                # Look for "No issues found" or similar text
                copyright_status = WebDriverWait(driver, 30).until(
                    EC.presence_of_element_located((By.XPATH, '//*[contains(text(), "No issues found") or contains(text(), "Copyright")]'))
                )
                print("✅ Copyright check completed")
            except:
                print("⚠️ Copyright check status unclear, continuing...")
            
            time.sleep(2)

            # Click Next button (Step 3: Checks → Visibility)
            print("➡️ Step 3: Checks → Visibility...")
            try:
                next_button = WebDriverWait(driver, 15).until(
                    EC.element_to_be_clickable((By.XPATH, '//*[@id="next-button"]'))
                )
                next_button.click()
                time.sleep(3)
                print("✅ Step 3 completed")
            except Exception as e:
                print(f"⚠️ Error on step 3: {e}")

            # Select Public visibility
            print("🌍 Setting visibility to Public...")
            try:
                # Multiple selectors for the Public radio button
                public_selectors = [
                    '//tp-yt-paper-radio-button[@name="PUBLIC"]',
                    '//paper-radio-button[@name="PUBLIC"]',
                    '//*[contains(text(), "Public")]/ancestor::tp-yt-paper-radio-button',
                    '//*[@id="privacy-radios"]//tp-yt-paper-radio-button[3]'
                ]
                
                public_clicked = False
                for selector in public_selectors:
                    try:
                        public_button = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                        public_button.click()
                        public_clicked = True
                        print("✅ Selected 'Public' visibility")
                        break
                    except:
                        continue
                
                if not public_clicked:
                    print("⚠️ Could not find Public button, might already be selected")
                
                time.sleep(2)
                
            except Exception as e:
                print(f"⚠️ Error setting visibility: {e}")

            # Click Publish button
            print("🚀 Publishing video...")
            try:
                publish_button = WebDriverWait(driver, 15).until(
                    EC.element_to_be_clickable((By.XPATH, '//*[@id="done-button"]'))
                )
                publish_button.click()
                time.sleep(5)
                print("🎉 Video published successfully!")
                return True
            except Exception as e:
                print(f"⚠️ Error clicking publish: {e}")
                # Try alternative selector
                try:
                    publish_button = driver.find_element(By.XPATH, '//ytcp-button[@id="done-button"]')
                    publish_button.click()
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


# Import Keys at the top
from selenium.webdriver.common.keys import Keys


if __name__ == "__main__":
    print("=" * 60)
    print("🎬 AUTOTUBE - YouTube Video Uploader")
    print("=" * 60)
    
    result = YoutubeUploader.upload_latest_video()
    
    if result:
        print("\n✅ All done!")
    else:
        print("\n❌ Upload failed. Please check the errors above.")
    
    # Keep driver open for debugging
    print("\n💡 Chrome will stay open. Close manually when done.")
    input("Press Enter to cleanup and exit...")
    YoutubeUploader.cleanup_driver()
