"""
DateTime-related tools for PydanticAI agents.

These tools provide real-time date and time information for agents that need
current temporal context.
"""

from typing import Dict, Any, Optional
from datetime import datetime, timezone
from pydantic_ai import Agent, RunContext
from src.app.agents.tools.base import ToolDependencies
import logging

logger = logging.getLogger(__name__)


def register_datetime_tools(agent: Agent, deps_type: type) -> None:
    """
    Register datetime-related tools with a PydanticAI agent.
    
    Args:
        agent: The PydanticAI agent to register tools with
        deps_type: The dependencies type that should include ToolDependencies
    """
    
    @agent.tool
    async def get_current_datetime(ctx: RunContext, timezone_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get the current date and time.
        
        Args:
            timezone_name: Optional timezone name (e.g., 'UTC', 'America/New_York'). 
                         Defaults to system local timezone.
            
        Returns:
            Current datetime information in various formats
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
            
            # Format in multiple ways
            result = {
                "timestamp": current_dt.isoformat(),
                "datetime_local": current_dt.strftime("%Y-%m-%d %H:%M:%S"),
                "date": current_dt.strftime("%Y-%m-%d"),
                "time": current_dt.strftime("%H:%M:%S"),
                "day_of_week": current_dt.strftime("%A"),
                "month": current_dt.strftime("%B"),
                "year": current_dt.year,
                "timezone": str(current_dt.tzinfo) if current_dt.tzinfo else "Local",
                "formatted_readable": current_dt.strftime("%A, %B %d, %Y at %I:%M %p"),
                "unix_timestamp": int(current_dt.timestamp()),
                "success": True
            }
            
            logger.info(f"Successfully retrieved current datetime: {result['datetime_local']}")
            return result
            
        except Exception as e:
            logger.error(f"Error getting current datetime: {str(e)}")
            return {"error": f"Failed to get current datetime: {str(e)}", "success": False}

    @agent.tool
    async def get_date_info(ctx: RunContext, target_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Get detailed information about a specific date or today.
        
        Args:
            target_date: Optional date string in YYYY-MM-DD format. 
                        If not provided, uses current date.
            
        Returns:
            Detailed information about the date
        """
        try:
            if target_date:
                try:
                    # Parse the provided date
                    dt = datetime.strptime(target_date, "%Y-%m-%d")
                except ValueError:
                    return {"error": "Invalid date format. Please use YYYY-MM-DD format.", "success": False}
            else:
                # Use current date
                dt = datetime.now()
            
            # Calculate additional date information
            day_of_year = dt.timetuple().tm_yday
            week_number = dt.isocalendar()[1]
            is_weekend = dt.weekday() >= 5  # Saturday = 5, Sunday = 6
            
            result = {
                "date": dt.strftime("%Y-%m-%d"),
                "day_of_week": dt.strftime("%A"),
                "day_of_week_number": dt.weekday() + 1,  # Monday = 1, Sunday = 7
                "month": dt.strftime("%B"),
                "month_number": dt.month,
                "year": dt.year,
                "day_of_month": dt.day,
                "day_of_year": day_of_year,
                "week_number": week_number,
                "is_weekend": is_weekend,
                "formatted_readable": dt.strftime("%A, %B %d, %Y"),
                "formatted_short": dt.strftime("%m/%d/%Y"),
                "success": True
            }
            
            logger.info(f"Successfully retrieved date info for: {result['date']}")
            return result
            
        except Exception as e:
            logger.error(f"Error getting date info: {str(e)}")
            return {"error": f"Failed to get date information: {str(e)}", "success": False}

    @agent.tool
    async def get_time_info(ctx: RunContext, include_timezone: bool = True) -> Dict[str, Any]:
        """
        Get detailed information about the current time.
        
        Args:
            include_timezone: Whether to include timezone information
            
        Returns:
            Detailed information about the current time
        """
        try:
            current_dt = datetime.now()
            
            # Format in various time formats
            result = {
                "time_24h": current_dt.strftime("%H:%M:%S"),
                "time_12h": current_dt.strftime("%I:%M:%S %p"),
                "hour_24": current_dt.hour,
                "hour_12": int(current_dt.strftime("%I")),
                "minute": current_dt.minute,
                "second": current_dt.second,
                "am_pm": current_dt.strftime("%p"),
                "time_formatted": current_dt.strftime("%I:%M %p"),
                "success": True
            }
            
            if include_timezone:
                utc_time = datetime.now(timezone.utc)
                result.update({
                    "timezone_local": str(current_dt.astimezone().tzinfo),
                    "utc_time": utc_time.strftime("%H:%M:%S UTC"),
                    "utc_timestamp": utc_time.isoformat()
                })
            
            logger.info(f"Successfully retrieved time info: {result['time_24h']}")
            return result
            
        except Exception as e:
            logger.error(f"Error getting time info: {str(e)}")
            return {"error": f"Failed to get time information: {str(e)}", "success": False}


class DateTimeTools:
    """
    Standalone datetime tools that can be used without PydanticAI agents.
    Useful for testing or direct API access.
    """
    
    @staticmethod
    def get_current_datetime_direct(timezone_name: Optional[str] = None) -> Dict[str, Any]:
        """Direct datetime fetching without PydanticAI context."""
        try:
            if timezone_name:
                try:
                    import zoneinfo
                    tz = zoneinfo.ZoneInfo(timezone_name)
                    current_dt = datetime.now(tz)
                except Exception:
                    current_dt = datetime.now(timezone.utc)
            else:
                current_dt = datetime.now()
            
            return {
                "timestamp": current_dt.isoformat(),
                "datetime_local": current_dt.strftime("%Y-%m-%d %H:%M:%S"),
                "date": current_dt.strftime("%Y-%m-%d"),
                "time": current_dt.strftime("%H:%M:%S"),
                "day_of_week": current_dt.strftime("%A"),
                "month": current_dt.strftime("%B"),
                "year": current_dt.year,
                "timezone": str(current_dt.tzinfo) if current_dt.tzinfo else "Local",
                "formatted_readable": current_dt.strftime("%A, %B %d, %Y at %I:%M %p"),
                "unix_timestamp": int(current_dt.timestamp()),
                "success": True
            }
        except Exception as e:
            return {"error": f"Failed to get current datetime: {str(e)}", "success": False}
    
    @staticmethod
    def get_date_info_direct(target_date: Optional[str] = None) -> Dict[str, Any]:
        """Direct date info fetching without PydanticAI context."""
        try:
            if target_date:
                try:
                    dt = datetime.strptime(target_date, "%Y-%m-%d")
                except ValueError:
                    return {"error": "Invalid date format. Please use YYYY-MM-DD format.", "success": False}
            else:
                dt = datetime.now()
            
            day_of_year = dt.timetuple().tm_yday
            week_number = dt.isocalendar()[1]
            is_weekend = dt.weekday() >= 5
            
            return {
                "date": dt.strftime("%Y-%m-%d"),
                "day_of_week": dt.strftime("%A"),
                "day_of_week_number": dt.weekday() + 1,
                "month": dt.strftime("%B"),
                "month_number": dt.month,
                "year": dt.year,
                "day_of_month": dt.day,
                "day_of_year": day_of_year,
                "week_number": week_number,
                "is_weekend": is_weekend,
                "formatted_readable": dt.strftime("%A, %B %d, %Y"),
                "formatted_short": dt.strftime("%m/%d/%Y"),
                "success": True
            }
        except Exception as e:
            return {"error": f"Failed to get date information: {str(e)}", "success": False}
    
    @staticmethod
    def get_time_info_direct(include_timezone: bool = True) -> Dict[str, Any]:
        """Direct time info fetching without PydanticAI context."""
        try:
            current_dt = datetime.now()
            
            result = {
                "time_24h": current_dt.strftime("%H:%M:%S"),
                "time_12h": current_dt.strftime("%I:%M:%S %p"),
                "hour_24": current_dt.hour,
                "hour_12": int(current_dt.strftime("%I")),
                "minute": current_dt.minute,
                "second": current_dt.second,
                "am_pm": current_dt.strftime("%p"),
                "time_formatted": current_dt.strftime("%I:%M %p"),
                "success": True
            }
            
            if include_timezone:
                utc_time = datetime.now(timezone.utc)
                result.update({
                    "timezone_local": str(current_dt.astimezone().tzinfo),
                    "utc_time": utc_time.strftime("%H:%M:%S UTC"),
                    "utc_timestamp": utc_time.isoformat()
                })
            
            return result
        except Exception as e:
            return {"error": f"Failed to get time information: {str(e)}", "success": False} 