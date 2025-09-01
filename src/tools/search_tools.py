import asyncio
import aiohttp
from typing import List
from langchain.agents import Tool
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_community.tools.wikipedia.tool import WikipediaQueryRun
from langchain_community.utilities.wikipedia import WikipediaAPIWrapper
from src.config.settings import settings
from langchain_community.utilities import OpenWeatherMapAPIWrapper

class SearchToolFactory:
    def __init__(self):
        self.serper = GoogleSerperAPIWrapper()
        self.wikipedia = WikipediaAPIWrapper()
        self.wiki_tool = WikipediaQueryRun(api_wrapper=self.wikipedia)
        self.weather = OpenWeatherMapAPIWrapper()

    async def search_news_async(self, query: str):
        try:
            url = f"https://newsapi.org/v2/everything"
            params = {
                "q": query,
                "sortBy": "publishedAt",
                "apiKey": settings.news_api_key,
                "pageSize": 10
            }
            
            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, params=params) as response:
                    response.raise_for_status()
                    data = await response.json()

                    if data["status"] == "ok":
                        articles = data["articles"]
                        if not articles:
                            return f"No news articles found for '{query}'"

                        news_summary = f"Found {len(articles)} news articles for '{query}':\n\n"

                        for i, article in enumerate(articles[:10], 1):
                            title = article.get("title", "No title")
                            description = article.get("description", "No description")
                            url_link = article.get("url", "")
                            published_at = article.get("publishedAt", "Unknown date")

                            news_summary += f"{i}. {title}\n"
                            news_summary += f"   Published: {published_at}\n"
                            news_summary += f"   Description: {description}\n"
                            news_summary += f"   URL: {url_link}\n\n"

                        return news_summary
                    else:
                        return f"Error: {data.get('message', 'Unknown error occurred')}"

        except aiohttp.ClientError as e:
            return f"Network error: {str(e)}"
        except Exception as e:
            return f"Error searching news: {str(e)}"

    def search_news(self, query: str):
        try:
            loop = asyncio.get_running_loop()
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, self.search_news_async(query))
                return future.result()
        except RuntimeError:
            return asyncio.run(self.search_news_async(query))

    async def create_tools(self) -> List[Tool]:
        return [
            Tool(
                name="search_internet",
                func=lambda query: asyncio.run(asyncio.to_thread(self.serper.run, query)),
                description="""Search the internet for current information and general queries.

USE FOR: General web searches, current information, recent developments, product searches
KEYWORDS: search, find, look up, current, recent, latest information, what's new
INPUT: Search query with key terms

EXAMPLES:
- "find recent studies on climate change" → search_internet("recent climate change studies")
- "best laptops 2024" → search_internet("best laptops 2024")
- "current AI developments" → search_internet("AI developments 2024")

Provides comprehensive web search results from multiple sources.""",
            ),
            Tool(
                name="wikipedia_search", 
                func=lambda query: asyncio.run(asyncio.to_thread(self.wiki_tool.run, query)),
                description="""Search Wikipedia for factual, educational, and encyclopedic information.

USE FOR: Factual knowledge, definitions, historical information, educational content
KEYWORDS: what is, who is, explain, define, history of, facts about, learn about
INPUT: Topic or concept to research

EXAMPLES:
- "what is quantum computing" → wikipedia_search("quantum computing")
- "history of Ancient Rome" → wikipedia_search("Ancient Rome history")
- "explain photosynthesis" → wikipedia_search("photosynthesis")

Provides detailed, reliable information from Wikipedia encyclopedia.""",
            ),
            Tool(
                name="news_search",
                func=self.search_news,
                description="""Search for current news articles and breaking news.

USE FOR: Current events, breaking news, recent headlines, news updates
KEYWORDS: news, breaking, headlines, current events, latest news, today's news
INPUT: News topic or event

EXAMPLES:
- "latest AI news" → news_search("artificial intelligence news")
- "breaking news today" → news_search("breaking news")
- "election updates" → news_search("election news")

Returns recent news articles with titles, descriptions, publication dates, and URLs.""",
            ),
            Tool(
                name="weather",
                func=lambda query: asyncio.run(asyncio.to_thread(self.weather.run, query)),
                description="""Get weather information and forecasts for specific locations.

USE FOR: Weather conditions, forecasts, temperature, climate information
KEYWORDS: weather, temperature, forecast, rain, sunny, cloudy, climate, conditions
INPUT: Location name (city, region, or coordinates)

EXAMPLES:
- "weather in New York" → weather("New York")
- "San Francisco forecast" → weather("San Francisco")
- "tomorrow's weather" → weather("[current location]")

Provides current conditions, temperature, humidity, and forecast information."""
            )
        ]

    
_search_factory = SearchToolFactory()

search_tools = asyncio.run(_search_factory.create_tools())