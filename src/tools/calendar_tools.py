from langchain_google_community import CalendarToolkit
from langchain_google_community.calendar.utils import (
    build_resource_service,
    get_google_credentials,
)
from langchain.agents import Tool
from typing import List

from src.config.settings import settings

class CalendarToolsFactory:
    def __init__(self):
        self.credentials = get_google_credentials(
            token_file=settings.token_file,
            scopes=[
                "https://www.googleapis.com/auth/calendar",
                "https://www.googleapis.com/auth/calendar.events",
                "https://www.googleapis.com/auth/calendar.readonly",
            ],
            client_secrets_file=settings.credentials_file,
        )
    def create_tools(self) -> List[Tool]:
        api_resource = build_resource_service(credentials=self.credentials)
        toolkit = CalendarToolkit(api_resource=api_resource)
        return toolkit.get_tools()

calendar_tools=CalendarToolsFactory().create_tools()



