from langchain_core.tools import BaseTool

from common.tools.google_search import GoogleSearchTool
from common.tools.web_browser import WebBrowserTool

all_tools: list[BaseTool] = [
    GoogleSearchTool(),
    WebBrowserTool()
]

all_tools_dict: dict[str, BaseTool] = {
    tool.name: tool for tool in all_tools
}

all_tool_names: list[str] = [tool.name for tool in all_tools]
