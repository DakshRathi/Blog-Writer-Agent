# app.py
import streamlit as st
import asyncio
import json
import traceback
import uuid
import time
from blog_writer_agent.crew import BlogWriterCrew, process_crew_output
from blog_writer_agent.utils import sanitize_filename, extract_blog_content


# Streamlit Page Configuration 
st.set_page_config(page_title="AI Blog Writer Agent", layout="wide", page_icon="📝")
st.title("📝 AI Blog Writer Agent")
st.caption("Powered by CrewAI & Gemini")

# Session State Initialization 
if "chat_sessions" not in st.session_state:
    st.session_state.chat_sessions = {}
if "current_session_id" not in st.session_state:
    st.session_state.current_session_id = None
if "crew_instance" not in st.session_state:
    # Initialize crew instance lazily if needed, or keep one instance
    try:
        st.session_state.crew_instance = BlogWriterCrew()
    except Exception as e:
        st.error(f"Failed to initialize BlogWriterCrew: {e}")
        st.stop()

#  Helper Functions 
def create_new_session():
    """Creates a new chat session."""
    session_id = str(uuid.uuid4())
    timestamp = time.strftime("%H:%M:%S")
    session_name = f"Chat - {timestamp}"
    st.session_state.chat_sessions[session_id] = {"name": session_name, "messages": []}
    st.session_state.current_session_id = session_id
    return session_id

def get_session_messages():
    """Gets messages for the current session."""
    if st.session_state.current_session_id and st.session_state.current_session_id in st.session_state.chat_sessions:
        return st.session_state.chat_sessions[st.session_state.current_session_id]["messages"]
    return []

def add_message(role: str, content: any):
    """Adds a message to the current session."""
    if st.session_state.current_session_id:
        st.session_state.chat_sessions[st.session_state.current_session_id]["messages"].append(
            {"role": role, "content": content}
        )

# Sidebar for Session Management and Inputs
with st.sidebar:
    st.header("Chat Sessions")

    # Create a default session if none exist
    if not st.session_state.chat_sessions:
        create_new_session()

    session_options = {sid: data["name"] for sid, data in st.session_state.chat_sessions.items()}
    current_session_id = st.selectbox(
        "Select Chat",
        options=list(session_options.keys()),
        format_func=lambda sid: session_options.get(sid, "Unknown Session"),
        key="session_selector",
        index=list(session_options.keys()).index(st.session_state.current_session_id) if st.session_state.current_session_id in session_options else 0
    )

    # Update current session if selection changes
    if current_session_id != st.session_state.current_session_id:
        st.session_state.current_session_id = current_session_id
        st.rerun() # Rerun to update the main chat display

    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("➕ New Chat"):
            create_new_session()
            st.rerun() # Rerun to update selector and chat display
    with col2:
        if st.button("🗑️ Delete Chat", disabled=(len(st.session_state.chat_sessions) <= 1)):
            if st.session_state.current_session_id in st.session_state.chat_sessions:
                del st.session_state.chat_sessions[st.session_state.current_session_id]
                # Select the first remaining session or create a new one
                if st.session_state.chat_sessions:
                    st.session_state.current_session_id = list(st.session_state.chat_sessions.keys())[0]
                else:
                    create_new_session() # Create one if all were deleted
                st.rerun()


    st.divider()
    st.header("Blog Configuration")
    with st.form("blog_form"):
        topic_input = st.text_input("Enter Blog Topic:", key="topic_input")
        tone_input = st.selectbox(
            "Select Tone:",
            ["Educational", "Professional", "Formal", "Creative", "Technical", "Beginner-Friendly"],
            key="tone_input",
            index=1 # Default to 'Professional'
        )
        # Form submit button
        generate_button_form = st.form_submit_button("✨ Generate Blog Post", type="primary")


# Main Chat Area
st.header(f"Chat: {st.session_state.chat_sessions.get(st.session_state.current_session_id, {}).get('name', 'N/A')}")

# Display existing messages for the currently selected session
messages = get_session_messages()
for idx, message in enumerate(messages):
    with st.chat_message(message["role"]):
        if isinstance(message["content"], dict) and "markdown" in message["content"]:
            # Display Assistant response (Blog + Metadata + Buttons)
            st.markdown(message["content"]["markdown"], unsafe_allow_html=True) # Allow basic HTML if needed in markdown
            metadata = message["content"]["metadata"]
            # Use columns for better layout of JSON and buttons
            col_meta, col_buttons = st.columns([3, 1]) # Adjust ratio as needed
            with col_meta:
                 st.json(metadata, expanded=False)

            with col_buttons:
                slug = metadata.get("slug", "blog_post")
                title = metadata.get("title", "Untitled Blog")
                # Use slug primarily, fallback to title for filename
                safe_filename = sanitize_filename(slug if slug != "default-slug" and slug else title)

                st.download_button(
                    label="⬇️ Blog (.md)",
                    data=message["content"]["markdown"],
                    file_name=f"{safe_filename}.md",
                    mime="text/markdown",
                    key=f"md_dl_{st.session_state.current_session_id}_{idx}", # Unique key per message
                    use_container_width=True
                )
                st.download_button(
                    label="⬇️ Metadata (.json)",
                    data=json.dumps(metadata, indent=2, ensure_ascii=False),
                    file_name=f"{safe_filename}_metadata.json",
                    mime="application/json",
                    key=f"json_dl_{st.session_state.current_session_id}_{idx}", # Unique key per message
                    use_container_width=True
                )
        elif isinstance(message["content"], str):
            st.markdown(message["content"], unsafe_allow_html=True) # Allow bolding etc.

# --- Handle New Input Submission ---
async def handle_generation(topic, tone):
    """Handles the asynchronous crew execution and updates the chat session."""

    # <<< --- ADD RENAMING LOGIC HERE --- >>>
    current_messages = get_session_messages()
    is_first_user_message = len(current_messages) == 0 # Check if message list is empty *before* adding user msg
    current_sid = st.session_state.current_session_id

    if is_first_user_message and current_sid:
        # Create a concise name from the topic
        new_session_name = f"{topic[:40]}" # Truncate topic for name
        if len(topic) > 40:
            new_session_name += "..."
        # Update the name in session state
        st.session_state.chat_sessions[current_sid]["name"] = new_session_name
        print(f"Renamed session {current_sid} to '{new_session_name}'") # Optional debug log
    # <<< --- END RENAMING LOGIC --- >>>

    # Add user message to state *after* checking if it was the first
    add_message("user", f"**{topic}** (Tone: {tone})")

    with st.chat_message("user"):
       st.markdown(f"**{topic}** (Tone: {tone})")

    # Prepare for assistant response and progress updates
    with st.chat_message("assistant"):
        # Placeholder for progress updates during generation
        progress_placeholder = st.empty()
        progress_placeholder.info("🔄 Initializing agents...")
        await asyncio.sleep(0.3) # Short visual delay

        inputs = {'topic': topic, 'tone': tone}
        start_time = time.time()
        crew_result = None
        blog_content_output = None # Initialize

        try:
            crew_instance = st.session_state.crew_instance
            progress_placeholder.info("🧠 Analyzing topic...")

            # Kickoff crew asynchronously
            progress_placeholder.info("▶️ Starting crew execution...")
            crew_task = asyncio.create_task(crew_instance.crew().kickoff_async(inputs=inputs))

            # Simulate progress updates while waiting
            tasks_simulated = ["📚 Researching...", "✍️ Writing content...", "🔍 Optimizing for SEO..."]
            while not crew_task.done():
                idx = int(time.time() * 1.5) % len(tasks_simulated) # Cycle faster
                progress_placeholder.info(tasks_simulated[idx])
                await asyncio.sleep(0.6)

            # Await final result
            crew_result = await crew_task
            end_time = time.time()
            progress_placeholder.success(f"✅ Crew finished in {end_time - start_time:.2f} seconds!")
            await asyncio.sleep(1.5) # Keep success message visible

            # Process Results 
            # Extract final task output (likely SEO metadata string)
            seo_metadata_raw_output = getattr(crew_result, 'raw', str(crew_result))

            # Extract intermediate writing task output (using helper if possible)
            blog_content_output = extract_blog_content(crew_instance)

            if not blog_content_output:
                 # Fallback if helper fails: check tasks_output if available
                 if hasattr(crew_result, 'tasks_output'):
                      for task_output in crew_result.tasks_output:
                          if "write a complete blog post" in task_output.task.config.get('description','').lower():
                               blog_content_output = task_output.raw
                               break
                 if not blog_content_output:
                      st.warning("Could not reliably extract blog content.")
                      # Maybe raise error or use a placeholder? For now, continue processing SEO if possible.
                      blog_content_output = "[Blog content extraction failed]" # Placeholder


            # Call the processing function (now expects strings)
            blog_content, seo_metadata = process_crew_output(
                crew_result=seo_metadata_raw_output,
                writing_task_output=blog_content_output
            )

            if blog_content != "[Blog content extraction failed]" and seo_metadata and "error" not in seo_metadata:
                # Store structured result in session state
                assistant_content = {
                    "markdown": blog_content,
                    "metadata": seo_metadata
                }
                add_message("assistant", assistant_content)
            elif blog_content == "[Blog content extraction failed]" and seo_metadata and "error" not in seo_metadata:
                # If only blog extraction failed, still add metadata info
                add_message("assistant", f"Error extracting blog content. SEO Metadata: {json.dumps(seo_metadata)}")
            else:
                error_detail = seo_metadata.get('error', 'Unknown processing error.') if seo_metadata else 'Processing function failed.'
                raise ValueError(f"Failed to process crew output: {error_detail}")

        except Exception as e:
            st.error(f"An error occurred during generation: {e}")
            add_message("assistant", f"Sorry, I encountered an error: {str(e)[:500]}...") # Truncate long errors
            traceback.print_exc() 

        finally:
            progress_placeholder.empty() 


# Trigger Generation
if generate_button_form:
    if not topic_input:
        st.warning("Please enter a blog topic.")
    else:
        asyncio.run(handle_generation(topic_input, tone_input))
        st.rerun()