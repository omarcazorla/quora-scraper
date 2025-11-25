#!/usr/bin/env python3
"""
Quora Scraper Ultimate - Versión mejorada para obtener respuestas completas
Enfoque: Expandir botones (more) de manera más efectiva y extraer contenido completo
"""
import time
import json
import logging
import argparse
import re
from pathlib import Path
from datetime import datetime
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, ElementClickInterceptedException

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def setup_driver():
    """Initialize Chrome WebDriver with stealth settings."""
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')

    driver = webdriver.Chrome(options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    driver.maximize_window()
    logger.info("Chrome WebDriver initialized")
    return driver


def wait_for_cloudflare(driver, max_wait=45):
    """Wait for Cloudflare challenge to complete."""
    logger.info("Checking for Cloudflare...")
    start_time = time.time()

    while (time.time() - start_time) < max_wait:
        title = driver.title.lower()
        if "just a moment" not in title and "cloudflare" not in title:
            logger.info("✅ Cloudflare passed")
            return True
        time.sleep(2)

    logger.warning(f"Cloudflare timeout after {max_wait}s")
    return False


def scroll_and_load_all(driver, max_scrolls=200):
    """Scroll to load all content with progress tracking."""
    logger.info("📜 Scrolling to load all content...")
    last_height = driver.execute_script("return document.body.scrollHeight")
    no_change_count = 0
    scroll_count = 0

    while no_change_count < 5 and scroll_count < max_scrolls:
        # Scroll to bottom
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

        # Check if we loaded more content
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            no_change_count += 1
        else:
            no_change_count = 0
            last_height = new_height

        scroll_count += 1
        if scroll_count % 20 == 0:
            logger.info(f"   Scrolled {scroll_count} times...")

    logger.info(f"✅ Scrolling completed: {scroll_count} scrolls")
    return scroll_count


def expand_truncated_answers_v2(driver):
    """
    Improved version to expand truncated answers.
    Uses multiple strategies to click (more) buttons.
    """
    logger.info("🔍 Searching for truncated answers...")

    # Strategy 1: Find all elements containing "(more)"
    more_selectors = [
        "//span[contains(text(), '(more)')]",
        "//div[contains(text(), '(more)')]",
        "//a[contains(text(), '(more)')]",
        "//*[contains(text(), '(more)')]"
    ]

    all_more_buttons = []
    for selector in more_selectors:
        try:
            buttons = driver.find_elements(By.XPATH, selector)
            all_more_buttons.extend(buttons)
        except:
            pass

    # Remove duplicates
    unique_buttons = list(set(all_more_buttons))
    logger.info(f"Found {len(unique_buttons)} '(more)' indicators")

    expanded_count = 0
    failed_count = 0

    for i, button in enumerate(unique_buttons):
        try:
            # Get the parent clickable element
            parent = button.find_element(By.XPATH, "..")

            # Scroll into view
            driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", parent)
            time.sleep(0.3)

            # Try multiple click methods
            try:
                # Method 1: Regular click
                parent.click()
                expanded_count += 1
            except ElementClickInterceptedException:
                try:
                    # Method 2: JavaScript click
                    driver.execute_script("arguments[0].click();", parent)
                    expanded_count += 1
                except:
                    # Method 3: Click on the button itself
                    try:
                        driver.execute_script("arguments[0].click();", button)
                        expanded_count += 1
                    except:
                        failed_count += 1

            # Small delay between clicks
            if i % 10 == 0 and i > 0:
                logger.info(f"   Expanded {expanded_count}/{i} so far...")
                time.sleep(0.5)

        except Exception as e:
            failed_count += 1
            continue

    logger.info(f"✅ Expansion complete: {expanded_count} expanded, {failed_count} failed")
    time.sleep(2)
    return expanded_count


def extract_answers_improved(driver):
    """
    Extract answers using improved parsing strategy.
    Looks for answer blocks and extracts complete text.
    """
    logger.info("📊 Extracting answers from page...")

    # Get page source and parse with BeautifulSoup
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')

    answers = []

    # Strategy: Find all answer containers
    # Quora answers are typically in divs with specific structure
    # Look for patterns like: question text followed by answer text

    # Find all text blocks
    text_blocks = soup.find_all(['div', 'span'], class_=True)

    # Build a list of all text elements with their hierarchy
    all_text = []
    for elem in text_blocks:
        text = elem.get_text(strip=True)
        if len(text) > 20:  # Only consider substantial text
            all_text.append(text)

    logger.info(f"Found {len(all_text)} text blocks")

    # Pattern matching: Look for Q&A pairs
    # Questions usually end with "?" or are followed by date/credential info
    question_pattern = re.compile(r'.{20,}[?]')

    i = 0
    while i < len(all_text) - 1:
        text = all_text[i]

        # Check if this looks like a question
        if question_pattern.match(text) or '?' in text:
            question = text

            # Next few elements might be date, credential, answer
            potential_answer_idx = i + 1

            # Skip metadata (dates, credentials)
            while potential_answer_idx < len(all_text):
                potential = all_text[potential_answer_idx]

                # Skip short metadata
                if len(potential) < 30:
                    potential_answer_idx += 1
                    continue

                # Skip if it looks like another question
                if '?' in potential[-20:]:
                    break

                # This looks like an answer
                if len(potential) > 50:
                    # Check that it's not ending with "(more)" which means still truncated
                    if not potential.endswith('...') and not '(more)' in potential[-20:]:
                        answers.append({
                            'question': question,
                            'answer': potential,
                            'extracted_at': datetime.now().isoformat()
                        })
                        logger.info(f"   ✓ Extracted answer {len(answers)}")
                    break

                potential_answer_idx += 1

            i = potential_answer_idx

        i += 1

    logger.info(f"✅ Total answers extracted: {len(answers)}")
    return answers


def scrape_profile_ultimate(user_id, output_dir):
    """
    Ultimate scraper with improved expansion and extraction.
    """
    driver = setup_driver()
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    try:
        url = f"https://www.quora.com/profile/{user_id}"
        logger.info(f"🎯 Target: {url}")

        # Load page
        driver.get(url)
        time.sleep(5)

        # Wait for Cloudflare
        if not wait_for_cloudflare(driver):
            logger.error("❌ Failed to bypass Cloudflare")
            return False

        time.sleep(3)

        # Get profile stats
        body_text = driver.find_element(By.TAG_NAME, "body").text
        nb_answers = re.search(r'(\d+)\s+Answers', body_text)
        nb_answers = nb_answers.group(1) if nb_answers else "0"

        logger.info(f"📊 Profile has {nb_answers} answers")

        # Scroll to load all content
        scrolls = scroll_and_load_all(driver)

        # Expand truncated answers
        expanded = expand_truncated_answers_v2(driver)

        # Extract answers
        answers = extract_answers_improved(driver)

        # Save results
        result = {
            'profile': {
                'user_id': user_id,
                'url': url,
                'nb_answers_claimed': nb_answers,
                'scraped_at': datetime.now().isoformat()
            },
            'scraping_stats': {
                'scrolls_performed': scrolls,
                'expansions_attempted': expanded,
                'answers_extracted': len(answers)
            },
            'answers': answers
        }

        # Save JSON
        json_file = output_path / f"{user_id}_ultimate.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        logger.info(f"💾 JSON: {json_file}")

        # Save TXT
        txt_file = output_path / f"{user_id}_ultimate.txt"
        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write(f"QUORA PROFILE: {user_id}\n")
            f.write(f"{'=' * 100}\n\n")
            f.write(f"URL: {url}\n")
            f.write(f"Claimed answers: {nb_answers}\n")
            f.write(f"Extracted answers: {len(answers)}\n")
            f.write(f"Extraction rate: {len(answers)}/{nb_answers}\n")
            f.write(f"\n{'=' * 100}\n\n")

            for i, ans in enumerate(answers, 1):
                f.write(f"\n{'=' * 100}\n")
                f.write(f"ANSWER #{i}\n")
                f.write(f"{'=' * 100}\n")
                f.write(f"\n❓ QUESTION:\n{ans['question']}\n")
                f.write(f"\n💬 ANSWER:\n{ans['answer']}\n")

        logger.info(f"💾 TXT: {txt_file}")

        # Summary
        logger.info("=" * 80)
        logger.info("✅ SCRAPING COMPLETED!")
        logger.info("=" * 80)
        logger.info(f"Extracted: {len(answers)}/{nb_answers} answers")
        logger.info(f"Success rate: {len(answers)/max(int(nb_answers),1)*100:.1f}%")

        return True

    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        driver.quit()


def main():
    parser = argparse.ArgumentParser(description='Ultimate Quora Profile Scraper')
    parser.add_argument('user_id', help='Quora user ID (e.g., Bob-French-11)')
    parser.add_argument('-o', '--output', default='./output_ultimate',
                       help='Output directory')
    args = parser.parse_args()

    logger.info("=" * 80)
    logger.info("QUORA SCRAPER ULTIMATE")
    logger.info("=" * 80)

    success = scrape_profile_ultimate(args.user_id, args.output)
    return 0 if success else 1


if __name__ == '__main__':
    exit(main())
