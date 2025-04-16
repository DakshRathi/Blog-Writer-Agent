import argparse
import sys
import asyncio
import traceback
from blog_writer_agent.crew import BlogWriterCrew, process_crew_output
from blog_writer_agent.utils import save_markdown, save_json, sanitize_filename, print_cli_summary, extract_blog_content

def parse_args():
    parser = argparse.ArgumentParser(
        description="Autonomous Blog Writing Agent CLI",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("--topic", type=str, required=True, help="The main topic for the blog post.")
    parser.add_argument("--tone", type=str, default="Educational", help="Desired tone (e.g., Formal, Creative, Technical).")
    return parser.parse_args()

async def main():
    args = parse_args()
    topic, tone = args.topic, args.tone
    print(f"🚀 Starting blog generation for topic: '{topic}'\n   Tone specified: '{tone}'")

    inputs = {'topic': topic, 'tone': tone}
    try:
        print("\n🤖 Instantiating the Blog Writer Crew...")
        crew_instance = BlogWriterCrew()
        print("▶️ Kicking off the crew execution asynchronously... (This might take few minutes)")
        result = await crew_instance.crew().kickoff_async(inputs=inputs)
        print("\n🏁 Crew execution finished.\n--------------------------------------------------\n📊 Processing results...")

        blog_content_output = extract_blog_content(crew_instance)
        seo_metadata_raw_output = getattr(result, 'raw', result) 

        if not blog_content_output:
            print("❌ Critical Error: Could not retrieve final blog content from writing task.")
            return

        blog_content, seo_metadata = process_crew_output(seo_metadata_raw_output, blog_content_output)

        # --- Output Handling & Saving ---
        if blog_content and seo_metadata and "error" not in seo_metadata:
            safe_filename_base = sanitize_filename(topic)
            save_markdown(f"{safe_filename_base}_blog", blog_content)
            save_json(f"{safe_filename_base}_metadata", seo_metadata)
            print_cli_summary(blog_content, seo_metadata, safe_filename_base)
        else:
            print("\n❌ Error occurred during result processing.")
            if seo_metadata and "error" in seo_metadata:
                print(f"   Details: {seo_metadata.get('error')}")
                if "raw_output" in seo_metadata:
                    print(f"   Raw SEO Output: {seo_metadata['raw_output']}")
            if blog_content_output:
                print("\n💾 Attempting to save raw blog content despite processing errors...")
                safe_filename_base = sanitize_filename(topic)
                save_markdown(f"{safe_filename_base}_blog_raw", blog_content_output)

    # --- Error Handling ---
    except Exception as e:
        print(f"\n❌ An unexpected error occurred:")
        traceback.print_exc() 
        print(f"\nError Summary: {e}")

if __name__ == "__main__":
    asyncio.run(main())
