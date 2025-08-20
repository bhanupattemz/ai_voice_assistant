from typing import List
from langchain.agents import Tool
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_community.tools.wikipedia.tool import WikipediaQueryRun
from langchain_community.utilities.wikipedia import WikipediaAPIWrapper
import requests
from src.config.settings import settings
from langchain_community.utilities import OpenWeatherMapAPIWrapper
class SearchToolFactory:
    def __init__(self):
        self.serper = GoogleSerperAPIWrapper()
        self.wikipedia = WikipediaAPIWrapper()
        self.wiki_tool = WikipediaQueryRun(api_wrapper=self.wikipedia)
        self.weather = OpenWeatherMapAPIWrapper()

    def search_news(self, query: str):
        """This tool searches for news articles based on a query.
        It takes parameter: query (the search term for news)
        It returns news articles related to the query.
        important:Useful when User ask for news relatedly
        """
        try:
            url = f"https://newsapi.org/v2/everything?q={query}&sortBy=publishedAt&apiKey={settings.news_api_key}"
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()

            if data["status"] == "ok":
                articles = data["articles"]
                if not articles:
                    return f"No news articles found for '{query}'"

                news_summary = f"Found {len(articles)} news articles for '{query}':\n\n"

                for i, article in enumerate(articles[:10], 1):
                    title = article.get("title", "No title")
                    description = article.get("description", "No description")
                    url = article.get("url", "")
                    published_at = article.get("publishedAt", "Unknown date")

                    news_summary += f"{i}. {title}\n"
                    news_summary += f"   Published: {published_at}\n"
                    news_summary += f"   Description: {description}\n"
                    news_summary += f"   URL: {url}\n\n"

                return news_summary
            else:
                return f"Error: {data.get('message', 'Unknown error occurred')}"

        except requests.exceptions.RequestException as e:
            return f"Network error: {str(e)}"
        except Exception as e:
            return f"Error searching news: {str(e)}"

    def create_tools(self) -> List[Tool]:
        return [
            Tool(
                name="search_internet",
                func=self.serper.run,
                description="Search the internet for current information",
            ),
            self.wiki_tool,
            Tool(
                name="news_search",
                func=self.search_news,
                description="Search for news articles based on a query",
            ),
            Tool(
                name="weather",
                func=self.weather.run,
                description="Useful when user want to know the details related to weather"
            )
        ]

search_tools=SearchToolFactory().create_tools()