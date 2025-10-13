#!/usr/bin/env python3
"""
Time and Date Functions for Alfred
"""

from datetime import datetime
import pytz

def get_time(timezone: str = "Europe/Rome") -> dict:
    """
    Get current time

    Args:
        timezone: Timezone string (default: Europe/Rome for Italy)

    Returns:
        dict with time information
    """
    try:
        tz = pytz.timezone(timezone)
        now = datetime.now(tz)

        return {
            "success": True,
            "time": now.strftime("%H:%M"),
            "time_12h": now.strftime("%I:%M %p"),
            "hour": now.hour,
            "minute": now.minute,
            "timezone": timezone
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def get_date(timezone: str = "Europe/Rome") -> dict:
    """
    Get current date

    Args:
        timezone: Timezone string (default: Europe/Rome for Italy)

    Returns:
        dict with date information
    """
    try:
        tz = pytz.timezone(timezone)
        now = datetime.now(tz)

        # Day names in English and Italian
        days_en = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        days_it = ["Lunedi", "Martedi", "Mercoledi", "Giovedi", "Venerdi", "Sabato", "Domenica"]

        # Month names in English and Italian
        months_en = ["January", "February", "March", "April", "May", "June",
                     "July", "August", "September", "October", "November", "December"]
        months_it = ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
                     "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]

        return {
            "success": True,
            "date": now.strftime("%Y-%m-%d"),
            "date_formatted": now.strftime("%B %d, %Y"),
            "day": now.day,
            "month": now.month,
            "year": now.year,
            "weekday": days_en[now.weekday()],
            "weekday_it": days_it[now.weekday()],
            "month_name": months_en[now.month - 1],
            "month_name_it": months_it[now.month - 1],
            "timezone": timezone
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def get_datetime(timezone: str = "Europe/Rome") -> dict:
    """
    Get current date and time together

    Args:
        timezone: Timezone string (default: Europe/Rome for Italy)

    Returns:
        dict with datetime information
    """
    time_data = get_time(timezone)
    date_data = get_date(timezone)

    if time_data["success"] and date_data["success"]:
        return {
            "success": True,
            **time_data,
            **date_data
        }
    else:
        return {
            "success": False,
            "error": "Failed to get datetime"
        }


if __name__ == '__main__':
    # Test functions
    print("Time & Date Functions Test\n" + "="*50)

    print("\n1. Current Time:")
    time_data = get_time()
    if time_data["success"]:
        print(f"   24h: {time_data['time']}")
        print(f"   12h: {time_data['time_12h']}")

    print("\n2. Current Date:")
    date_data = get_date()
    if date_data["success"]:
        print(f"   Date: {date_data['date_formatted']}")
        print(f"   Weekday: {date_data['weekday']} / {date_data['weekday_it']}")
        print(f"   Month: {date_data['month_name']} / {date_data['month_name_it']}")

    print("\n3. Combined DateTime:")
    dt_data = get_datetime()
    if dt_data["success"]:
        print(f"   {dt_data['weekday']}, {dt_data['date_formatted']} at {dt_data['time']}")
