# src/blog_writer/utils.py
import json
import re
from pathlib import Path
import textstat  # For readability score 

# Directory to store outputs
OUTPUT_DIR = Path().cwd().parent / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def calculate_reading_time(text: str) -> int:
    """
    Estimates reading time in minutes based on an average reading speed.
    """
    if not text:
        return 0
    word_count = len(re.findall(r'\w+', text))
    # Average reading speed: ~200 words per minute
    reading_time = round(word_count / 200)
    return max(1, reading_time)  # Ensure minimum 1 minute reading time

def calculate_readability_score(text: str) -> float:
    """
    Calculates Flesch Reading Ease score.
    Higher scores indicate easier readability.
    """
    if not text:
        return 0.0
    try:
        return round(textstat.flesch_reading_ease(text), 2)
    except Exception as e:
        # Handle potential errors if text is too short or unusual
        print(f"Warning: Could not calculate readability score. Error: {e}")
        return 0.0  # Return 0.0 or None on failure

def save_markdown(filename: str, content: str):
    """
    Saves the provided content to a Markdown file in the designated outputs directory.
    """
    filepath = OUTPUT_DIR / f"{filename}.md"
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Markdown content saved to: {filepath}")
    except IOError as e:
        print(f"❌ Error saving Markdown file {filepath}: {e}")
    except Exception as e:
        print(f"❌ An unexpected error occurred while saving Markdown: {e}")


def save_json(filename: str, data: dict):
    """
    Saves the provided dictionary data to a JSON file in the outputs directory.
    """
    filepath = OUTPUT_DIR / f"{filename}.json"
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            # Use indent for readability, ensure_ascii=False for proper unicode handling
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"✅ JSON metadata saved to: {filepath}")
    except IOError as e:
        print(f"❌ Error saving JSON file {filepath}: {e}")
    except TypeError as e:
        # This usually happens if the data dictionary contains non-serializable types
        print(f"❌ Error serializing data to JSON for {filepath}: {e}")
    except Exception as e:
        print(f"❌ An unexpected error occurred while saving JSON: {e}")

def sanitize_filename(topic: str) -> str:
    """
    Creates a filesystem-safe filename from a topic string by removing invalid characters
    and replacing spaces.
    """
    if not topic:
        return "untitled_blog"
    # Remove characters that are invalid in filenames across different OS
    sanitized = re.sub(r'[\\/*?:"<>|]', "", topic)
    # Replace spaces with underscores for better readability/compatibility
    sanitized = sanitized.replace(" ", "_")
    # Collapse multiple consecutive underscores
    sanitized = re.sub(r'_+', '_', sanitized)
    # Remove leading/trailing underscores
    sanitized = sanitized.strip('_')
    # Truncate to a reasonable length
    return sanitized[:100]
