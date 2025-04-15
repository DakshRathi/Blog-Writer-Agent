# src/blog_writer/tools/__init__.py

# Import the tool classes
from .news_tool import NewsSearchTool
from .datamuse_tool import DatamuseTool

# Instantiate the tools for use in the crew
news_tool = NewsSearchTool()
datamuse_tool = DatamuseTool()

# Define an __all__ for explicit exports
__all__ = ['news_tool', 'datamuse_tool', 'NewsSearchTool', 'DatamuseTool']
