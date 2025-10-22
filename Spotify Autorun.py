from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, WebDriverException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import ActionChains
import time

def safe_get_url(driver, url, max_retries=3):
    """Safely navigate to a URL with retries and error handling"""
    for attempt in range(max_retries):
        try:
            driver.get(url)
            return True
        except Exception as e:
            print(f"❌ Failed to navigate to {url} (attempt {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2)
    return False

def check_driver_alive(driver):
    """Check if the driver is still responsive"""
    try:
        driver.current_url
        return True
    except Exception:
        return False

def safe_get_current_url(driver):
    """Safely get current URL with error handling"""
    try:
        return driver.current_url
    except Exception as e:
        print(f"❌ Error getting current URL: {e}")
        return ""

# === STATIC CONFIG ===
brave_path = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"
chromedriver_path = r"D:\Automations\Chromedriver\chromedriver.exe"
base_profile_dir = r"D:\Automations\Braves"

# --- Add this new section for user input and playlist selection ---
playlists = {
    '1': {"name": "NAS LEGENDS", "id": "0QmeNTNpmXCMYMnfUElIqb"},
    '2': {"name": "NAS ELITE", "id": "7EYdQbtIwnVFUbIOOva0HI"},
    '3': {"name": "NAS SUPERSTARS", "id": "0VU5Mk2VKp80eBK8iB7ROZ"},
    '4': {"name": "NAS ALL-STARS", "id": "1agpv6FCGMrvhw27myRJ1s"},
    '5': {"name": "NAS", "id": "7aJOhDOlQVCITOCnV7XWpZ"},
    '6': {"name": "NAS PRO", "id": "5TCao2OVhZGrShZM2zsMLq"},
    '7': {"name": "NAS 101", "id": "6pUo5Yekpi89jNpJ4hDcqz"},
    '0': {"name": "End Script", "id": None}
}

# Correct Spotify URLs
SPOTIFY_WEB_PLAYER_URL = "https://open.spotify.com"

nas_util_url = "https://spotifyfollow.a2hosted.com/nas"
nas_login_url = "https://spotifyfollow.a2hosted.com/nas/login"

# === GENERAL AUTOMATION SETTINGS ===
max_page_load_attempts = 3 # Number of attempts for critical page loads/interactions before giving up on a step

# === PROFILES TO RUN ===
profiles = [
    # Profiles 5-8: Just need the browser profile folder
    {"folder": "Profile 5"},
    {"folder": "Profile 6"},
    {"folder": "Profile 7"},
    {"folder": "Profile 8"},
]

summary = {}
active_drivers = {} # Using a dictionary to map profile folders to driver instances
selected_playlist = None
playlist_name = ""
playlist_id = ""


def try_click(driver, selector, by=By.CSS_SELECTOR, label="", max_tries=2, delay=1.5):
    """
    Attempts to click an element, with retries. Returns True on success, False on failure.
    """
    for attempt in range(max_tries):
        try:
            btn = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((by, selector)))
            driver.execute_script("arguments[0].scrollIntoView({behavior: 'auto', block: 'center'});", btn)
            btn.click()
            print(f"✅ {label} clicked successfully (attempt {attempt + 1}).")
            return True
        except TimeoutException:
            print(f"❌ {label} not found or not clickable within timeout (attempt {attempt + 1}).")
            time.sleep(delay)
        except Exception as e:
            print(f"❌ Failed to click {label} (attempt {attempt + 1}). Error: {e}")
            time.sleep(delay)
    return False

def click_with_retries(driver, element, max_attempts=3, delay=1):
    """
    Attempts to click a WebElement directly, with retries. Returns True on success, False on failure.
    """
    for i in range(max_attempts):
        try:
            WebDriverWait(driver, 5).until(EC.element_to_be_clickable(element))
            element.click()
            return True
        except Exception as e:
            print(f"Click attempt {i+1} failed: {e}")
            time.sleep(delay)
    return False

def is_spotify_logged_in(driver, timeout=10):
    print("🔄 Checking Spotify login status...")

    logged_in_indicators = [
        (By.CSS_SELECTOR, 'a[href="/collection"]'),  # Your Library link
        (By.CSS_SELECTOR, 'button[data-testid="user-widget-link"]'),  # Profile button
        (By.CSS_SELECTOR, 'div[role="search"] input[role="searchbox"]')  # Search input
    ]

    logged_out_indicators = [
        (By.CSS_SELECTOR, 'button[data-testid="login-button"]'),  # The general login button
        (By.CSS_SELECTOR, 'a[data-testid="signup-button"]'),
        (By.XPATH, '//a[contains(@href, "/signup")]'),
        (By.XPATH, '//h2[contains(text(), "Create your first playlist")]')
    ]

    for attempt in range(1, 4):
        print(f"🔄 Attempt {attempt}: Looking for both logged-in and logged-out indicators...")

        # --- Check for Logged-In Indicators ---
        for by, selector in logged_in_indicators:
            try:
                WebDriverWait(driver, 5).until(EC.visibility_of_element_located((by, selector)))
                print(f"✅ Found logged-in indicator: {selector}. User is logged in.")
                return True
            except TimeoutException:
                pass  # Keep going if not found

        # --- Check for Logged-Out Indicators ---
        for by, selector in logged_out_indicators:
            try:
                WebDriverWait(driver, 5).until(EC.visibility_of_element_located((by, selector)))
                print(f"❌ Found logged-out indicator: {selector}. User is NOT logged in.")
                return False
            except TimeoutException:
                pass  # Keep going if not found

        # If neither was found after checking all selectors, close the tab and open a new one
        if attempt < 3:
            print(f"❓ Could not find a definitive login/logout indicator. Closing and reopening Spotify page for attempt {attempt + 1}...")
            # Get the current window handle
            original_tab = driver.current_window_handle
            
            # Open a new tab
            driver.execute_script("window.open('');")
            time.sleep(1) # Give it a moment to open
            
            # Switch to the new tab and navigate to Spotify
            new_tab = driver.window_handles[-1]
            driver.switch_to.window(new_tab)
            driver.get('https://open.spotify.com/')
            
            # Close the old tab
            driver.switch_to.window(original_tab)
            driver.close()
            
            # Switch back to the new tab for the next iteration
            driver.switch_to.window(new_tab)
            time.sleep(5)  # Wait for the new page to load
            
    # If all attempts fail
    print("❌ Failed to definitively determine login status after 3 attempts. Defaulting to NOT logged in for safety.")
    return False

# --- Main Automation Loop ---
while True:
    print("🔔 Profiles 5-8")
    print("\n--- 🎶 Playlist Selection ---")
    print("Please choose a playlist by entering its number:")
    for num, pl in playlists.items():
        print(f"   {num} - {pl['name']}")
    
    choice = input("Enter your choice (0-7): ")
    
    if choice == '0':
        print("✅ Ending script as requested. Closing all open browsers.")
        # --- Close all active browser profiles ---
        for folder, driver in active_drivers.items():
            try:
                print(f"🔒 Closing browser for {folder}...")
                driver.quit()
            except Exception as e:
                print(f"⚠️ Error closing browser for {folder}: {e}")
        break # Exit the main while loop
    
    if choice in playlists:
        selected_playlist = playlists[choice]
        playlist_name = selected_playlist["name"]
        playlist_id = selected_playlist["id"]
        playlist_uri = f"spotify:playlist:{playlist_id}"
        print(f"✅ You have selected to play: {playlist_name}")
    else:
        print("❌ Invalid choice. Please enter a number from 0 to 7.")
        continue # Skip to the next iteration of the while loop

    # --- Profile Processing ---
    for profile in profiles:
        folder = profile["folder"]

        print(f"\n=== 🚀 Processing {folder} ===")
        summary[folder] = "❌ Fail"

        # Check if a driver for this profile is already open
        if folder in active_drivers:
            driver = active_drivers[folder]
            print(f"✅ Found existing Brave browser for {folder}.")
        else:
            # Launch a new Brave browser for this profile
            print(f"🔄 Launching a new Brave browser for {folder}...")
            user_data_dir = f"{base_profile_dir}\\{folder}"
            options = Options()
            options.binary_location = brave_path
            options.add_argument(f'--user-data-dir={user_data_dir}')
            options.add_argument("--mute-audio")
            options.add_argument("--start-maximized")

            try:
                service = Service(chromedriver_path)
                service.start()
                driver = webdriver.Chrome(service=service, options=options)
                active_drivers[folder] = driver
            except WebDriverException as e:
                print(f"❌ Cannot launch {folder} — profile may be in use or corrupted. Error: {e}")
                continue # Skip to next profile
            except Exception as e:
                print(f"❌ Unexpected error in {folder}: {e}")
                continue # Skip to next profile

        # --- Memory Efficient Tab Management ---
        main_spotify_tab = None
        nas_tab = None
        tabs_to_keep = set()
        
        try:
            for handle in driver.window_handles:
                try:
                    driver.switch_to.window(handle)
                    current_url = safe_get_current_url(driver)
                    if current_url and ("open.spotify.com" in current_url or "play.spotify.com" in current_url):
                        print(f"✅ Found existing Spotify tab.")
                        main_spotify_tab = handle
                        tabs_to_keep.add(handle)
                    elif current_url and "spotifyfollow.a2hosted.com/nas" in current_url:
                        print(f"✅ Found existing NAS tab.")
                        nas_tab = handle
                        tabs_to_keep.add(handle)
                except Exception as e:
                    print(f"⚠️ Error accessing tab {handle}: {e}")
                    # If we can't access a tab, it might be crashed - skip it
                    continue
        except Exception as e:
            print(f"❌ Browser connection lost for {folder}. Error: {e}")
            print(f"🔄 Closing and restarting browser for {folder}...")
            
            # Remove the problematic driver from active_drivers
            if folder in active_drivers:
                try:
                    active_drivers[folder].quit()
                except:
                    pass  # Ignore errors when quitting
                del active_drivers[folder]
            
            # Restart the browser
            print(f"🔄 Restarting Brave browser for {folder}...")
            user_data_dir = f"{base_profile_dir}\\{folder}"
            options = Options()
            options.binary_location = brave_path
            options.add_argument(f'--user-data-dir={user_data_dir}')
            options.add_argument("--mute-audio")
            options.add_argument("--start-maximized")
            options.add_argument("--disable-dev-shm-usage")  # Helps with memory issues
            options.add_argument("--no-sandbox")  # Helps with stability

            try:
                service = Service(chromedriver_path)
                service.start()
                driver = webdriver.Chrome(service=service, options=options)
                active_drivers[folder] = driver
                print(f"✅ Browser restarted successfully for {folder}")
                # Reset tabs since we have a fresh browser
                main_spotify_tab = None
                nas_tab = None
                tabs_to_keep = set()
            except Exception as restart_error:
                print(f"❌ Failed to restart browser for {folder}: {restart_error}")
                summary[folder] = "❌ Browser Error"
                continue  # Skip to next profile

        # Close all unrelated tabs (with error handling)
        try:
            for handle in driver.window_handles[:]:
                if handle not in tabs_to_keep:
                    try:
                        driver.switch_to.window(handle)
                        current_url = safe_get_current_url(driver)
                        print(f"❌ Closing unrelated tab: {current_url}")
                        driver.close()
                    except Exception as e:
                        print(f"⚠️ Error closing tab: {e}")
            # After closing, switch to a known good window
            if driver.window_handles:
                driver.switch_to.window(driver.window_handles[0])
        except Exception as e:
            print(f"⚠️ Error during tab cleanup: {e}")

        # --- Handle tabs and switch to the correct ones ---
        # main_spotify_tab = None
        # nas_tab = None
        
        # # New approach: Iterate through existing windows to find the tabs
        # for handle in driver.window_handles:
        #     driver.switch_to.window(handle)
        #     current_url = driver.current_url
        #     if "open.spotify.com" in current_url or "play.spotify.com" in current_url:
        #         print(f"✅ Found existing Spotify tab.")
        #         main_spotify_tab = handle
        #     elif "spotifyfollow.a2hosted.com/nas" in current_url:
        #         print(f"✅ Found existing NAS tab.")
        #         nas_tab = handle

        # # If Spotify tab wasn't found, open it with retries
        # if not main_spotify_tab:
        #     print(f"🔄 No Spotify tab found. Opening a new one...")
            
        #     # Use a retry loop for creating a new tab
        #     for attempt in range(1, 4):
        #         try:
        #             driver.switch_to.window(driver.window_handles[0])  # Switch to a known handle
        #             driver.execute_script(f"window.open('{SPOTIFY_WEB_PLAYER_URL}', '_blank');")
                    
        #             # Wait for the new window to be present
        #             WebDriverWait(driver, 20).until(EC.number_of_windows_to_be(len(driver.window_handles) + 1))
                    
        #             # Switch to the new tab
        #             new_tab_handle = driver.window_handles[-1]
        #             driver.switch_to.window(new_tab_handle)
                    
        #             # Validate the URL of the new tab
        #             WebDriverWait(driver, 10).until(EC.url_contains("spotify.com"))
        #             main_spotify_tab = new_tab_handle
        #             print(f"✅ Opened new Spotify tab successfully on attempt {attempt}.")
        #             break # Exit the retry loop on success
                
        #         except TimeoutException:
        #             print(f"[{folder}] ❌ TimeoutException: Failed to open new Spotify tab on attempt {attempt}. Retrying...")
        #             if attempt == 3:
        #                 print(f"[{folder}] ❌ All attempts to open a new Spotify tab failed. Skipping to the next profile.")
        #                 summary[folder] = "❌ Fail - Tab Blocked"
        #                 continue # This will skip the rest of the code for this profile and move to the next profile in the loop.
        #     else:
        #         # This 'else' block runs if the for loop completes without a 'break'
        #         # which means all 3 attempts failed. The continue statement above handles this.
        #         continue

        # # If we successfully found or opened a tab, switch to it and proceed
        # if main_spotify_tab:
        #     driver.switch_to.window(main_spotify_tab)
        # else:
        #     # If after all retries we still don't have a Spotify tab, skip
        #     continue
        
        # --- Spotify Login & Playback Block ---
        play_success = False
        for attempt in range(1, 4):  # Overall retry loop for Spotify login & playback
            print(f"\n🎯 Attempt {attempt}: Spotify login & playback...")

            # --- Attempt to load Spotify Web Player ---
            loaded_spotify = False
            for load_try in range(max_page_load_attempts):
                try:
                    print(f"[{folder}] Navigating to Spotify Web Player ({load_try + 1}/{max_page_load_attempts})...")
                    driver.get(SPOTIFY_WEB_PLAYER_URL)
                    WebDriverWait(driver, 15).until(
                        EC.presence_of_element_located((By.TAG_NAME, "body"))  # Wait for any element to be present
                    )
                    loaded_spotify = True
                    print(f"[{folder}] ✅ Spotify Web Player loaded successfully.")
                    break
                except TimeoutException:
                    print(f"[{folder}] ❌ Spotify Web Player failed to load within timeout. Refreshing...")
                    driver.refresh()
                    time.sleep(5)
                except WebDriverException as e:
                    print(f"[{folder}] ❌ WebDriver error loading Spotify: {e}. Refreshing...")
                    driver.refresh()
                    time.sleep(5)
                except Exception as e:
                    print(f"[{folder}] ❌ Unexpected error loading Spotify: {e}. Refreshing...")
                    driver.refresh()
                    time.sleep(5)
            
            if not loaded_spotify:
                print(f"[{folder}] ❌ Failed to load Spotify Web Player after {max_page_load_attempts} attempts. Cannot proceed with Spotify for this profile.")
                continue  # Move to next overall attempt

            time.sleep(3)  # Give a little extra time after successful load

            if not is_spotify_logged_in(driver):
                print(f"[{folder}] 🔐 Spotify is NOT logged in. Skipping this profile.")
                summary[folder] = "⏭️ Skipped - Not logged in"
                break  # Exit the overall attempt loop and move to next profile
            else:
                print("✅ Already logged into Spotify. Proceeding with playlist playback.")
            # --- Spotify Playback ---
            search_found = False
            playback_attempt_successful = False
            shuffle_successful = False
            repeat_successful = False
            skip_forward_successful = False
            for refresh_attempt in range(3):
                if playback_attempt_successful:
                    print("✅ Playback already confirmed, skipping playback block.")
                    break
                try:
                    time.sleep(3)
                    library_button = driver.find_elements(By.XPATH, '//button[@aria-label="Open Your Library"]')
                    if library_button and library_button[0].is_displayed():
                        print(f"📂 'Your Library' is collapsed — clicking (attempt {refresh_attempt + 1})...")
                        click_with_retries(driver, library_button[0])
                        time.sleep(2)
                    else:
                        print(f"📂 'Your Library' already open or not found (attempt {refresh_attempt + 1}).")

                    if not search_found:
                        search = WebDriverWait(driver, 10).until(EC.presence_of_element_located(
                            (By.CSS_SELECTOR, 'div[role="search"] input[role="searchbox"]')))
                        search.clear()
                        search.send_keys(playlist_name)
                        print(f"🔎 Searching playlist: '{playlist_name}' (attempt {refresh_attempt + 1})...")
                        time.sleep(2)
                        search_found = True
                    # --- Double-click playlist logic ---
                    for dbl in range(3):
                        if playback_attempt_successful:
                            print("✅ Playback already confirmed, skipping double-click block.")
                            break
                        try:
                            sidebar_btn = WebDriverWait(driver, 12).until(EC.element_to_be_clickable(
                                (By.CSS_SELECTOR, f'div[role="button"][aria-labelledby^="listrow-title-{playlist_uri}"]')))
                            driver.execute_script("arguments[0].scrollIntoView({behavior:'smooth',block:'center'});", sidebar_btn)
                            ActionChains(driver).double_click(sidebar_btn).perform()
                            print(f"🖱️ Double-clicked playlist (attempt {dbl + 1})")
                            time.sleep(4)
                            current_url = driver.current_url
                            if playlist_id not in current_url:
                                print(f"⚠️ URL mismatch! Expected URI '{playlist_uri}' not in current URL '{current_url}'.")
                                print("❌ Double-click failed to navigate to the correct playlist page. Retrying the search and click...")
                                driver.refresh()
                                time.sleep(5)
                                continue
                            print(f"✅ URL confirmed: '{current_url}' contains playlist URI.")
                            WebDriverWait(driver, 12).until(EC.presence_of_element_located(
                                (By.CSS_SELECTOR, 'button[data-testid="control-button-playpause"][aria-label="Pause"]')))
                            print("✅ Playback confirmed.")
                            playback_attempt_successful = True
                            break
                        except Exception as e:
                            print(f"⏱️ Playback not confirmed after double-click {dbl + 1}. Error: {e}")
                            print(f"    Details: {e}")
                            if dbl < 2:
                                print("🔄 Refreshing page before next playback attempt...")
                                driver.refresh()
                                time.sleep(5)
                            time.sleep(2)
                    if playback_attempt_successful:
                        break  # Exit the search retry loop after successful playback
                except Exception as e:
                    print(f"� Search input or library not ready (attempt {refresh_attempt + 1}) — refreshing. Error: {e}")
                    driver.refresh()
                    time.sleep(5)
            if not search_found:
                print("❌ Search input failed after 3 refresh attempts. Skipping playback attempt for this profile.")
                continue # Move to next overall attempt

            # --- Shuffle and Repeat buttons ---
            print(f"[{folder}] Attempting to enable shuffle and repeat...")
            if not shuffle_successful:
                if try_click(driver, 'button[data-testid="control-button-shuffle"][aria-checked="false"]', label="Shuffle button"):
                    print(f"[{folder}] ✅ Shuffle enabled.")
                    shuffle_successful = True
                else:
                    print(f"[{folder}] ⚠️ Shuffle button not found or already enabled/not clickable.")
                time.sleep(1)
            else:
                print(f"[{folder}] ✅ Shuffle already enabled, skipping shuffle block.")

            if not repeat_successful:
                if try_click(driver, 'button[data-testid="control-button-repeat"][aria-checked="false"]', label="Repeat button"):
                    print(f"[{folder}] ✅ Repeat enabled.")
                    repeat_successful = True
                else:
                    print(f"[{folder}] ⚠️ Repeat button not found or already enabled/not clickable.")
                time.sleep(2)
            else:
                print(f"[{folder}] ✅ Repeat already enabled, skipping repeat block.")

            # --- Skip Forward Button ---
            print(f"[{folder}] Attempting to click skip forward...")
            if not skip_forward_successful:
                for attempt in range(3):
                    if try_click(driver, 'button[data-testid="control-button-skip-forward"]', label="Skip Forward button"):
                        print(f"[{folder}] ✅ Skip Forward clicked.")
                        skip_forward_successful = True
                        break
                    else:
                        print(f"[{folder}] ⚠️ Skip Forward button not found or not clickable (attempt {attempt+1}).")
                        time.sleep(1)
                if not skip_forward_successful:
                    print(f"[{folder}] ❌ Could not click Skip Forward after 3 attempts.")
            else:
                print(f"[{folder}] ✅ Skip Forward already clicked, skipping skip forward block.")

            # --- NAS Submit Block ---
            summary[folder] = "✅ Success"
            print("🌐 NAS Submit...")

            # Always redirect NAS tab to nas_login_url before submit
            if not nas_tab:
                driver.execute_script(f"window.open('{nas_login_url}', '_blank');")
                WebDriverWait(driver, 20).until(EC.number_of_windows_to_be(len(driver.window_handles)))
                driver.switch_to.window(driver.window_handles[-1])
                nas_tab = driver.current_window_handle
                print(f"🔄 Opened new NAS tab.")
            else:
                driver.switch_to.window(nas_tab)
                print(f"✅ Switched to existing NAS tab.")
                # Ensure NAS tab is at nas_login_url
                if driver.current_url != nas_login_url:
                    print(f"🔄 Redirecting NAS tab to login page...")
                    driver.get(nas_login_url)
            time.sleep(5)

            # --- Check if already logged in by looking for welcome message ---
            try:
                welcome_element = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, '//h3[@id="results1" and contains(text(), "Welcome")]'))
                )
                print(f"[{folder}] ✅ Welcome message found. User is already logged in. Skipping login button click.")
            except TimeoutException:
                print(f"[{folder}] ℹ️ Welcome message not found. Checking for NAS login button...")
                # --- Check for NAS login button and click if present ---
                try:
                    login_btn = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, 'a#loginButton.btn.btn-primary'))
                    )
                    print(f"[{folder}] ✅ NAS Login button found, clicking...")
                    click_with_retries(driver, login_btn)
                    time.sleep(10)  # Wait for login process
                except TimeoutException:
                    print(f"[{folder}] ℹ️ NAS Login button not found, continuing with submit.")
                except Exception as e:
                    print(f"[{folder}] ❌ Error checking/clicking NAS Login button: {e}")
            except Exception as e:
                print(f"[{folder}] ❌ Error checking for welcome message: {e}. Proceeding with login button check...")
                # --- Check for NAS login button and click if present ---
                try:
                    login_btn = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, 'a#loginButton.btn.btn-primary'))
                    )
                    print(f"[{folder}] ✅ NAS Login button found, clicking...")
                    click_with_retries(driver, login_btn)
                    time.sleep(10)  # Wait for login process
                except TimeoutException:
                    print(f"[{folder}] ℹ️ NAS Login button not found, continuing with submit.")
                except Exception as e:
                    print(f"[{folder}] ❌ Error checking/clicking NAS Login button: {e}")

            nas_success = False
            for nas_attempt in range(1, 4):
                print(f"[{folder}] NAS operation attempt {nas_attempt}/3...")
                try:
                    print(f"[{folder}] -> Attempting to trigger 'onAutoSubmitButtonPressed()' via JavaScript...")
                    triggered_auto_submit = False
                    try:
                        auto_submit_btn_present = WebDriverWait(driver, 5).until(
                            EC.presence_of_element_located((By.ID, "autoSubmitButton"))
                        )
                        driver.execute_script("arguments[0].scrollIntoView({behavior: 'auto', block: 'center'});", auto_submit_btn_present)
                        driver.execute_script("onAutoSubmitButtonPressed();")
                        print(f"[{folder}] -> JavaScript function 'onAutoSubmitButtonPressed()' executed.")
                        triggered_auto_submit = True
                    except TimeoutException:
                        print(f"[{folder}] -> 'autoSubmitButton' element not found for direct JS execution within timeout.")
                    except Exception as e:
                        print(f"[{folder}] -> Error executing 'onAutoSubmitButtonPressed()' via JS: {e}")

                    if triggered_auto_submit:
                        print(f"[{folder}] -> Checking for 'Submitting...' text after 'Auto Submit' trigger...")
                        try:
                            WebDriverWait(driver, 20).until(
                                EC.visibility_of_element_located((By.XPATH, "//*[contains(text(), 'Submitting...')]"))
                            )
                            print(f"[{folder}] ✅ 'Submitting...' text appeared. Auto Submit confirmed successful.")
                            nas_success = True
                            break
                        except TimeoutException:
                            print(f"[{folder}] ❌ 'Submitting...' text did NOT appear after triggering 'Auto Submit'. The submission might not have triggered or completed within timeout. Refreshing.")
                            driver.refresh()
                            time.sleep(5)
                            continue
                        except Exception as e:
                            print(f"[{folder}] ❌ Error checking for 'Submitting...' text: {e}. Refreshing.")
                            driver.refresh()
                            time.sleep(5)
                            continue
                    else:
                        print(f"[{folder}] -> Direct 'Auto Submit' trigger failed. Trying 'Login' button again if present...")
                        # Try clicking login button again if present
                        try:
                            login_btn = WebDriverWait(driver, 5).until(
                                EC.presence_of_element_located((By.CSS_SELECTOR, 'a#loginButton.btn.btn-primary'))
                            )
                            print(f"[{folder}] ✅ NAS Login button found, clicking again...")
                            click_with_retries(driver, login_btn)
                            time.sleep(10)
                        except TimeoutException:
                            print(f"[{folder}] ℹ️ NAS Login button not found, continuing.")
                        except Exception as e:
                            print(f"[{folder}] ❌ Error checking/clicking NAS Login button: {e}")

                        # Try auto submit again after login
                        try:
                            auto_submit_btn_present = WebDriverWait(driver, 5).until(
                                EC.presence_of_element_located((By.ID, "autoSubmitButton"))
                            )
                            driver.execute_script("arguments[0].scrollIntoView({behavior: 'auto', block: 'center'});", auto_submit_btn_present)
                            driver.execute_script("onAutoSubmitButtonPressed();")
                            print(f"[{folder}] -> JavaScript function 'onAutoSubmitButtonPressed()' executed after Login.")
                            triggered_auto_submit = True
                        except TimeoutException:
                            print(f"[{folder}] -> 'autoSubmitButton' element not found after Login for direct JS execution within timeout.")
                        except Exception as e:
                            print(f"[{folder}] -> Error executing 'onAutoSubmitButtonPressed()' after Login: {e}")

                        if triggered_auto_submit:
                            print(f"[{folder}] -> Checking for 'Submitting...' text after second 'Auto Submit' trigger...")
                            try:
                                WebDriverWait(driver, 20).until(
                                    EC.visibility_of_element_located((By.XPATH, "//*[contains(text(), 'Submitting...')]"))
                                )
                                print(f"[{folder}] ✅ 'Submitting...' text appeared after login. Auto Submit confirmed successful.")
                                nas_success = True
                                break
                            except TimeoutException:
                                print(f"[{folder}] ❌ 'Submitting...' text did NOT appear after triggering 'Auto Submit' post-login. Refreshing.")
                                driver.refresh()
                                time.sleep(5)
                                continue
                            except Exception as e:
                                print(f"[{folder}] ❌ Error checking for 'Submitting...' text post-login: {e}. Refreshing.")
                                driver.refresh()
                                time.sleep(5)
                                continue
                        else:
                            print(f"[{folder}] ❌ Second 'Auto Submit' trigger failed. Refreshing page for next attempt.")
                            driver.refresh()
                            time.sleep(5)
                            continue

                except Exception as e:
                    print(f"[{folder}] ❌ An unexpected general error occurred during NAS operations: {e}. Refreshing page for next attempt.")
                    driver.refresh()
                    time.sleep(5)

            if nas_success:
                print(f"[{folder}] ✅ NAS operations completed successfully.")
                # Switch to Spotify tab after NAS operations
                if main_spotify_tab is not None:
                    try:
                        driver.switch_to.window(main_spotify_tab)
                        print(f"[{folder}] 🔄 Switched to Spotify tab after NAS operations.")
                        # --- Try skip forward again after NAS submit ---
                        print(f"[{folder}] Attempting to click skip forward again after NAS submit...")
                        for attempt in range(3):
                            if try_click(driver, 'button[data-testid="control-button-skip-forward"]', label="Skip Forward button (post-NAS)"):
                                print(f"[{folder}] ✅ Skip Forward clicked after NAS submit.")
                                break
                            else:
                                print(f"[{folder}] ⚠️ Skip Forward button not found or not clickable after NAS submit (attempt {attempt+1}).")
                                time.sleep(1)
                    except Exception as e:
                        print(f"[{folder}] ⚠️ Could not switch to Spotify tab: {e}")
            else:
                print(f"[{folder}] ❌ NAS operations failed after all {nas_attempt} attempts.")

            print(f"[{folder}] ⚠️ NAS tab left open for manual inspection: {driver.current_url}")
            play_success = True
            break
        
        if not play_success:
            print(f"🚫 All Spotify login and playback attempts failed for {folder}. Moving to next profile.")

        print(f"✅ {folder} finished. Brave browser for this profile remains open.\n{'-'*60}")
        
# === FINAL SUMMARY ===
print("\n" + "="*60)
print("=== SCRIPT FINISHED ===")
print("=== RUN SUMMARY ===")
for folder, status in summary.items():
    print(f"  [{folder}]: {status}")
print("="*60)