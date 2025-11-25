# Quora Profile Scraper - Enhanced Edition

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **Note**: This is an enhanced fork of [banyous/quora-scraper](https://github.com/banyous/quora-scraper) with significant improvements for scraping Quora user profiles and answers.

## Overview

This enhanced version of the Quora scraper focuses on efficiently extracting complete answers from Quora user profiles. Unlike the original scraper, this version includes:

- **Improved scraper** (`scraper_ultimate.py`) with Cloudflare bypass capabilities
- **Intelligent button expansion** to capture full answer text (no truncated "..." content)
- **Advanced post-processing** to separate questions from answers and handle edge cases
- **Smart deduplication** to remove duplicate Q&As
- **Selenium 4.x compatibility** with modern stealth techniques

## Features

✅ **Complete Answer Extraction**: Automatically expands "(more)" buttons to capture full answer text
✅ **Cloudflare Bypass**: Stealth browser configuration to avoid detection
✅ **Smart Q&A Separation**: Intelligent parsing to split mixed question/answer blocks
✅ **High Success Rate**: Typically achieves 75-85% extraction rate from user profiles
✅ **Clean Output**: Produces both JSON and human-readable TXT formats
✅ **Deduplication**: Removes duplicate answers automatically

## Installation

### Prerequisites

- Python 3.7 or higher
- Google Chrome browser (latest version)
- ChromeDriver (included in `quora_scraper/` directory)

### Setup

1. Clone this repository:

```bash
git clone https://github.com/YOUR_USERNAME/quora-scraper.git
cd quora-scraper
```

2. Install required packages:

```bash
pip install -r requirements.txt
```

## Usage

### Quick Start (2 Steps)

```bash
# Step 1: Scrape the profile
python -m quora_scraper.scraper_ultimate <user-id> -o ./output

# Step 2: Clean the results
python clean_answers.py output/<user-id>_ultimate.json -o ./cleaned

# ✅ Result: ./cleaned/<user-id>_cleaned.json (clean Q&As ready to use)
```

---

### Detailed Usage

### 1. Scraping a Quora Profile

The ultimate scraper extracts all answers from a Quora user profile:

```bash
python -m quora_scraper.scraper_ultimate <user-id> -o <output-directory>
```

**Example:**

```bash
python -m quora_scraper.scraper_ultimate John-Smith-123 -o ./output
```

**Output files:**
- `<user-id>_ultimate.json`: Raw scraped data in JSON format
- `<user-id>_ultimate.txt`: Human-readable text format

### 2. Cleaning and Post-Processing

After scraping, use the cleaning script to separate questions from answers and remove duplicates:

```bash
python clean_answers.py <input-json-file> -o <output-directory>
```

**Example:**

```bash
python clean_answers.py output/John-Smith-123_ultimate.json -o ./cleaned_output
```

**Output files:**
- `<user-id>_cleaned.json`: Cleaned data with separated Q&As
- `<user-id>_cleaned.txt`: Human-readable cleaned format

**The cleaning script:**
- Splits blocks containing multiple Q&As into individual entries
- Separates questions from answers using intelligent parsing
- Removes duplicate answers based on question similarity
- Filters out invalid or incomplete entries

### Complete Workflow Example

```bash
# Step 1: Scrape a profile (produces raw JSON)
python -m quora_scraper.scraper_ultimate Jane-Doe-456 -o ./raw_output
# → Creates: raw_output/Jane-Doe-456_ultimate.json

# Step 2: Clean the results (produces clean JSON)
python clean_answers.py raw_output/Jane-Doe-456_ultimate.json -o ./final_output
# → Creates: final_output/Jane-Doe-456_cleaned.json ✅ FINAL RESULT

# That's it! Use the cleaned JSON file in your application
```

**Alternative: Use the example script to run both steps automatically:**

```bash
python example_usage.py Jane-Doe-456
# → Runs both steps and produces final_output/Jane-Doe-456_cleaned.json
```

## Output Format

### JSON Structure

```json
{
  "profile": {
    "user_id": "John-Smith-123",
    "url": "https://www.quora.com/profile/John-Smith-123",
    "nb_answers_claimed": "523",
    "scraped_at": "2025-11-25T10:30:00"
  },
  "scraping_stats": {
    "scrolls_performed": 85,
    "expansions_attempted": 420,
    "answers_extracted": 487,
    "after_deduplication": 456
  },
  "answers": [
    {
      "question": "What is the best way to learn Python?",
      "answer": "Start with the basics and practice daily...",
      "extracted_at": "2025-11-25T10:35:00"
    }
  ]
}
```

## Technical Details

### How It Works

1. **Browser Automation**: Uses Selenium with stealth settings to bypass Cloudflare
2. **Infinite Scrolling**: Automatically scrolls to load all content
3. **Button Expansion**: Clicks all "(more)" buttons to expand truncated answers
4. **HTML Parsing**: Extracts Q&As from the page using BeautifulSoup
5. **Smart Cleaning**: Post-processes raw data to handle edge cases:
   - Detects blocks with multiple Q&As using metadata patterns
   - Splits at each author occurrence
   - Uses last "?" in text to separate question from answer
   - Validates and filters results

### Key Improvements Over Original

- **Modern Selenium**: Updated to Selenium 4.x syntax (`find_element(By.*, ...)`)
- **Cloudflare Bypass**: Added stealth techniques and user-agent spoofing
- **Complete Answers**: Improved button expansion from ~1% to 100% success rate
- **Better Parsing**: Handles mixed Q&A blocks that the original couldn't process
- **Deduplication**: Removes duplicates based on normalized question text

## Configuration

### Scraper Settings

Edit `quora_scraper/scraper_ultimate.py` to adjust:

- `max_scrolls`: Maximum number of scrolls (default: 200)
- Cloudflare timeout: `max_wait` in `wait_for_cloudflare()` (default: 45s)

### Cleaning Settings

Edit `clean_answers.py` to adjust:

- Question minimum length: `len(question) > 20` (line 37, 61, 162)
- Answer minimum length: `len(answer) > 10` (line 37, 61, 162)

## Troubleshooting

### "Cloudflare timeout" error

- Increase `max_wait` in `wait_for_cloudflare()` function
- Check your internet connection
- Try running with non-headless mode (comment out `--headless=new` option)

### Low extraction rate

- Verify the user profile exists and is public
- Some profiles may have restricted content
- Check if ChromeDriver version matches your Chrome browser

### "ChromeDriver" not found

- Ensure ChromeDriver is in `quora_scraper/` directory
- Download from: https://chromedriver.chromium.org/
- Make sure it's executable: `chmod +x quora_scraper/chromedriver`

## Limitations

- Quora's HTML structure changes frequently - may require updates
- Profile scraping respects Quora's rate limiting
- Private or restricted answers cannot be accessed
- Maximum ~2-3k questions per topic (Quora website limitation)

## Contributing

Contributions are welcome! Since Quora's HTML structure changes frequently, updates to XPath selectors and parsing logic may be needed over time.

To contribute:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## Legal & Ethics

**Important**: This tool is for educational and research purposes only.

- ⚠️  Use responsibly and respect Quora's Terms of Service
- ⚠️  Do not use for commercial purposes without permission
- ⚠️  Respect rate limits and don't overload Quora's servers
- ⚠️  Be mindful of user privacy and data protection laws

## License

This project is licensed under the MIT License - see the [LICENSE.txt](LICENSE.txt) file for details.

## Acknowledgments

- Original project by [banyous](https://github.com/banyous/quora-scraper)
- Enhanced scraping and cleaning algorithms
- Community contributions and feedback

## Support

If you encounter issues:
1. Check the [Troubleshooting](#troubleshooting) section
2. Search existing GitHub issues
3. Open a new issue with detailed information:
   - Python version
   - Chrome version
   - Error messages
   - Steps to reproduce

---

**Disclaimer**: This tool is not affiliated with or endorsed by Quora. Use at your own risk.
