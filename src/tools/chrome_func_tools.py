from typing import List
from langchain.agents import Tool
import time
from src.services.selenium_service import seleniumservice
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class ChromeFuncToolFactory:
    def __init__(self):
        pass

    def scroll_page(self, steps):
        step_height = steps.get("step_height", 500)
        pause = steps.get("pause", 0.3)
        direction = steps.get("direction", "down")
        steps = int(steps.get("steps", 1))

        driver = seleniumservice.chrome_driver()
        if direction.lower() == "up":
            step_height = -abs(step_height)
        else:
            step_height = abs(step_height)

        for _ in range(steps):
            driver.execute_script(f"window.scrollBy(0, {step_height});")
            time.sleep(pause)

        return f"Scrolled {steps} steps {direction} by {abs(step_height)}px each"

    def open_page(self, url: str):
        driver = seleniumservice.chrome_driver()
        driver.implicitly_wait(10)
        try:
            driver.get(url=url)
            return f"Open '{url}' success"
        except Exception as e:
            return f"Error Occurred: {e}"

    def create_tools(self) -> List[Tool]:
        """Create and return all Selenium tools for agent usage with detailed descriptions."""
        return [
            Tool(
                name="scroll_page",
                func=self.scroll_page,
                description="""Scroll the webpage up or down in steps.
                Input: steps, step_height, pause, direction
                Example: "steps": 3, "step_height": 400, "direction": "down"
                Notes: 'direction' can be 'up' or 'down'.""",
            ),
            Tool(
                name="open_page",
                func=self.open_page,
                description=""" Opens a URL in the current Chrome tab.

        Parameters:
        - url (str): Full URL of the webpage to open

        Returns:
        - Success message if the page loads, else error message

        Example usage:
        open_page("https://www.google.com/")
        open_page("https://www.youtube.com/results?search_query=songs")

        Notes:
        - The page in the current tab will be replaced by the new URL.
        - After opening a page, you can interact with elements using other tools like click_on_page or form_fill.""",
            ),
        ]


_chrome_func_factory = ChromeFuncToolFactory()
chrome_func_tools = _chrome_func_factory.create_tools()
