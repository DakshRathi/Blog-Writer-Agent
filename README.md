# AI Blog Writer Agent 📝

[![Python Version](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://python.org)
[![Framework](https://img.shields.io/badge/Framework-CrewAI-orange.svg)](https://crewai.com/)
[![UI](https://img.shields.io/badge/UI-Streamlit-red.svg)](https://streamlit.io/)

An autonomous content generation agent built with Python and CrewAI that mimics the role of a junior blog writer and SEO optimizer. This system takes a topic and tone, conducts research using public APIs, generates an SEO-optimized blog post, and exports the content and metadata.

## Overview

This project aims to build an autonomous system capable of:

1.  **Understanding a Topic:** Breaking down a given topic into sub-topics.
2.  **Conducting Research:** Using NewsData.io and Datamuse APIs for context and keywords.
3.  **Generating Content:** Leveraging Google Geminix via CrewAI to write structured blog posts in Markdown.
4.  **SEO Optimization:** Creating titles, meta descriptions, tags, slugs, and calculating readability scores.
5.  **Exporting:** Saving the final blog post as a `.md` file and metadata as a `.json` file.

The system features both a Command-Line Interface (CLI) and an interactive Streamlit web application.

## ✨ Features

*   **Autonomous Workflow:** Uses a CrewAI multi-agent system (Topic Analyzer, Researcher, Writer, SEO Optimizer).
*   **API Integration:** Fetches real-time news (NewsData.io) and semantic keywords (Datamuse).
*   **LLM-Powered Writing:** Utilizes `gemini-2.0-flash` for content generation.
*   **SEO Optimization:** Generates essential metadata (Title, Description, Tags, Slug).
*   **Readability Score:** Calculates and includes the Flesch Reading Ease score.
*   **Structured Output:** Exports blog content in Markdown (`.md`) and metadata in JSON (`.json`).
*   **Dual Interfaces:**
    *   **CLI:** Run generation via command-line arguments.
    *   **Streamlit UI:** Interactive web application with session management.
*   **Asynchronous Execution:** Leverages `kickoff_async` in CrewAI for a non-blocking user experience.
*   **Session Management (Streamlit):** Supports multiple, renameable chat sessions.
*   **Modular Design:** Codebase organized into distinct modules for agents, tasks, tools, and utilities.

## 📂 Project Structure
```
└── 📁blog-writer-agent
│ └── 📁blog_writer_agent # Main package source
│   ├── init.py
│   ├── 📁config # Agent/Task definitions
│   │ ├── agents.yaml
│   │ └── tasks.yaml
│   ├── crew.py # CrewAI setup and orchestration
│   ├── 📁tools # API interaction functions
│   │ ├── init.py
│   │ ├── datamuse_tool.py
│   │ └── news_tool.py
│   └── utils.py # Helper functions (file I/O, metrics, etc.)
├── 📁outputs/ # Default location for generated files
│ ├── example_blog.md
│ └── example_metadata.json
├── .env # API Keys (!!! IMPORTANT - Create this file !!!)
├── .gitignore
├── app.py # Streamlit application entry point
├── main.py # CLI application entry point
└── requirements.txt # Project dependencies
```


## ⚙️ Technologies Used

*   **Core Framework:** Python 3.9+, CrewAI
*   **LLM:** gemini-2.0-flash (via CrewAI integration)
*   **APIs:** NewsData.io, Datamuse API
*   **Web Interface:** Streamlit
*   **HTTP Requests:** `httpx` (within tools)
*   **Asynchronous:** `asyncio` (`kickoff_async` in CrewAI)
*   **Utilities:** `python-dotenv` (API keys), `PyYAML` (configs), `textstat` (readability)

## 🚀 Setup and Installation

1.  **Prerequisites:**
    *   Python 3.9 or higher installed.
    *   `pip` package installer.

2.  **Clone the Repository:**
    ```
    git clone https://github.com/DakshRathi/Blog-Writer-Agent.git
    cd blog-writer-agent
    ```

3.  **Create a Virtual Environment:** (Recommended)
    ```
    python -m venv .venv
    ```

4.  **Activate the Environment:**
    *   **macOS/Linux:** `source .venv/bin/activate`
    *   **Windows (CMD):** `.venv\Scripts\activate.bat`
    *   **Windows (PowerShell):** `.venv\Scripts\Activate.ps1`

5.  **Install Dependencies:**
    ```
    pip install -r requirements.txt
    ```

6.  **Create `.env` File:**
    *   Create a file named `.env` in the project's root directory.
    *   Add your API keys to this file. Get keys from:
        *   **Google AI Studio:** [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)
        *   **NewsData.io:** [https://newsdata.io/](https://newsdata.io/)

    ```
    # .env file content
    GOOGLE_API_KEY="YOUR_GEMINI_API_KEY_HERE"
    NEWSDATA_API_KEY="YOUR_NEWSDATA_IO_API_KEY_HERE"
    ```
    **Important:** Ensure the `.env` file is listed in your `.gitignore` to avoid committing keys.

## ▶️ Usage

You can run the AI Blog Writer Agent using either the CLI or the Streamlit web interface.

### Command-Line Interface (CLI)

Execute the `main.py` script from the project root directory:

```
python main.py --topic "Your Blog Topic Here" [--tone "Desired Tone"]
```


**Arguments:**

*   `--topic` (Required): The main subject for the blog post. Enclose in quotes if it contains spaces.
*   `--tone` (Optional): The desired writing style (e.g., "Professional", "Creative", "Technical"). Defaults to "Educational".

**Example:**

```
python main.py --topic "The Future of Renewable Energy" --tone "Formal"
```


The script will output progress logs to the console and save the generated `.md` and `.json` files to the `outputs/` directory.

### Streamlit Web Application

Launch the interactive web interface:

```
streamlit run app.py
```


This will typically open the application in your web browser at `http://localhost:8501`.

**Features:**

*   **Multi-Session Chat:** Create, select, and delete different chat conversations using the sidebar.
*   **Input:** Enter the blog topic and select the tone from the dropdown in the sidebar form.
*   **Generate:** Click "Generate Blog Post". The session name will update based on the first topic entered.
*   **Progress:** A spinner indicates that the agent crew is working.
*   **Output:** The generated blog appears in the chat, followed by expandable JSON metadata and download buttons.


## 💡 Key Engineering Features


*   **🤖 Modular Design:** The system is broken down into distinct agents (`topic_analyzer`, `researcher`, `writer`, `seo_optimizer`) defined in `agents.yaml` and corresponding tasks in `tasks.yaml`. Code is organized into modules for tools, utilities, and the core crew logic.
*   **⚡ Asynchronous Execution:** The application utilizes `kickoff_async` to run the CrewAI workflow asynchronously, preventing the UI from blocking during generation. API calls within tools are designed to be compatible with this async orchestration.
*   **🧹 Clean Interfaces:** Provides both a parameterized CLI (`main.py` with `argparse`) and an intuitive Streamlit web UI (`app.py`).
*   **🛠️ API Tooling:** Dedicated functions in the `tools/` directory handle interactions with external APIs (NewsData, Datamuse) with basic error handling.
*   **📊 Structured Outputs:** Reliably generates well-formatted Markdown files and JSON metadata.


## 🔮 Future Improvements

*   **Advanced Error Handling:** Implement more robust retry logic for API calls (e.g., exponential backoff for rate limits).
*   **Caching:** Re-introduce caching (e.g., `@cache` or disk-based) for API tools to further reduce redundant calls, especially for Datamuse.
*   **Batch Processing:** Add CLI support for processing a list of topics from a file or multiple arguments.
*   **Real-time Progress:** Investigate deeper integration with CrewAI callbacks (if available) to provide more granular progress updates in Streamlit instead of simulation.
*   **Content Editing Agent:** Add an optional "Editor" agent to review and refine the Writer's output before SEO optimization.


