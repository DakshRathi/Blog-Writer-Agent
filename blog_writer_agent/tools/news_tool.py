# src/blog_writer/tools/news_tool.py
import os
import httpx
import json
from crewai.tools import tool
from dotenv import load_dotenv

load_dotenv()

@tool("News Search Tool")
def search_news(search_query: str) -> str:
    """Searches for recent news articles on a given topic using the NewsData.io API. Input should be the search query (topic string)."""
    api_key = os.getenv("NEWSDATA_API_KEY")
    if not api_key:
        return "Error: NEWSDATA_API_KEY not found in environment variables. Please set it in the .env file."

    base_url = "https://newsdata.io/api/1/news"
    params = {
        "apikey": api_key,
        "q": search_query,
        "language": "en",
        "size": 5
    }
    headers = {"Accept": "application/json"}

    try:
        with httpx.Client() as client:
            print(f"--- Calling NewsData API (function tool) for query: {search_query} ---")
            response = client.get(base_url, params=params, headers=headers, timeout=15.0)
            response.raise_for_status()
            data = response.json()

            if data.get("status") == "success" and data.get("results"):
                articles = data["results"]
                formatted_results = ["**Recent News:**"]
                for article in articles:
                    title = article.get('title', 'N/A')
                    link = article.get('link', '#')
                    description = article.get('description') or article.get('content', '')
                    snippet = (description[:200] + '...') if description and len(description) > 200 else description or "No description."
                    formatted_results.append(f"- Title: {title}\n  Snippet: {snippet}\n  Link: {link}")
                return "\n".join(formatted_results) if len(formatted_results) > 1 else "No relevant news articles found."
            else:
                error_msg = data.get('results', {}).get('message', 'Unknown API error or no results')
                print(f"NewsData API Warning: {error_msg}")
                return f"No news results found or API error: {error_msg}"

    except httpx.HTTPStatusError as e:
        error_message = f"HTTP error calling NewsData API: {e.response.status_code} - {e.response.text}"
        print(f"Error: {error_message}")
        return error_message
    except httpx.TimeoutException:
        error_message = "Error: Request to NewsData API timed out."
        print(error_message)
        return error_message
    except httpx.RequestError as e:
        error_message = f"Network error calling NewsData API: {e}"
        print(error_message)
        return error_message
    except json.JSONDecodeError:
        error_message = "Error: Could not decode JSON response from NewsData API."
        print(error_message)
        return error_message
    except Exception as e:
        error_message = f"An unexpected error occurred with NewsData API: {e}"
        print(error_message)
        return error_message
