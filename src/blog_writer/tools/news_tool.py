# src/blog_writer/tools/news_tool.py
import os
import httpx
import json
from functools import cache # Use cache for memoization
from crewai.tools import BaseTool
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class NewsSearchTool(BaseTool):
    name: str = "News Search Tool"
    description: str = ("Searches for recent news articles on a given topic using the NewsData.io API. "
                       "Input should be the search query (topic string).")
    api_key: str = os.getenv("NEWSDATA_API_KEY")

    @cache # Cache results for the same query during a single run/session
    def _run(self, search_query: str) -> str:
        """
        Executes the news search.
        """
        if not self.api_key:
            return "Error: NEWSDATA_API_KEY not found in environment variables. Please set it in the .env file."

        # NewsData.io endpoint details (refer to their documentation if needed)
        base_url = "https://newsdata.io/api/1/news"
        params = {
            "apikey": self.api_key,
            "q": search_query,
            "language": "en", # Focus on English articles
            "size": 5
        }
        headers = {"Accept": "application/json"}

        try:
            # Using httpx for sync requests, consider AsyncClient if using asyncio extensively [1]
            with httpx.Client() as client:
                print(f"--- Calling NewsData API for query: {search_query} ---") # For debugging
                response = client.get(base_url, params=params, headers=headers, timeout=15.0) # Increased timeout
                response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)

                data = response.json()

                if data.get("status") == "success" and data.get("results"):
                    articles = data["results"]
                    # Format results clearly for the agent
                    formatted_results = ["**Recent News:**"]
                    for article in articles:
                        title = article.get('title', 'N/A')
                        link = article.get('link', '#')
                        # Use description or content snippet if available and concise
                        description = article.get('description') or article.get('content', '')
                        snippet = (description[:200] + '...') if description and len(description) > 200 else description or "No description."

                        formatted_results.append(f"- Title: {title}\n  Snippet: {snippet}\n  Link: {link}")

                    return "\n".join(formatted_results) if len(formatted_results) > 1 else "No relevant news articles found."
                else:
                    # Handle API-specific errors or empty results
                    error_msg = data.get('results', {}).get('message', 'Unknown API error or no results')
                    print(f"NewsData API Warning: {error_msg}")
                    return f"No news results found or API error: {error_msg}"

        except httpx.HTTPStatusError as e:
            # Handle HTTP errors (e.g., 401 Unauthorized, 429 Rate Limit, 5xx Server Error)
            error_message = f"HTTP error calling NewsData API: {e.response.status_code} - {e.response.text}"
            print(f"Error: {error_message}")
            return error_message # Return error message to the agent
        except httpx.TimeoutException:
            error_message = "Error: Request to NewsData API timed out."
            print(error_message)
            return error_message
        except httpx.RequestError as e:
            # Handle other network-related errors (DNS, connection issues)
            error_message = f"Network error calling NewsData API: {e}"
            print(error_message)
            return error_message
        except json.JSONDecodeError:
            error_message = "Error: Could not decode JSON response from NewsData API."
            print(error_message)
            return error_message
        except Exception as e:
            # Catch any other unexpected errors
            error_message = f"An unexpected error occurred with NewsData API: {e}"
            print(error_message)
            return error_message
