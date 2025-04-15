# src/blog_writer/crew.py
import os
import json
from crewai import Agent, Task, Crew, Process
from crewai.project import CrewBase, agent, task, crew
from langchain_google_genai import ChatGoogleGenerativeAI
from .tools import news_tool, datamuse_tool
from .utils import calculate_reading_time, calculate_readability_score
from dotenv import load_dotenv

load_dotenv()

llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash", # Or "gemini-1.5-flash", etc.
    google_api_key=os.getenv("GOOGLE_API_KEY"),
    temperature=0.7
)

# --- Crew Definition ---
@CrewBase
class BlogWriterCrew:
    """BlogWriterCrew orchestrates agents and tasks for autonomous blog generation."""

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    def __init__(self):
        """Initialize the crew with the LLM and necessary tools."""
        self.llm = llm
        self.news_tool = news_tool
        self.datamuse_tool = datamuse_tool

    # --- Agent Definitions ---
    @agent
    def topic_analyzer(self) -> Agent:
        return Agent(
            config=self.agents_config['topic_analyzer'],
            llm=self.llm,
            allow_delegation=False,
            verbose=True
        )

    @agent
    def researcher(self) -> Agent:
        return Agent(
            config=self.agents_config['researcher'],
            tools=[self.news_tool, self.datamuse_tool],
            llm=self.llm,
            allow_delegation=False,
            verbose=True
        )

    @agent
    def writer(self) -> Agent:
        return Agent(
            config=self.agents_config['writer'],
            llm=self.llm,
            allow_delegation=False,
            verbose=True
        )

    @agent
    def seo_optimizer(self) -> Agent:
        return Agent(
            config=self.agents_config['seo_optimizer'],
            # SEO agent might use Datamuse again for keyword ideas, or just analyze content
            # Assigning it based on potential utility, even if task description focuses on content analysis
            tools=[self.datamuse_tool],
            llm=self.llm,
            allow_delegation=False,
            verbose=True
        )

    # --- Task Definitions ---
    @task
    def topic_analysis_task(self) -> Task:
        return Task(
            config=self.tasks_config['topic_analysis_task'],
            agent=self.topic_analyzer()
        )

    @task
    def research_task(self) -> Task:
        return Task(
            config=self.tasks_config['research_task'],
            agent=self.researcher(),
            context=[self.topic_analysis_task()]
        )

    @task
    def writing_task(self) -> Task:
        return Task(
            config=self.tasks_config['writing_task'],
            agent=self.writer(),
            context=[
                self.topic_analysis_task(),
                self.research_task()
            ]
        )

    @task
    def seo_optimization_task(self) -> Task:
        return Task(
            config=self.tasks_config['seo_optimization_task'],
            agent=self.seo_optimizer(),
            context=[self.writing_task()]
        )

    # --- Crew Assembly ---
    @crew
    def crew(self) -> Crew:
        """Creates and configures the sequential blog writing crew."""
        return Crew(
            agents=self.get_agents(),
            tasks=self.get_tasks(),  
            process=Process.sequential,
            verbose=2 # Set verbosity level (0=silent, 1=basic, 2=detailed)
            # full_output=True # May provide more detailed output object
        )

    # Helper methods to instantiate agents and tasks
    def get_agents(self):
        """Returns a list of agent instances for the crew."""
        return [
            self.topic_analyzer(),
            self.researcher(),
            self.writer(),
            self.seo_optimizer(),
        ]

    def get_tasks(self):
        """Returns a list of task instances for the crew."""
        return [
            self.topic_analysis_task(),
            self.research_task(),
            self.writing_task(),
            self.seo_optimization_task(),
        ]

# --- Post-Processing Logic (typically called from main script) ---
def process_crew_output(crew_result, writing_task_output):
    """
    Processes the raw output from the crew, calculates final metrics,
    and returns structured blog content and metadata.

    Args:
        crew_result: The result obtained from crew.kickoff(). This is typically the output of the last task in a sequential process.
        writing_task_output: The raw markdown output from the writing task.

    Returns:
        A tuple: (blog_content: str, metadata: dict) or (None, None) on error.
    """
    if not writing_task_output:
        print("❌ Error: Writing task output (blog content) is missing.")
        return None, None

    blog_content = writing_task_output # Assign the writing task output

    # The crew_result should be the output of the seo_optimization_task (JSON string)
    seo_metadata_raw = crew_result
    seo_metadata = {}

    if not seo_metadata_raw or not isinstance(seo_metadata_raw, str):
        print(f"❌ Error: SEO task output is missing or not a string. Found: {type(seo_metadata_raw)}")
        return blog_content, {"error": "Missing or invalid SEO metadata from crew."}


    # Parse the JSON string from the SEO task output
    try:
        if seo_metadata_raw.startswith("```json"):
            seo_metadata_raw = seo_metadata_raw[7:-3].strip()
        elif seo_metadata_raw.startswith("```"):
             seo_metadata_raw = seo_metadata_raw[3:-3].strip()

        seo_metadata = json.loads(seo_metadata_raw)

        # Validate required keys
        required_keys = ["title", "meta_description", "tags", "slug"]
        if not all(key in seo_metadata for key in required_keys):
            print(f"Warning: SEO metadata missing required keys. Found: {seo_metadata.keys()}")

    except json.JSONDecodeError as e:
        print(f"❌ Error parsing SEO metadata JSON: {e}")
        print(f"Raw SEO output was: {seo_metadata_raw}")
        return blog_content, {"error": "Failed to parse SEO JSON", "raw_output": seo_metadata_raw}
    except Exception as e:
        print(f"❌ Unexpected error processing SEO metadata: {e}")
        return blog_content, {"error": str(e), "raw_output": seo_metadata_raw}


    # Calculate final metrics using the blog content
    try:
        reading_time = calculate_reading_time(blog_content)
        readability_score = calculate_readability_score(blog_content)

        # Add calculated metrics to the metadata dictionary
        seo_metadata['estimated_reading_time_minutes'] = reading_time
        seo_metadata['flesch_reading_ease_score'] = readability_score
    except Exception as e:
        print(f"Warning: Failed to calculate reading time/readability score. Error: {e}")
        seo_metadata['estimated_reading_time_minutes'] = "N/A"
        seo_metadata['flesch_reading_ease_score'] = "N/A"


    return blog_content, seo_metadata