#!/usr/bin/env python3
"""
Clean and deduplicate answers from the ultimate scraper output
Properly separate questions from answers
"""
import json
import re
from pathlib import Path
from datetime import datetime


def clean_answer_block(text, author_pattern=None):
    """
    Clean a single answer block to separate question from answer.

    Pattern: Author Name + Credential + · + Date + · + QUESTION + ANSWER

    Args:
        text: Raw text block to clean
        author_pattern: Optional regex pattern to match author metadata.
                       If None, uses a generic pattern that matches most Quora authors.
    """
    # Remove leading navigation/UI text
    text = re.sub(r'^Skip to content.*?Most recent', '', text, flags=re.DOTALL)
    text = re.sub(r'^\d+ followers.*?More', '', text)

    # Generic pattern for Quora author metadata: Name + Credential + Date
    # Matches patterns like: "John Smith [credentials]·[date]·"
    # This works for most Quora answer formats regardless of author name
    if author_pattern is None:
        # Generic pattern: looks for [text]·[date]· structure
        # where date can be "5y", "3mo", "Jan 15", etc.
        author_pattern = r'[A-Z][^·]{5,50}·(?:\d+[ymo]|[A-Z][a-z]{2} \d+)·?'

    # Find all occurrences
    matches = list(re.finditer(author_pattern, text, re.IGNORECASE))

    if not matches:
        # No author metadata found, use last question mark strategy
        last_q_pos = text.rfind('?')
        if last_q_pos != -1:
            question = text[:last_q_pos + 1].strip()
            answer = text[last_q_pos + 1:].strip()

            # Lowered answer threshold to 10 chars to capture concise but valid answers
            if question != answer and len(question) > 20 and len(answer) > 10:
                return question, answer

        return None, None

    # Strategy: Find the LAST occurrence of author metadata before a question
    # The text after that is the actual Q&A content
    last_match = matches[-1]
    content_after_metadata = text[last_match.end():].strip()

    # Find the LAST question mark - everything before is question, after is answer
    # This handles cases where there are multiple questions in the question text
    last_question_mark_pos = content_after_metadata.rfind('?')

    if last_question_mark_pos != -1:
        # Everything up to and including the last ? is the question
        question = content_after_metadata[:last_question_mark_pos + 1].strip()
        # Everything after the last ? is the answer
        answer = content_after_metadata[last_question_mark_pos + 1:].strip()

        # Remove any remaining author metadata patterns from answer
        answer = re.sub(author_pattern, '', answer, flags=re.IGNORECASE).strip()

        # Validate: question and answer should be different and substantial
        # Lowered answer threshold to 10 chars to capture concise but valid answers
        if question != answer and len(question) > 20 and len(answer) > 10:
            return question, answer

    return None, None


def deduplicate_answers(answers):
    """
    Remove duplicate answers based on question similarity.
    """
    seen_questions = set()
    unique_answers = []

    for ans in answers:
        question = ans.get('question', '')

        # Create a normalized version for comparison
        normalized = re.sub(r'\s+', ' ', question.lower().strip())

        # Only keep if we haven't seen this question before
        if normalized not in seen_questions and len(normalized) > 20:
            seen_questions.add(normalized)
            unique_answers.append(ans)

    return unique_answers


def split_multiple_qa_blocks(text, author_pattern=None):
    """
    Split text containing multiple Q&A blocks into individual blocks.
    Detects multiple author metadata patterns and splits at each occurrence.

    Args:
        text: Raw text potentially containing multiple Q&As
        author_pattern: Optional regex pattern to match author metadata.
                       If None, uses generic pattern.

    Returns:
        List of text blocks, each containing a single Q&A
    """
    # Generic pattern for Quora author metadata
    if author_pattern is None:
        author_pattern = r'[A-Z][^·]{5,50}·(?:\d+[ymo]|[A-Z][a-z]{2} \d+)·?'

    # Find all author metadata occurrences
    matches = list(re.finditer(author_pattern, text, re.IGNORECASE))

    # If only 0 or 1 match, return as single block
    if len(matches) <= 1:
        return [text]

    # Split at each author metadata occurrence
    blocks = []
    for i, match in enumerate(matches):
        # Start from this match
        start_pos = match.start()

        # End at next match (or end of text)
        if i + 1 < len(matches):
            end_pos = matches[i + 1].start()
        else:
            end_pos = len(text)

        block = text[start_pos:end_pos].strip()
        if len(block) > 50:  # Only keep substantial blocks
            blocks.append(block)

    return blocks


def clean_ultimate_output(input_file, output_dir):
    """
    Clean the ultimate scraper output.
    """
    print(f"📂 Reading: {input_file}")

    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    original_count = len(data['answers'])
    print(f"📊 Original answers: {original_count}")

    # Clean each answer
    cleaned_answers = []
    skipped = 0
    split_count = 0

    for i, ans in enumerate(data['answers']):
        question_raw = ans.get('question', '')
        answer_raw = ans.get('answer', '')

        # First, split if there are multiple Q&A blocks in the raw text
        blocks = split_multiple_qa_blocks(question_raw)

        # Count how many raw entries got split
        if len(blocks) > 1:
            split_count += 1

        # Process each block separately
        for block in blocks:
            # Always try to clean the block to separate question from answer
            question, answer = clean_answer_block(block)

            # Skip if cleaning failed
            if question is None or answer is None:
                skipped += 1
                continue

            # Only keep if both question and answer have substance and are different
            # Lowered answer threshold to 10 chars to capture concise but valid answers
            if (question and answer and
                len(question) > 20 and len(answer) > 10 and
                question != answer):
                cleaned_answers.append({
                    'question': question,
                    'answer': answer,
                    'extracted_at': ans.get('extracted_at', datetime.now().isoformat())
                })
            else:
                skipped += 1

        if (i + 1) % 100 == 0:
            print(f"   Processed {i + 1}/{original_count} ({skipped} skipped, {split_count} split)...")

    print(f"✅ Cleaned: {len(cleaned_answers)} answers")

    # Deduplicate
    unique_answers = deduplicate_answers(cleaned_answers)
    print(f"✅ After deduplication: {len(unique_answers)} unique answers")

    # Prepare output
    result = {
        'profile': data.get('profile', {}),
        'scraping_stats': {
            **data.get('scraping_stats', {}),
            'original_extractions': original_count,
            'after_cleaning': len(cleaned_answers),
            'after_deduplication': len(unique_answers)
        },
        'answers': unique_answers
    }

    # Save cleaned JSON
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    user_id = data['profile'].get('user_id', 'unknown')
    json_file = output_path / f"{user_id}_cleaned.json"

    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"💾 Saved: {json_file}")

    # Save cleaned TXT
    txt_file = output_path / f"{user_id}_cleaned.txt"
    with open(txt_file, 'w', encoding='utf-8') as f:
        f.write(f"QUORA PROFILE: {user_id}\n")
        f.write(f"{'=' * 100}\n\n")
        f.write(f"URL: {data['profile'].get('url', 'N/A')}\n")
        f.write(f"Claimed answers: {data['profile'].get('nb_answers_claimed', 'N/A')}\n")
        f.write(f"Unique answers extracted: {len(unique_answers)}\n")
        f.write(f"\n{'=' * 100}\n\n")

        for i, ans in enumerate(unique_answers, 1):
            f.write(f"\n{'=' * 100}\n")
            f.write(f"ANSWER #{i}\n")
            f.write(f"{'=' * 100}\n")
            f.write(f"\n❓ QUESTION:\n{ans['question']}\n")
            f.write(f"\n💬 ANSWER:\n{ans['answer']}\n")

    print(f"💾 Saved: {txt_file}")

    # Summary
    print("\n" + "=" * 80)
    print("✅ CLEANING COMPLETED!")
    print("=" * 80)
    print(f"Original extractions: {original_count}")
    print(f"Blocks split (multiple Q&As): {split_count}")
    print(f"After cleaning: {len(cleaned_answers)}")
    print(f"After deduplication: {len(unique_answers)}")
    print(f"Extraction rate: {len(unique_answers)}/{data['profile'].get('nb_answers_claimed', 'N/A')}")

    return result


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Clean ultimate scraper output')
    parser.add_argument('input_file', help='Path to ultimate JSON file')
    parser.add_argument('-o', '--output', default='./output_cleaned',
                       help='Output directory')
    args = parser.parse_args()

    clean_ultimate_output(args.input_file, args.output)


if __name__ == '__main__':
    main()
