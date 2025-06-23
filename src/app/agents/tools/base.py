"""
Base classes and utilities for PydanticAI tools.

This module provides common functionality and patterns for creating tools
that can be used across different agents in the Nexora AI system.
"""

from typing import Protocol, Dict, Any, Optional
import httpx
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from src.app.core.config.settings import settings

logger = logging.getLogger(__name__)


def generate_datetime_context(timezone_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Generate comprehensive datetime context information.

    Args:
        timezone_name: Optional timezone name (e.g., 'UTC', 'America/New_York').
                      Defaults to system local timezone.

    Returns:
        Comprehensive datetime information in various formats
    """
    try:
        # Get current datetime
        if timezone_name:
            try:
                import zoneinfo

                tz = zoneinfo.ZoneInfo(timezone_name)
                current_dt = datetime.now(tz)
            except Exception:
                # Fallback to UTC if timezone parsing fails
                current_dt = datetime.now(timezone.utc)
                logger.warning(f"Invalid timezone '{timezone_name}', using UTC instead")
        else:
            # Use local timezone
            current_dt = datetime.now()

        # Calculate additional date information
        day_of_year = current_dt.timetuple().tm_yday
        week_number = current_dt.isocalendar()[1]
        is_weekend = current_dt.weekday() >= 5  # Saturday = 5, Sunday = 6

        # Format in multiple ways
        datetime_context = {
            "timestamp": current_dt.isoformat(),
            "datetime_local": current_dt.strftime("%Y-%m-%d %H:%M:%S"),
            "date": current_dt.strftime("%Y-%m-%d"),
            "time": current_dt.strftime("%H:%M:%S"),
            "time_12h": current_dt.strftime("%I:%M:%S %p"),
            "day_of_week": current_dt.strftime("%A"),
            "day_of_week_number": current_dt.weekday() + 1,  # Monday = 1, Sunday = 7
            "month": current_dt.strftime("%B"),
            "month_number": current_dt.month,
            "year": current_dt.year,
            "day_of_month": current_dt.day,
            "day_of_year": day_of_year,
            "week_number": week_number,
            "is_weekend": is_weekend,
            "hour_24": current_dt.hour,
            "hour_12": int(current_dt.strftime("%I")),
            "minute": current_dt.minute,
            "second": current_dt.second,
            "am_pm": current_dt.strftime("%p"),
            "timezone": str(current_dt.tzinfo) if current_dt.tzinfo else "Local",
            "formatted_readable": current_dt.strftime("%A, %B %d, %Y at %I:%M %p"),
            "formatted_short": current_dt.strftime("%m/%d/%Y"),
            "unix_timestamp": int(current_dt.timestamp()),
        }

        # Add UTC information if not already in UTC
        if current_dt.tzinfo != timezone.utc:
            utc_time = datetime.now(timezone.utc)
            datetime_context.update(
                {
                    "utc_time": utc_time.strftime("%H:%M:%S UTC"),
                    "utc_timestamp": utc_time.isoformat(),
                    "utc_date": utc_time.strftime("%Y-%m-%d"),
                }
            )

        logger.debug(
            f"Generated datetime context: {datetime_context['datetime_local']}"
        )
        return datetime_context

    except Exception as e:
        logger.error(f"Error generating datetime context: {str(e)}")
        return {
            "error": f"Failed to generate datetime context: {str(e)}",
            "datetime_local": "Unknown",
            "date": "Unknown",
            "time": "Unknown",
        }


def format_datetime_context_for_prompt(datetime_context: Dict[str, Any]) -> str:
    """
    Format datetime context for inclusion in agent prompts.

    Args:
        datetime_context: Datetime context dictionary from generate_datetime_context()

    Returns:
        Formatted string suitable for agent context
    """
    if "error" in datetime_context:
        return f"**Current DateTime:** {datetime_context.get('error', 'Unknown error')}"

    context_lines = [
        "**CURRENT DATE & TIME CONTEXT:**",
        f"📅 **Date:** {datetime_context['formatted_readable']}",
        f"🕒 **Time:** {datetime_context['time_12h']} ({datetime_context['time']} 24h format)",
        f"📍 **Timezone:** {datetime_context['timezone']}",
        f"📊 **Details:** Day {datetime_context['day_of_year']} of {datetime_context['year']}, Week {datetime_context['week_number']}",
        f"🗓️ **Day Type:** {'Weekend' if datetime_context['is_weekend'] else 'Weekday'}",
        "",
        "**Available DateTime Formats:**",
        f"- ISO Timestamp: {datetime_context['timestamp']}",
        f"- Short Date: {datetime_context['formatted_short']}",
        f"- Unix Timestamp: {datetime_context['unix_timestamp']}",
    ]

    # Add UTC info if available
    if "utc_time" in datetime_context:
        context_lines.extend(
            [
                f"- UTC Time: {datetime_context['utc_time']}",
                f"- UTC Date: {datetime_context['utc_date']}",
            ]
        )

    context_lines.append("---")
    return "\n".join(context_lines)


@dataclass
class ToolDependencies:
    """Common dependencies that tools might need."""

    http_client: httpx.AsyncClient
    base_api_url: str = settings.BASE_URL
    # Datetime context is automatically generated and included
    datetime_context: Dict[str, Any] = field(
        default_factory=lambda: generate_datetime_context()
    )


class ToolError(Exception):
    """Base exception for tool-related errors."""

    pass


class HTTPToolError(ToolError):
    """Exception for HTTP-related tool errors."""

    pass


class Tool(Protocol):
    """Protocol for defining tools that can be used by agents."""

    async def execute(self, dependencies: ToolDependencies, **kwargs) -> Dict[str, Any]:
        """Execute the tool with given dependencies and parameters."""
        ...


async def handle_http_request(
    client: httpx.AsyncClient, url: str, method: str = "GET", **kwargs
) -> Dict[str, Any]:
    """
    Common HTTP request handler with error handling.

    Args:
        client: HTTP client to use
        url: URL to request
        method: HTTP method (GET, POST, etc.)
        **kwargs: Additional arguments passed to the HTTP client

    Returns:
        Response data or error information
    """
    try:
        logger.info(f"Making {method} request to: {url}")

        if method.upper() == "GET":
            response = await client.get(url, **kwargs)
        elif method.upper() == "POST":
            response = await client.post(url, **kwargs)
        else:
            raise HTTPToolError(f"Unsupported HTTP method: {method}")

        response.raise_for_status()
        data = response.json()

        logger.info(f"Successfully received response from {url}")
        return {"data": data, "success": True}

    except httpx.HTTPError as e:
        logger.error(f"HTTP error for {url}: {str(e)}")
        return {"error": f"HTTP request failed: {str(e)}", "success": False}
    except Exception as e:
        logger.error(f"Unexpected error for {url}: {str(e)}")
        return {"error": f"Unexpected error: {str(e)}", "success": False}
