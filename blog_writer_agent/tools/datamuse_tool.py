# src/blog_writer/tools/datamuse_tool.py
import httpx
import json
from functools import cache
from crewai.tools import BaseTool

class DatamuseTool(BaseTool):
    name: str = "Datamuse Keyword Finder"
    description: str = ("Finds semantically related words (keywords, variations) "
                       "for a given topic/word using the Datamuse API. Input should be the topic or keyword string.")

    @cache # Cache results for the same query [1]
    def _run(self, query: str) -> str:
        """
        Executes the Datamuse query.
        """
        base_url = "https://api.datamuse.com/words"
        # 'ml' means "means like" - good for general semantic relation
        # 'rel_syn' finds synonyms specifically
        params = {
            "ml": query, # Find words with similar meaning to the query
            "max": 15    # Limit results as per task description example
            }
        headers = {"Accept": "application/json"}

        try:
            with httpx.Client() as client:
                print(f"--- Calling Datamuse API for query: {query} ---")
                response = client.get(base_url, params=params, headers=headers, timeout=10.0)
                response.raise_for_status() # Check for HTTP errors

                results = response.json()

                if results:
                    # Extract just the words
                    keywords = [item['word'] for item in results]
                    # Format clearly for the agent
                    return f"**Keywords related to '{query}':**\n- {', '.join(keywords)}"
                else:
                    return f"No related keywords found for '{query}' via Datamuse."

        except httpx.HTTPStatusError as e:
            error_message = f"HTTP error calling Datamuse API: {e.response.status_code} - {e.response.text}"
            print(f"Error: {error_message}")
            return error_message
        except httpx.TimeoutException:
            error_message = "Error: Request to Datamuse API timed out."
            print(error_message)
            return error_message
        except httpx.RequestError as e:
            error_message = f"Network error calling Datamuse API: {e}"
            print(error_message)
            return error_message
        except json.JSONDecodeError:
            error_message = "Error: Could not decode JSON response from Datamuse API."
            print(error_message)
            return error_message
        except Exception as e:
            error_message = f"An unexpected error occurred with Datamuse API: {e}"
            print(error_message)
            return error_message
