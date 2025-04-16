# src/blog_writer/crew.py
import os
import json
from crewai import Agent, Task, Crew, Process
from crewai.project import CrewBase, agent, task, crew
from crewai import LLM
from .tools import search_news, find_keywords 
from .utils import calculate_reading_time, calculate_readability_score
from dotenv import load_dotenv

load_dotenv()

llm = LLM(
    model="gemini/gemini-2.0-flash",
    api_key=os.getenv("GOOGLE_API_KEY"),
    temperature=0.7
)

# --- Crew Definition ---
@CrewBase
class BlogWriterCrew:
    """BlogWriterCrew orchestrates agents and tasks for autonomous blog generation."""

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    def __init__(self):
        """Initialize the crew with the LLM."""
        self.llm = llm

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
            tools=[search_news, find_keywords],
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
            tools=[find_keywords],
            llm=self.llm,
            allow_delegation=False,
            verbose=True
        )

    # --- Task Definitions ---
    @task
    def topic_analysis_task(self) -> Task:
        return Task(
            config=self.tasks_config['topic_analysis_task'],
        )

    @task
    def research_task(self) -> Task:
        return Task(
            config=self.tasks_config['research_task'],
            tools=[search_news, find_keywords],
        )

    @task
    def writing_task(self) -> Task:
        return Task(
            config=self.tasks_config['writing_task'],
        )

    @task
    def seo_optimization_task(self) -> Task:
        return Task(
            config=self.tasks_config['seo_optimization_task'],
            tools=[find_keywords],
        )

    # --- Crew Assembly ---
    @crew
    def crew(self) -> Crew:
        """Creates and configures the sequential blog writing crew."""
        return Crew(
            agents=self.get_agents(),
            tasks=self.get_tasks(),  
            process=Process.sequential,
            verbose=True,
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
        Tuple: (blog_content: str, metadata: dict) or (None, None) on error.
    """
    if not writing_task_output:
        print("❌ Error: Writing task output (blog content) is missing.")
        return None, None
    
    if writing_task_output.startswith("```markdown"):
        writing_task_output = writing_task_output[11:-3].strip()
    elif writing_task_output.startswith("```"):
        writing_task_output = writing_task_output[3:-3].strip()

    seo_metadata = {}

    if not crew_result or not isinstance(crew_result, str):
        # Adjusted error message based on the change above
        print(f"❌ Error: Raw SEO task output is missing or not a string. Found: {type(crew_result)}")
        return writing_task_output, {"error": "Missing or invalid raw SEO metadata from crew."}



    # Parse the JSON string from the SEO task output
    try:
        if crew_result.startswith("```json"):
            crew_result = crew_result[7:-3].strip()
        elif crew_result.startswith("```"):
            crew_result = crew_result[3:-3].strip()

        seo_metadata = json.loads(crew_result)

        # Validate required keys
        required_keys = ["title", "meta_description", "tags", "slug"]
        if not all(key in seo_metadata for key in required_keys):
            print(f"Warning: SEO metadata missing required keys. Found: {seo_metadata.keys()}")

    except json.JSONDecodeError as e:
        print(f"❌ Error parsing SEO metadata JSON: {e}")
        print(f"Raw SEO output was: {crew_result}")
        return writing_task_output, {"error": "Failed to parse SEO JSON", "raw_output": crew_result}
    except Exception as e:
        print(f"❌ Unexpected error processing SEO metadata: {e}")
        return writing_task_output, {"error": str(e), "raw_output": crew_result}


    # Calculate final metrics using the blog content
    try:
        reading_time = calculate_reading_time(writing_task_output)
        readability_score = calculate_readability_score(writing_task_output)

        # Add calculated metrics to the metadata dictionary
        seo_metadata['estimated_reading_time_minutes'] = reading_time
        seo_metadata['flesch_reading_ease_score'] = readability_score
    except Exception as e:
        print(f"Warning: Failed to calculate reading time/readability score. Error: {e}")
        seo_metadata['estimated_reading_time_minutes'] = "N/A"
        seo_metadata['flesch_reading_ease_score'] = "N/A"


    return writing_task_output, seo_metadata