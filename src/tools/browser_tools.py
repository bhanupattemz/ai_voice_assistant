import asyncio
from typing import List
from langchain.agents import Tool
from langchain_community.agent_toolkits import PlayWrightBrowserToolkit
from playwright.async_api import async_playwright  
import nest_asyncio

nest_asyncio.apply()


class BrowserToolFactory:
    def __init__(self):
        self.async_browser = None
        self.toolkit = None
        self._initialized = False

    async def initialize(self):
        """Initialize the browser asynchronously with real Chrome."""
        if not self._initialized:
            p = await async_playwright().start()

            self.async_browser = await p.chromium.launch(
                headless=False,
                executable_path="C:/Program Files/Google/Chrome/Application/chrome.exe" 
            )

            self.toolkit = PlayWrightBrowserToolkit.from_browser(
                async_browser=self.async_browser
            )
            self._initialized = True

    async def create_tools(self) -> List[Tool]:
        """Create browser tools asynchronously."""
        if not self._initialized:
            await self.initialize()
        return self.toolkit.get_tools()


_browser_factory = BrowserToolFactory()

browser_tools = asyncio.run(_browser_factory.create_tools())
