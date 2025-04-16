# src/blog_writer/tools/datamuse_tool.py
import httpx
import json
from crewai.tools import tool

@tool("Datamuse Keyword Finder")
def find_keywords(query: str) -> str:
    """Finds semantically related words (keywords, variations) for a given topic/word using the Datamuse API. Input should be the topic or keyword string."""
    base_url = "https://api.datamuse.com/words"
    params = {"ml": query, "max": 15}
    headers = {"Accept": "application/json"}

    try:
        with httpx.Client() as client:
            print(f"--- Calling Datamuse API (function tool) for query: {query} ---")
            response = client.get(base_url, params=params, headers=headers, timeout=10.0)
            response.raise_for_status()
            results = response.json()

            if results:
                keywords = [item['word'] for item in results]
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
    