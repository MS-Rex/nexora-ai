"""
DateTime utilities for the Nexora AI system.

These utilities provide date and time information. The datetime context is now automatically
provided in agent message context, so tool registration is no longer needed.

The standalone DateTimeTools class is still available for direct API access or testing.
"""

from typing import Dict, Any, Optional
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)


class DateTimeTools:
    """
    Standalone datetime tools that can be used without PydanticAI agents.
    Useful for testing, direct API access, or anywhere datetime info is needed.
    
    All datetime operations default to Sri Lanka (Asia/Colombo) timezone.
    
    Note: For PydanticAI agents, datetime context is automatically provided
    in the message context, so these tools are not needed as agent tools.
    """

    @staticmethod
    def get_current_datetime_direct(
        timezone_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Direct datetime fetching without PydanticAI context."""
        try:
            # Default to Sri Lanka (Colombo) timezone if none specified
            if timezone_name is None:
                timezone_name = "Asia/Colombo"
            
            if timezone_name:
                try:
                    import zoneinfo

                    tz = zoneinfo.ZoneInfo(timezone_name)
                    current_dt = datetime.now(tz)
                except Exception:
                    # Fallback to Sri Lanka timezone, then UTC if that fails
                    try:
                        import zoneinfo
                        tz = zoneinfo.ZoneInfo("Asia/Colombo")
                        current_dt = datetime.now(tz)
                    except Exception:
                        current_dt = datetime.now(timezone.utc)
            else:
                # This shouldn't happen now, but keeping as fallback
                try:
                    import zoneinfo
                    tz = zoneinfo.ZoneInfo("Asia/Colombo")
                    current_dt = datetime.now(tz)
                except Exception:
                    current_dt = datetime.now()

            return {
                "timestamp": current_dt.isoformat(),
                "datetime_local": current_dt.strftime("%Y-%m-%d %H:%M:%S"),
                "date": current_dt.strftime("%Y-%m-%d"),
                "time": current_dt.strftime("%H:%M:%S"),
                "day_of_week": current_dt.strftime("%A"),
                "month": current_dt.strftime("%B"),
                "year": current_dt.year,
                "timezone": str(current_dt.tzinfo) if current_dt.tzinfo else "Asia/Colombo",
                "formatted_readable": current_dt.strftime("%A, %B %d, %Y at %I:%M %p"),
                "unix_timestamp": int(current_dt.timestamp()),
                "success": True,
            }
        except Exception as e:
            return {
                "error": f"Failed to get current datetime: {str(e)}",
                "success": False,
            }

    @staticmethod
    def get_date_info_direct(target_date: Optional[str] = None) -> Dict[str, Any]:
        """Direct date info fetching without PydanticAI context."""
        try:
            if target_date:
                try:
                    dt = datetime.strptime(target_date, "%Y-%m-%d")
                    # Convert to Sri Lanka timezone for consistency
                    try:
                        import zoneinfo
                        tz = zoneinfo.ZoneInfo("Asia/Colombo")
                        dt = dt.replace(tzinfo=tz)
                    except Exception:
                        pass
                except ValueError:
                    return {
                        "error": "Invalid date format. Please use YYYY-MM-DD format.",
                        "success": False,
                    }
            else:
                # Use Sri Lanka timezone as default
                try:
                    import zoneinfo
                    tz = zoneinfo.ZoneInfo("Asia/Colombo")
                    dt = datetime.now(tz)
                except Exception:
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
                "success": True,
            }
        except Exception as e:
            return {
                "error": f"Failed to get date information: {str(e)}",
                "success": False,
            }

    @staticmethod
    def get_time_info_direct(include_timezone: bool = True) -> Dict[str, Any]:
        """Direct time info fetching without PydanticAI context."""
        try:
            # Use Sri Lanka timezone as default
            try:
                import zoneinfo
                tz = zoneinfo.ZoneInfo("Asia/Colombo")
                current_dt = datetime.now(tz)
            except Exception:
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
                "success": True,
            }

            if include_timezone:
                utc_time = datetime.now(timezone.utc)
                result.update(
                    {
                        "timezone_local": str(current_dt.tzinfo) if current_dt.tzinfo else "Asia/Colombo",
                        "utc_time": utc_time.strftime("%H:%M:%S UTC"),
                        "utc_timestamp": utc_time.isoformat(),
                        "colombo_time": current_dt.strftime("%H:%M:%S %Z"),
                    }
                )

            return result
        except Exception as e:
            return {
                "error": f"Failed to get time information: {str(e)}",
                "success": False,
            }
