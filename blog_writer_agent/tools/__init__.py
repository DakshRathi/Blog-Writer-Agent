# src/blog_writer/tools/__init__.py
from .news_tool import search_news
from .datamuse_tool import find_keywords

# Export the functions directly
__all__ = ['search_news', 'find_keywords']
