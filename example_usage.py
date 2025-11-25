#!/usr/bin/env python3
"""
Example usage of the Quora Profile Scraper

This script demonstrates how to:
1. Scrape a Quora profile
2. Clean and post-process the results
"""

import subprocess
import sys
from pathlib import Path


def scrape_profile(user_id, output_dir='./output'):
    """
    Scrape a Quora profile using the ultimate scraper

    Args:
        user_id: Quora user ID (e.g., 'John-Smith-123')
        output_dir: Directory to save raw output
    """
    print(f"\n{'='*80}")
    print(f"STEP 1: SCRAPING PROFILE '{user_id}'")
    print(f"{'='*80}\n")

    cmd = [
        sys.executable, '-m', 'quora_scraper.scraper_ultimate',
        user_id,
        '-o', output_dir
    ]

    result = subprocess.run(cmd, capture_output=False)

    if result.returncode != 0:
        print(f"❌ Scraping failed with exit code {result.returncode}")
        return None

    # Return path to output file
    return Path(output_dir) / f"{user_id}_ultimate.json"


def clean_results(input_file, output_dir='./cleaned_output'):
    """
    Clean and post-process the scraped results

    Args:
        input_file: Path to raw JSON file
        output_dir: Directory to save cleaned output
    """
    print(f"\n{'='*80}")
    print(f"STEP 2: CLEANING RESULTS")
    print(f"{'='*80}\n")

    cmd = [
        sys.executable, 'clean_answers.py',
        str(input_file),
        '-o', output_dir
    ]

    result = subprocess.run(cmd, capture_output=False)

    if result.returncode != 0:
        print(f"❌ Cleaning failed with exit code {result.returncode}")
        return None

    # Return path to cleaned file
    user_id = input_file.stem.replace('_ultimate', '')
    return Path(output_dir) / f"{user_id}_cleaned.json"


def main():
    """Main workflow example"""

    # Get user ID from command line or use default
    if len(sys.argv) > 1:
        user_id = sys.argv[1]
    else:
        print("Usage: python example_usage.py <user-id>")
        print("\nExample:")
        print("  python example_usage.py John-Smith-123")
        print("\nProceeding with example user ID for demonstration...")
        user_id = "example-user"
        print(f"⚠️  Please replace '{user_id}' with an actual Quora user ID")
        return

    print(f"\n{'='*80}")
    print(f"QUORA PROFILE SCRAPER - COMPLETE WORKFLOW")
    print(f"{'='*80}")
    print(f"Target: {user_id}")
    print(f"{'='*80}\n")

    # Step 1: Scrape
    raw_output = scrape_profile(user_id, output_dir='./raw_output')

    if raw_output is None:
        print("\n❌ Workflow stopped: Scraping failed")
        return 1

    print(f"\n✅ Raw data saved to: {raw_output}")

    # Step 2: Clean
    cleaned_output = clean_results(raw_output, output_dir='./final_output')

    if cleaned_output is None:
        print("\n❌ Workflow stopped: Cleaning failed")
        return 1

    print(f"\n✅ Cleaned data saved to: {cleaned_output}")

    print(f"\n{'='*80}")
    print("✅ WORKFLOW COMPLETED SUCCESSFULLY!")
    print(f"{'='*80}")
    print(f"\nFinal output: {cleaned_output}")
    print(f"View results: cat {cleaned_output.with_suffix('.txt')}")
    print(f"{'='*80}\n")

    return 0


if __name__ == '__main__':
    exit(main())
