from selenium import webdriver

from selenium.common.exceptions import WebDriverException, InvalidSessionIdException


class SeleniumService:
    def __init__(self):
        self.chrome = None

    def create_chrome(self):
        options = webdriver.ChromeOptions()
        options.add_experimental_option("detach", True)
        options.add_argument("--log-level=3")
        options.add_argument("--silent")
        options.add_argument("--disable-logging")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        options.add_experimental_option("useAutomationExtension", False)
        return webdriver.Chrome(options=options)

    def chrome_driver(self, files_mode: bool = False):
        """Ensure we have a valid WebDriver session, create new one if needed"""
        path="file:///C://" if files_mode else "https://www.google.com/"
        try:
            if not self.chrome:
                self.chrome = self.create_chrome()
                self.chrome.get(path)
                return self.chrome
            self.chrome.current_url
        except:
            self.chrome.quit()
            self.chrome = self.create_chrome()
            self.chrome.get(path)

        return self.chrome


seleniumservice = SeleniumService()
