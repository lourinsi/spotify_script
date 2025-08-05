from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, WebDriverException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import ActionChains
import time

# === STATIC CONFIG ===
brave_path = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"
chromedriver_path = r"C:\Automations\Chromedriver\chromedriver.exe"
base_profile_dir = r"C:\Automations\Braves"
playlist_name = "NAS 101"
playlist_id = "6pUo5Yekpi89jNpJ4hDcqz"

# --- CRITICAL: CORRECTED SPOTIFY URLs ---
# These are standard Spotify URLs. Please verify if they are correct for your usage.
# If you have a specific local setup (like a proxy or local routing) that
# relied on your previous `googleusercontent.com/spotify.com` URLs,
# you will need to revert these specific URL definitions.
SPOTIFY_PLAYLIST_URL = f"https://open.spotify.com/playlist/{playlist_id}" # Example: Actual playlist URL
SPOTIFY_WEB_PLAYER_URL = "https://open.spotify.com/" # Example: Main Spotify Web Player URL
SPOTIFY_LOGIN_PAGE_URL = "https://accounts.spotify.com/en/login" # Example: Direct Spotify Login Page URL

playlist_uri = f"spotify:playlist:{playlist_id}"
nas_util_url = "https://spotifyfollow.a2hosted.com/nas"
nas_login_url = "https://spotifyfollow.a2hosted.com/nas/login"

# === GENERAL AUTOMATION SETTINGS ===
max_page_load_attempts = 3 # Number of attempts for critical page loads/interactions before giving up on a step

# === PROFILES TO RUN ===
profiles = [
    # Profile 1: Only Google Login for Spotify
    {"folder": "Profile 1", "email": "jamesjack2323g@gmail.com", "name": "James Jack", "spotify_password": None, "fb_password": None},
    # Profiles 5-8: Only Facebook Login for Spotify
    {"folder": "Profile 5", "email": "lorenzoleorojas@gmail.com", "name": "Lorenz Leo Rojas", "spotify_password": None, "fb_password": "Facebook@Wr0ng?Main?"},
    {"folder": "Profile 6", "email": "nfthighvalueman@gmail.com", "name": "Leron James", "spotify_password": None, "fb_password": "Facebook@Wr0ng?"},
    {"folder": "Profile 7", "email": "iamlourinsi@gmail.com", "name": "Mysty Bryant", "spotify_password": None, "fb_password": "Facebook@Wr0ng?Main?"},
    {"folder": "Profile 8", "email": "19100121@usc.edu.com", "name": "Fayke lourinsi", "spotify_password": None, "fb_password": "Facebook@Wr0ng?"},
]

summary = {}
active_drivers = [] # List to hold all active driver instances

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
        (By.CSS_SELECTOR, 'a[href="/collection"]'), # Your Library link
        (By.CSS_SELECTOR, 'button[data-testid="user-widget-link"]'), # Profile button
        (By.CSS_SELECTOR, 'div[role="search"] input[role="searchbox"]') # Search input if already logged in and on homepage
    ]

    print("Attempting to find logged-in indicators...")
    for by, selector in logged_in_indicators:
        try:
            WebDriverWait(driver, 5).until(EC.visibility_of_element_located((by, selector)))
            print(f"✅ Found logged-in indicator: {selector}. User is logged in.")
            return True
        except TimeoutException:
            pass

    logged_out_indicators = [
        (By.CSS_SELECTOR, 'button[data-testid="login-button"]'), # The general login button
        (By.CSS_SELECTOR, 'a[data-testid="signup-button"]'),
        (By.XPATH, '//a[contains(@href, "/signup")]'),
        (By.XPATH, '//h2[contains(text(), "Create your first playlist")]'),
        (By.CSS_SELECTOR, 'input[placeholder="What do you want to play?"]') # This could be present even if logged in
    ]

    print("No immediate logged-in indicators found. Checking for logged-out indicators...")
    for by, selector in logged_out_indicators:
        try:
            WebDriverWait(driver, 5).until(EC.visibility_of_element_located((by, selector)))
            print(f"❌ Found logged-out indicator: {selector}. User is NOT logged in.")
            return False
        except TimeoutException:
            pass

    print("❓ Could not definitively determine login status based on direct indicators. Defaulting to NOT logged in for safety.")
    return False


# --- Main Automation Loop ---
for profile in profiles:
    folder = profile["folder"]
    profile_email = profile["email"] # Use a general name as it can be Google or Facebook email
    facebook_password = profile.get("fb_password")
    spotify_password = profile.get("spotify_password") # This will be None for Profile 1 and 5-8 now.

    print(f"\n=== 🚀 Launching {folder} ===")
    summary[folder] = "❌ Fail"

    user_data_dir = f"{base_profile_dir}\\{folder}"
    options = Options()
    options.binary_location = brave_path
    options.add_argument(f'--user-data-dir={user_data_dir}')
    options.add_argument("--mute-audio")
    options.add_argument("--start-maximized")

    driver = None

    try:
        service = Service(chromedriver_path)
        driver = webdriver.Chrome(service=service, options=options)
        active_drivers.append(driver)

        print("🧹 Closing all extra tabs (except initial blank tab if present)...")
        initial_window_handle = driver.window_handles[0]
        for handle in driver.window_handles:
            if handle != initial_window_handle:
                driver.switch_to.window(handle)
                driver.close()
        driver.switch_to.window(initial_window_handle)
        main_spotify_tab = initial_window_handle
        initial_window_count = len(driver.window_handles)

        # --- Spotify Login & Playback Block ---
        play_success = False
        for attempt in range(1, 4): # Overall retry loop for Spotify login & playback
            print(f"\n🎯 Attempt {attempt}: Spotify login & playback...")

            # --- Attempt to load Spotify Web Player ---
            loaded_spotify = False
            for load_try in range(max_page_load_attempts):
                try:
                    print(f"[{folder}] Navigating to Spotify Web Player ({load_try + 1}/{max_page_load_attempts})...")
                    driver.get(SPOTIFY_WEB_PLAYER_URL)
                    WebDriverWait(driver, 15).until(
                        EC.presence_of_element_located((By.TAG_NAME, "body")) # Wait for any element to be present
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
                continue # Move to next overall attempt

            time.sleep(3) # Give a little extra time after successful load

            if not is_spotify_logged_in(driver):
                print(f"[{folder}] 🔐 Spotify is NOT logged in. Initiating login process...")
                
                login_initiated = False
                for login_btn_try in range(max_page_load_attempts):
                    if try_click(driver, 'button[data-testid="login-button"]', label="Spotify Top-Right Login Button"):
                        print(f"[{folder}] ✅ Clicked Spotify 'Log in' button. Waiting for login page/modal...")
                        time.sleep(3) # Give it time to redirect or open a modal
                        login_initiated = True
                        break
                    else:
                        print(f"[{folder}] ❌ Spotify 'Log in' button not found (attempt {login_btn_try + 1}). Refreshing page to retry finding it...")
                        driver.refresh()
                        time.sleep(5)

                if not login_initiated:
                    print(f"[{folder}] ❌ Failed to find and click the Spotify 'Log in' button after {max_page_load_attempts} attempts. Cannot proceed with Spotify for this profile.")
                    continue # Move to next overall attempt

                # Logic for Profile 1: Google Login ONLY
                if folder == "Profile 1":
                    print(f"[{folder}] Attempting to log in via Google (explicitly for Profile 1).")
                    google_login_successful_this_try = False
                    for google_try in range(max_page_load_attempts):
                        if try_click(driver, 'button[data-testid="google-login"]', label="Continue with Google Button"):
                            print(f"[{folder}] ✅ Clicked 'Continue with Google' button. Waiting for Google authentication...")
                            time.sleep(10) # Give ample time for Google redirect/popup and authentication
                            
                            if is_spotify_logged_in(driver):
                                print(f"[{folder}] ✅ Successfully logged into Spotify via Google.")
                                google_login_successful_this_try = True
                                break # Exit google_try loop
                            else:
                                print(f"[{folder}] ❌ Spotify login via Google failed or did not complete after re-check (attempt {google_try + 1}). Current URL: {driver.current_url}. Refreshing to retry.")
                                driver.save_screenshot(f"debug_spotify_google_login_failed_{folder}_{int(time.time())}_try{google_try}.png") # Screenshot on failure
                                driver.refresh()
                                time.sleep(5)
                        else:
                            print(f"[{folder}] ❌ 'Continue with Google' button not found (attempt {google_try + 1}). Refreshing page to retry finding it.")
                            driver.refresh()
                            time.sleep(5)

                    if not google_login_successful_this_try:
                        print(f"[{folder}] ❌ Failed to log into Spotify via Google after {max_page_load_attempts} attempts. Cannot proceed with Spotify for this profile.")
                        continue # Move to next overall attempt

                # Logic for Profiles 5-8: Facebook Login ONLY
                elif facebook_password: # This now applies specifically to Profiles 5-8 based on their configuration
                    print(f"[{folder}] Attempting to log in via Facebook.")
                    facebook_login_successful_this_try = False
                    for fb_try in range(max_page_load_attempts):
                        if try_click(driver, 'button[data-testid="facebook-login"]', label="Continue with Facebook Button"):
                            time.sleep(5)
                            # Handle potential Facebook permission pop-up if it's the first time
                            try_click(driver, 'div[role="button"][aria-label^="Continue as"]', label="Continue as (Facebook)")
                            time.sleep(5)
                            if is_spotify_logged_in(driver):
                                print(f"[{folder}] ✅ Successfully logged into Spotify via Facebook.")
                                facebook_login_successful_this_try = True
                                break # Exit fb_try loop
                            else:
                                print(f"[{folder}] ❌ Spotify login via Facebook failed or did not complete after re-check (attempt {fb_try + 1}). Current URL: {driver.current_url}. Refreshing to retry.")
                                driver.save_screenshot(f"debug_spotify_facebook_login_failed_{folder}_{int(time.time())}_try{fb_try}.png") # Screenshot on failure
                                driver.refresh()
                                time.sleep(5)
                        else:
                            print(f"[{folder}] ❌ 'Continue with Facebook' button not found on login page (attempt {fb_try + 1}). Refreshing to retry.")
                            driver.refresh()
                            time.sleep(5)
                    
                    if not facebook_login_successful_this_try:
                        print(f"[{folder}] ❌ Failed to log into Spotify via Facebook after {max_page_load_attempts} attempts. Cannot proceed with Spotify for this profile.")
                        continue # Move to next overall attempt

                else: # Fallback if neither Google (for P1) nor Facebook (for P5-8) login initiated successfully
                    print(f"[{folder}] ❌ No specific login method (Google for Profile 1 or Facebook for others) was successfully initiated for Spotify. Current URL: {driver.current_url}. Retrying overall attempt.")
                    driver.save_screenshot(f"debug_spotify_login_method_missing_{folder}_{int(time.time())}.png")
                    continue # Move to the next overall playback attempt
            else: # Already logged in
                print("✅ Already logged into Spotify. Proceeding with playlist search.")
            
            # Now, ensure we are on the playlist URL after login or if already logged in
            driver.get(SPOTIFY_PLAYLIST_URL)
            time.sleep(5)

            # --- Spotify Playback ---
            search_found = False
            for refresh_attempt in range(3):
                try:
                    time.sleep(3)
                    library_button = driver.find_elements(By.XPATH, '//button[@aria-label="Open Your Library"]')
                    if library_button and library_button[0].is_displayed():
                        print(f"📂 'Your Library' is collapsed — clicking (attempt {refresh_attempt + 1})...")
                        click_with_retries(driver, library_button[0])
                        time.sleep(2)
                    else:
                        print(f"📂 'Your Library' already open or not found (attempt {refresh_attempt + 1}).")

                    search = WebDriverWait(driver, 10).until(EC.presence_of_element_located(
                        (By.CSS_SELECTOR, 'div[role="search"] input[role="searchbox"]')))
                    search.clear()
                    search.send_keys(playlist_name)
                    print(f"🔎 Searching playlist: '{playlist_name}' (attempt {refresh_attempt + 1})...")
                    time.sleep(2)
                    search_found = True
                    break
                except Exception as e:
                    print(f"🔄 Search input or library not ready (attempt {refresh_attempt + 1}) — refreshing. Error: {e}")
                    driver.refresh()
                    time.sleep(5)

            if not search_found:
                print("❌ Search input failed after 3 refresh attempts. Skipping playback attempt for this profile.")
                continue # Move to next overall attempt

            playback_attempt_successful = False
            for dbl in range(2): # Try double-clicking playlist up to 2 times
                try:
                    sidebar_btn = WebDriverWait(driver, 12).until(EC.element_to_be_clickable(
                        (By.CSS_SELECTOR, f'div[role="button"][aria-labelledby^="listrow-title-{playlist_uri}"]')))
                    driver.execute_script("arguments[0].scrollIntoView({behavior:'smooth',block:'center'});", sidebar_btn)
                    ActionChains(driver).double_click(sidebar_btn).perform()
                    print(f"🖱️ Double-clicked playlist (attempt {dbl + 1})")
                    time.sleep(4)

                    WebDriverWait(driver, 12).until(EC.presence_of_element_located(
                        (By.CSS_SELECTOR, 'button[data-testid="control-button-playpause"][aria-label="Pause"]')))
                    print("✅ Playback confirmed.")
                    playback_attempt_successful = True
                    break
                except Exception as e:
                    print(f"⏱️ Playback not confirmed after double-click {dbl + 1}. Error: {e}")
                    print(f"    Details: {e}")
                    if dbl < 1: # Only refresh if not the last attempt
                        print("🔄 Refreshing page before next playback attempt...")
                        driver.refresh()
                        time.sleep(5)
                    playback_attempt_successful = False
                    time.sleep(2)

            if not playback_attempt_successful:
                print(f"[{folder}] ❌ Playback failed after all attempts. Moving to next overall attempt.")
                continue # Move to the next overall playback attempt

            # --- Shuffle and Repeat buttons ---
            print(f"[{folder}] Attempting to enable shuffle and repeat...")
            # Click Shuffle button
            if try_click(driver, 'button[data-testid="control-button-shuffle"][aria-checked="false"]', label="Shuffle button"):
                print(f"[{folder}] ✅ Shuffle enabled.")
            else:
                print(f"[{folder}] ⚠️ Shuffle button not found or already enabled/not clickable.")
            time.sleep(1) # Small delay

            # Click Repeat button
            if try_click(driver, 'button[data-testid="control-button-repeat"][aria-checked="false"]', label="Repeat button"):
                print(f"[{folder}] ✅ Repeat enabled.")
            else:
                print(f"[{folder}] ⚠️ Repeat button not found or already enabled/not clickable.")
            time.sleep(2) # Small delay after trying repeat

            # --- NAS Submit Block ---
            summary[folder] = "✅ Success" # Assume success up to this point, NAS is final step.
            print("🌐 NAS Submit...")

            driver.execute_script(f"window.open('{nas_login_url}', '_blank');")
            print(f"[{folder}] Waiting for new NAS tab to open (expected window count: {initial_window_count + 1})...")
            WebDriverWait(driver, 20).until(EC.number_of_windows_to_be(initial_window_count + 1))
            driver.switch_to.window(driver.window_handles[-1])
            print(f"[{folder}] ✅ Switched to new NAS tab: {driver.current_url}")
            time.sleep(5)

            nas_success = False
            for nas_attempt in range(1, 4):
                print(f"[{folder}] NAS operation attempt {nas_attempt}/3...")
                try:
                    print(f"[{folder}] -> Attempting to trigger 'onAutoSubmitButtonPressed()' via JavaScript...")
                    triggered_auto_submit = False
                    try:
                        auto_submit_btn_present = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, "autoSubmitButton")))
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
                            WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.XPATH, "//*[contains(text(), 'Submitting...')]")))
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
                        print(f"[{folder}] -> Direct 'Auto Submit' trigger failed. Trying 'Login' button...")
                        if try_click(driver, 'a#loginButton.btn.btn-primary', label="NAS Login Initiator"):
                            print(f"[{folder}] ✅ NAS 'Login' button clicked. Waiting for login process (10s)...")
                            time.sleep(10)

                            print(f"[{folder}] -> Trying to trigger 'onAutoSubmitButtonPressed()' again after Login...")
                            triggered_auto_submit_after_login = False
                            try:
                                auto_submit_btn_present = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, "autoSubmitButton")))
                                driver.execute_script("arguments[0].scrollIntoView({behavior: 'auto', block: 'center'});", auto_submit_btn_present)
                                driver.execute_script("onAutoSubmitButtonPressed();")
                                print(f"[{folder}] -> JavaScript function 'onAutoSubmitButtonPressed()' executed after Login.")
                                triggered_auto_submit_after_login = True
                            except TimeoutException:
                                print(f"[{folder}] -> 'autoSubmitButton' element not found after Login for direct JS execution within timeout.")
                            except Exception as e:
                                print(f"[{folder}] -> Error executing 'onAutoSubmitButtonPressed()' after Login: {e}")

                            if triggered_auto_submit_after_login:
                                print(f"[{folder}] -> Checking for 'Submitting...' text after second 'Auto Submit' trigger...")
                                try:
                                    WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.XPATH, "//*[contains(text(), 'Submitting...')]")))
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
                        else:
                            print(f"[{folder}] ❌ NAS 'Login' button not found/clickable. Refreshing page for next attempt.")
                            driver.refresh()
                            time.sleep(5)
                            continue

                except Exception as e:
                    print(f"[{folder}] ❌ An unexpected general error occurred during NAS operations: {e}. Refreshing page for next attempt.")
                    driver.refresh()
                    time.sleep(5)

            if nas_success:
                print(f"[{folder}] ✅ NAS operations completed successfully.")
            else:
                print(f"[{folder}] ❌ NAS operations failed after all {nas_attempt} attempts.")
            
            print(f"[{folder}] ⚠️ NAS tab left open for manual inspection: {driver.current_url}")
            break # Exit the Spotify attempt loop if playback and NAS were successful

        # This block is only reached if the overall 'attempt' loop for Spotify/playback did NOT break early
        if not play_success: # If the entire Spotify login/playback process failed after all attempts
            print(f"🚫 All Spotify login and playback attempts failed for {folder}. Moving to next profile.")

        print(f"✅ {folder} finished. Brave browser for this profile remains open.\n{'-'*60}")

    except WebDriverException as e:
        print(f"❌ Cannot launch {folder} — profile may be in use or corrupted. Error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error in {folder}: {e}")
        if driver and driver not in active_drivers:
            active_drivers.append(driver)


# === FINAL CLEANUP (after all profiles are processed) ===
print("\n=== ✅ All Profiles Processed ===")
print("All Brave browser windows will remain open until you press Enter.")
input("Press Enter to close all opened Brave browser windows and exit the script...\n")

for driver_instance in active_drivers:
    try:
        driver_instance.quit()
        print(f"✅ Closed a Brave browser instance.")
    except Exception as e:
        print(f"❌ Error closing a Brave browser instance: {e}")

# === SUMMARY ===
print("\n=== ✅ Final Summary ===")
for profile in profiles:
    status = summary.get(profile["folder"], "N/A - Not Processed")
    print(f"{profile['folder']}: {status}")