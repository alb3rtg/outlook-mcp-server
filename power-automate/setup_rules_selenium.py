#!/usr/bin/env python3
"""
Automate Outlook Rules setup using Selenium
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

def setup_outlook_rules():
    print("=" * 60)
    print("OUTLOOK RULES SETUP VIA BROWSER AUTOMATION")
    print("=" * 60)

    # Setup Chrome with existing profile to use logged-in session
    chrome_options = Options()
    chrome_options.add_argument("--user-data-dir=/Users/albert.greenberg/Library/Application Support/Google/Chrome")
    chrome_options.add_argument("--profile-directory=Default")
    # Don't run headless so user can see what's happening
    # chrome_options.add_argument("--headless")

    print("\n🌐 Starting Chrome with your existing profile...")
    print("   (This will use your logged-in Outlook session)")

    try:
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )
    except Exception as e:
        print(f"   ❌ Error starting Chrome: {e}")
        print("   Trying without profile...")
        chrome_options = Options()
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )

    wait = WebDriverWait(driver, 20)

    try:
        # Step 1: Go to Outlook Rules page
        print("\n📧 Opening Outlook Rules settings...")
        driver.get("https://outlook.live.com/mail/0/options/mail/rules")
        time.sleep(3)

        # Check if we need to log in
        if "login" in driver.current_url.lower() or "signin" in driver.current_url.lower():
            print("\n⚠️ Please log in to your Outlook account in the browser window...")
            print("   Waiting for login to complete...")
            # Wait for redirect back to outlook
            wait.until(lambda d: "outlook.live.com/mail" in d.current_url)
            print("   ✅ Login detected, continuing...")
            driver.get("https://outlook.live.com/mail/0/options/mail/rules")
            time.sleep(3)

        # Step 2: Click "Add new rule" button
        print("\n📋 Looking for 'Add new rule' button...")
        try:
            add_button = wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//button[contains(., 'Add new rule') or contains(., 'Add rule')]")
            ))
            add_button.click()
            print("   ✅ Clicked 'Add new rule'")
            time.sleep(2)
        except Exception as e:
            print(f"   ⚠️ Could not find Add button: {e}")
            # Try alternative selector
            try:
                add_button = driver.find_element(By.CSS_SELECTOR, "[data-testid='add-rule-button']")
                add_button.click()
                print("   ✅ Clicked Add button (alternate)")
            except:
                print("   ❌ Could not click Add Rule button")

        # Step 3: Fill in rule name
        print("\n📝 Filling in rule details...")
        try:
            name_input = wait.until(EC.presence_of_element_located(
                (By.XPATH, "//input[@placeholder='Name your rule' or @aria-label='Name']")
            ))
            name_input.clear()
            name_input.send_keys("Move Promotional Emails")
            print("   ✅ Set rule name: 'Move Promotional Emails'")
        except Exception as e:
            print(f"   ⚠️ Could not find name input: {e}")

        # Step 4: Add condition - body contains "unsubscribe"
        print("\n🔍 Setting up condition...")
        try:
            # Click add condition
            add_condition = wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//button[contains(., 'Add a condition') or contains(., 'Add condition')]")
            ))
            add_condition.click()
            time.sleep(1)

            # Select "Body includes"
            body_option = wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//div[contains(., 'Body includes') or contains(., 'body includes')]")
            ))
            body_option.click()
            time.sleep(1)

            # Enter keywords
            keyword_input = wait.until(EC.presence_of_element_located(
                (By.XPATH, "//input[@placeholder='Enter words' or contains(@aria-label, 'words')]")
            ))
            keyword_input.send_keys("unsubscribe")
            print("   ✅ Added condition: body contains 'unsubscribe'")
        except Exception as e:
            print(f"   ⚠️ Could not set condition: {e}")

        # Step 5: Add action - Move to folder
        print("\n📁 Setting up action...")
        try:
            add_action = wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//button[contains(., 'Add an action') or contains(., 'Add action')]")
            ))
            add_action.click()
            time.sleep(1)

            # Select "Move to"
            move_option = wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//div[contains(., 'Move to') or contains(., 'move to')]")
            ))
            move_option.click()
            time.sleep(1)
            print("   ✅ Selected 'Move to' action")
        except Exception as e:
            print(f"   ⚠️ Could not set action: {e}")

        # Step 6: Save rule
        print("\n💾 Saving rule...")
        try:
            save_button = wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//button[contains(., 'Save') or @data-testid='save-button']")
            ))
            # Don't click save yet - let user review
            print("   ⏸️ Rule configured - please review and click Save in the browser")
        except Exception as e:
            print(f"   ⚠️ Could not find save button: {e}")

        print("\n" + "=" * 60)
        print("AUTOMATION PAUSED")
        print("=" * 60)
        print("""
Please complete the setup in the browser:

1. Review the rule configuration
2. For 'Move to' action, select/create folder 'Promotional-ToDelete'
3. Click 'Save' to create the rule

The browser will stay open for you to complete and verify.
Press Enter here when done...
""")
        input()

    except Exception as e:
        print(f"\n❌ Error during automation: {e}")
        print("The browser is open - you can complete setup manually.")
        print("Press Enter to close...")
        input()

    finally:
        print("\n👋 Closing browser...")
        driver.quit()

if __name__ == '__main__':
    setup_outlook_rules()
