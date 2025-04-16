# main.py
import argparse
import json
import sys
import traceback
from blog_writer_agent.crew import BlogWriterCrew, process_crew_output
from blog_writer_agent.utils import save_markdown, save_json, sanitize_filename

# --- Main Execution Logic ---
def main():
    """
    Main function to run the Blog Writing Agent via Command Line Interface.
    """
    # --- Argument Parsing ---
    parser = argparse.ArgumentParser(
        description="Autonomous Blog Writing Agent CLI",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "--topic",
        type=str,
        required=True,
        help="The main topic for the blog post (e.g., 'How Python is used in AI')."
    )
    parser.add_argument(
        "--tone",
        type=str,
        default="Educational",
        help="Specify the desired tone for the blog post (e.g., Formal, Creative, Technical)."
    )

    try:
        args = parser.parse_args()
    except SystemExit:
        sys.exit(1)


    # --- Input Preparation ---
    topic = args.topic
    tone = args.tone
    print(f"🚀 Starting blog generation for topic: '{topic}'")
    print(f"   Tone specified: '{tone}'")

    # Prepare the inputs dictionary for the crew
    inputs = {
        'topic': topic,
        'tone': tone
    }

    # --- Crew Execution ---
    try:
        print("\n🤖 Instantiating the Blog Writer Crew...")
        crew_instance = BlogWriterCrew()

        print("▶️ Kicking off the crew execution... (This might take few minutes)")
        result = crew_instance.crew().kickoff(inputs=inputs)

        print("\n🏁 Crew execution finished.")
        print("--------------------------------------------------")
        print("📊 Processing results...")

        final_tasks = crew_instance.crew().tasks
        blog_content_output = None

        # Initialize raw output from CrewOutput object
        seo_metadata_raw_output = None
        if result and hasattr(result, 'raw'):
            seo_metadata_raw_output = result.raw # <<< Extract raw output here
        elif isinstance(result, str): # Fallback
            seo_metadata_raw_output = result

        for task in final_tasks:
            if task == crew_instance.writing_task():
                if task.output and hasattr(task.output, 'raw'):
                    blog_content_output = task.output.raw
                    print("   Extracted blog content from writing task.")
                    break
                elif task.output: # Fallback if raw attribute is not present
                    blog_content_output = str(task.output)
                    print("   Extracted blog content (as string) from writing task output.")
                    break
        
        if not blog_content_output:
            print("❌ Critical Error: Could not retrieve final blog content from the writing task output.")
            print("   Please check the crew execution logs (verbose=2) for the Markdown output.")
            print("   Cannot proceed with saving or metric calculation.")
            return 

        # Use the dedicated processing function from crew.py
        blog_content, seo_metadata = process_crew_output(
            crew_result=seo_metadata_raw_output,
            writing_task_output=blog_content_output
        )

        # --- Output Handling & Saving ---
        if blog_content and seo_metadata and "error" not in seo_metadata:
            print("   Successfully processed crew output.")

            print("\n--- Generated Blog Content (Snippet) ---")
            print(blog_content[:500] + ("..." if len(blog_content) > 500 else ""))
            print("----------------------------------------")

            print("\n--- Generated SEO Metadata ---")
            print(json.dumps(seo_metadata, indent=2))
            print("----------------------------")

            # Sanitize the topic to create a safe filename
            safe_filename_base = sanitize_filename(topic)

            # Save the outputs using utility functions
            print("\n💾 Saving outputs...")
            save_markdown(f"{safe_filename_base}_blog", blog_content)
            save_json(f"{safe_filename_base}_metadata", seo_metadata)

            # Display final summary as required [1]
            print("\n🎉 Process Completed Successfully!")
            print(f"   Blog content saved to: outputs/{safe_filename_base}_blog.md")
            print(f"   Metadata saved to: outputs/{safe_filename_base}_metadata.json")
            reading_time = seo_metadata.get('estimated_reading_time_minutes', 'N/A')
            readability = seo_metadata.get('flesch_reading_ease_score', 'N/A')
            print(f"   Estimated Reading Time: {reading_time} minutes")
            print(f"   Readability Score (Flesch): {readability}")

        else:
            # Handle cases where processing failed (errors printed within process_crew_output)
            print("\n❌ Error occurred during result processing.")
            if seo_metadata and "error" in seo_metadata:
                print(f"   Details: {seo_metadata.get('error')}")
                if "raw_output" in seo_metadata:
                     print(f"   Raw SEO Output: {seo_metadata['raw_output']}")

            # Still try to save the raw content if available
            if blog_content_output:
                print("\n💾 Attempting to save raw blog content despite processing errors...")
                safe_filename_base = sanitize_filename(topic)
                save_markdown(f"{safe_filename_base}_blog_raw", blog_content_output)


    # --- Error Handling for Crew Execution ---
    except ImportError as e:
        print(f"❌ Critical Import Error: {e}. Please check project structure and dependencies.")
    except Exception as e:
        print(f"\n❌ An unexpected error occurred during the process:")
        traceback.print_exc()
        print(f"\nError Summary: {e}")

# --- Script Entry Point ---
if __name__ == "__main__":
    main()
