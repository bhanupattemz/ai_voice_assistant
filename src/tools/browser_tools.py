from typing import List
from langchain.agents import Tool
import requests
from src.config.settings import settings
from langchain_community.agent_toolkits import PlayWrightBrowserToolkit
from langchain_community.tools.playwright.utils import (
    create_async_playwright_browser, 
)
import nest_asyncio
nest_asyncio.apply()

class BrowserToolFactory:
    def __init__(self):
        self.async_browser=create_async_playwright_browser()
        self.toolkit=PlayWrightBrowserToolkit.from_browser(async_browser=self.async_browser)

    def create_tools(self) -> List[Tool]:
        return self.toolkit.get_tools()

browser_tools=BrowserToolFactory().create_tools()