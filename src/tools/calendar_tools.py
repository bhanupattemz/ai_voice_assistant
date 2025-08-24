import asyncio
import os
from langchain_google_community import CalendarToolkit
from langchain_google_community.calendar.utils import (
    build_resource_service,
    get_google_credentials,
)
from langchain.agents import Tool
from typing import List, Optional
import logging

from src.config.settings import settings

logger = logging.getLogger(__name__)

class CalendarToolsFactory:
    def __init__(self):
        self.credentials = None
        self.api_resource = None
        self._initialized = False
        self._tools = None
    
    async def initialize(self):
        """Initialize credentials and API resource asynchronously."""
        if self._initialized:
            return
            
        try:
            if not os.path.exists(settings.credentials_file):
                logger.error(f"Google credentials file not found: {settings.credentials_file}")
                raise FileNotFoundError(f"Google credentials file not found: {settings.credentials_file}")
            
            self.credentials = await asyncio.to_thread(
                get_google_credentials,
                token_file=settings.token_file,
                scopes=[
                    "https://www.googleapis.com/auth/calendar",
                    "https://www.googleapis.com/auth/calendar.events",
                    "https://www.googleapis.com/auth/calendar.readonly",
                ],
                client_secrets_file=settings.credentials_file,
            )
            
            if not self.credentials:
                raise ValueError("Failed to obtain Google credentials")
            
            self.api_resource = await asyncio.to_thread(
                build_resource_service, 
                credentials=self.credentials
            )
            
            if not self.api_resource:
                raise ValueError("Failed to build Google Calendar API resource")
            
            self._initialized = True
            logger.info("Google Calendar integration initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Google Calendar: {str(e)}")
            self._initialized = False
            raise
    
    async def create_tools(self) -> List[Tool]:
        """Create calendar tools asynchronously with error handling."""
        try:
            if not self._initialized:
                await self.initialize()
            
            if self._tools is not None:
                return self._tools
            
            toolkit = CalendarToolkit(api_resource=self.api_resource)
            tools = toolkit.get_tools()
            
            enhanced_tools = []
            
            for tool in tools:
                if tool.name == "calendar_search_events":
                    enhanced_tools.append(Tool(
                        name=tool.name,
                        func=tool.func,
                        description="""Search for events in Google Calendar.

USE FOR: Finding existing meetings, appointments, or events
KEYWORDS: check, find, show, list, what meetings, any events, schedule for, busy, free
INPUT: Search query with date range or keywords

EXAMPLES:
- "what meetings do I have tomorrow" → calendar_search_events("tomorrow")
- "check my schedule for next week" → calendar_search_events("next week")
- "any events today" → calendar_search_events("today")
- "find meeting with John" → calendar_search_events("John")

Returns detailed information about matching calendar events."""
                    ))
                
                elif tool.name == "calendar_create_event":
                    enhanced_tools.append(Tool(
                        name=tool.name,
                        func=tool.func,
                        description="""Create new events in Google Calendar.

USE FOR: Scheduling new meetings, appointments, or events
KEYWORDS: schedule, create, add, book, set up, plan, meeting with, appointment
INPUT: Event details including title, date, time, duration, location

REQUIRED PARAMETERS:
- title: Event name/subject
- date: Event date (YYYY-MM-DD format)
- start_time: Start time (HH:MM format)
- end_time: End time (optional, defaults to 1 hour later)

OPTIONAL PARAMETERS:
- location: Meeting location or address
- description: Additional event details

EXAMPLES:
- "schedule meeting with John tomorrow 3 PM" → create event with extracted details
- "book dentist appointment Friday 10 AM" → create appointment event

Creates new calendar event and returns confirmation."""
                    ))
                
                elif tool.name == "calendar_update_event":
                    enhanced_tools.append(Tool(
                        name=tool.name,
                        func=tool.func,
                        description="""Update existing events in Google Calendar.

USE FOR: Modifying existing meetings, appointments, or events
KEYWORDS: change, modify, update, reschedule, move, edit
INPUT: Event identifier and new details

EXAMPLES:
- "move my 2 PM meeting to 3 PM" → update event time
- "change meeting location to conference room" → update event location
- "reschedule dentist appointment to next week" → update event date

Updates specified calendar event and returns confirmation."""
                    ))
                
                elif tool.name == "calendar_delete_event":
                    enhanced_tools.append(Tool(
                        name=tool.name,
                        func=tool.func,
                        description="""Delete events from Google Calendar.

USE FOR: Canceling or removing meetings, appointments, or events
KEYWORDS: cancel, delete, remove, clear
INPUT: Event identifier or search criteria

EXAMPLES:
- "cancel my meeting with John" → delete specific meeting
- "remove dentist appointment" → delete appointment
- "clear my 3 PM meeting" → delete meeting at specific time

Deletes specified calendar event and returns confirmation."""
                    ))
                
                else:
                    enhanced_tools.append(tool)
            
            self._tools = enhanced_tools
            logger.info(f"Created {len(enhanced_tools)} calendar tools")
            return enhanced_tools
            
        except Exception as e:
            logger.error(f"Failed to create calendar tools: {str(e)}")
            return []

    async def get_tools_safe(self) -> List[Tool]:
        """Get calendar tools safely with fallback."""
        try:
            return await self.create_tools()
        except Exception as e:
            logger.warning(f"Calendar tools unavailable: {str(e)}")
            return []
_calendar_factory = CalendarToolsFactory()

async def get_calendar_tools():
    """Get calendar tools asynchronously."""
    return await _calendar_factory.get_tools_safe()

try:
    calendar_tools = asyncio.run(_calendar_factory.create_tools())
except Exception as e:
    logger.error(f"Failed to initialize calendar tools: {str(e)}")
    calendar_tools = []