# src/blog_writer/utils.py
import json
import re
from pathlib import Path
import textstat

OUTPUT_DIR = Path().cwd() / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def calculate_reading_time(text: str) -> int:
    """
    Estimates reading time in minutes based on an average reading speed.
    """
    if not text:
        return 0
    word_count = len(re.findall(r'\w+', text))
    return max(1, round(word_count / 200))

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
        print(f"Warning: Could not calculate readability score. Error: {e}")
        return 0.0

def save_markdown(filename: str, content: str):
    """
    Saves the provided content to a Markdown file in the designated outputs directory.
    """
    filepath = OUTPUT_DIR / f"{filename}.md"
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Markdown content saved to: {filepath}")
    except Exception as e:
        print(f"❌ Error saving Markdown file {filepath}: {e}")

def save_json(filename: str, data: dict):
    """
    Saves the provided dictionary data to a JSON file in the outputs directory.
    """
    filepath = OUTPUT_DIR / f"{filename}.json"
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"✅ JSON metadata saved to: {filepath}")
    except Exception as e:
        print(f"❌ Error saving JSON file {filepath}: {e}")

def sanitize_filename(topic: str) -> str:
    """
    Creates a filesystem-safe filename from a topic string by removing invalid characters
    and replacing spaces.
    """
    if not topic:
        return "untitled_blog"
    sanitized = re.sub(r'[\\/*?:"<>|]', "", topic)
    sanitized = re.sub(r'\s+', '_', sanitized)
    return sanitized[:100]

def print_cli_summary(blog_content, seo_metadata, filename_base):
    print("\n--- Generated Blog Content (Snippet) ---")
    print(blog_content[:500] + ("..." if len(blog_content) > 500 else ""))
    print("----------------------------------------")
    print("\n--- Generated SEO Metadata ---")
    print(json.dumps(seo_metadata, indent=2))
    print("----------------------------")
    print("\n🎉 Process Completed Successfully!")
    print(f"   Blog content saved to: outputs/{filename_base}_blog.md")
    print(f"   Metadata saved to: outputs/{filename_base}_metadata.json")
    print(f"   Estimated Reading Time: {seo_metadata.get('estimated_reading_time_minutes', 'N/A')} minutes")
    print(f"   Readability Score (Flesch): {seo_metadata.get('flesch_reading_ease_score', 'N/A')}")

def extract_blog_content(crew_instance):
    # Extracts the writing task output from the crew instance
    for task in crew_instance.crew().tasks:
        if task == crew_instance.writing_task():
            if task.output and hasattr(task.output, 'raw'):
                return task.output.raw
            elif task.output:
                return str(task.output)
    return None
