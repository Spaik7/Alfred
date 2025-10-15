#!/usr/bin/env python3
"""
Transport Functions for Alfred - Traffic and Transit Information
Requires Google Maps API or other transport APIs
"""

import requests
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime, timedelta
import time as time_module

# Import from config.py
try:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from config import GOOGLE_MAPS_API_KEY, DEFAULT_LOCATION
except ImportError:
    GOOGLE_MAPS_API_KEY = None
    DEFAULT_LOCATION = "Santhia, Italy"

def parse_time_to_timestamp(time_str: str) -> int:
    """
    Parse time string to Unix timestamp for arrival_time

    Args:
        time_str: Time string like "8am", "14:30", "3:45 pm"

    Returns:
        Unix timestamp for today at that time
    """
    try:
        time_str = time_str.strip().lower()

        # Handle formats: "8am", "8 am", "8:30am", "8:30 am", "14:30"
        is_pm = 'pm' in time_str
        is_am = 'am' in time_str
        time_str = time_str.replace('am', '').replace('pm', '').strip()

        # Parse hour and minute
        if ':' in time_str:
            parts = time_str.split(':')
            hour = int(parts[0])
            minute = int(parts[1])
        else:
            hour = int(time_str)
            minute = 0

        # Convert to 24-hour format
        if is_pm and hour != 12:
            hour += 12
        elif is_am and hour == 12:
            hour = 0

        # Create datetime for today at specified time
        now = datetime.now()
        target_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

        # If time is in the past, assume tomorrow
        if target_time < now:
            target_time += timedelta(days=1)

        # Convert to Unix timestamp
        return int(target_time.timestamp())

    except Exception as e:
        # If parsing fails, return timestamp for 1 hour from now
        return int((datetime.now() + timedelta(hours=1)).timestamp())

def get_travel_time(origin: str, destination: str, mode: str = "driving") -> dict:
    """
    Get travel time between two locations

    Args:
        origin: Starting location
        destination: Destination location
        mode: Travel mode (driving, walking, bicycling, transit)

    Returns:
        dict with travel time information
    """
    if not GOOGLE_MAPS_API_KEY:
        return {
            "success": False,
            "error": "Google Maps API key not configured"
        }

    try:
        response = requests.get(
            "https://maps.googleapis.com/maps/api/directions/json",
            params={
                "origin": origin,
                "destination": destination,
                "mode": mode,
                "key": GOOGLE_MAPS_API_KEY
            },
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()

            if data["status"] == "OK" and data["routes"]:
                route = data["routes"][0]
                leg = route["legs"][0]

                return {
                    "success": True,
                    "origin": leg["start_address"],
                    "destination": leg["end_address"],
                    "distance": leg["distance"]["text"],
                    "distance_meters": leg["distance"]["value"],
                    "duration": leg["duration"]["text"],
                    "duration_seconds": leg["duration"]["value"],
                    "mode": mode
                }
            else:
                return {
                    "success": False,
                    "error": f"API error: {data.get('status', 'Unknown error')}"
                }

        return {
            "success": False,
            "error": f"HTTP {response.status_code}"
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def get_traffic_status(origin: str, destination: str, arrival_time: str = None) -> dict:
    """
    Get current traffic status between two locations

    Args:
        origin: Starting location (uses DEFAULT_LOCATION if None)
        destination: Destination location
        arrival_time: Optional arrival time string (e.g., "8am", "14:30")

    Returns:
        dict with traffic information including departure time if arrival_time specified
    """
    if not GOOGLE_MAPS_API_KEY:
        return {
            "success": False,
            "error": "Google Maps API key not configured"
        }

    # Use default location if origin is None
    if origin is None:
        origin = DEFAULT_LOCATION

    try:
        # NOTE: Google Maps API does NOT support arrival_time for driving mode
        # We always use departure_time="now" and calculate manually
        api_params = {
            "origin": origin,
            "destination": destination,
            "mode": "driving",
            "departure_time": "now",
            "traffic_model": "best_guess",
            "key": GOOGLE_MAPS_API_KEY
        }

        response = requests.get(
            "https://maps.googleapis.com/maps/api/directions/json",
            params=api_params,
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()

            if data["status"] == "OK" and data["routes"]:
                route = data["routes"][0]
                leg = route["legs"][0]

                # Duration in traffic vs normal duration
                duration_in_traffic = leg.get("duration_in_traffic", leg["duration"])
                normal_duration = leg["duration"]

                delay_seconds = duration_in_traffic["value"] - normal_duration["value"]
                delay_minutes = delay_seconds // 60

                traffic_status = "light" if delay_minutes < 5 else "moderate" if delay_minutes < 15 else "heavy"

                # Calculate departure time if arrival_time was specified
                departure_time_text = None
                if arrival_time:
                    # Calculate when to leave to arrive by the specified time
                    # We get current traffic duration, subtract from desired arrival time
                    arrival_timestamp = parse_time_to_timestamp(arrival_time)
                    duration_seconds = duration_in_traffic["value"]
                    departure_timestamp = arrival_timestamp - duration_seconds
                    departure_dt = datetime.fromtimestamp(departure_timestamp)
                    # Format time nicely (e.g., "11:45 AM" or "9:30 AM")
                    departure_time_text = departure_dt.strftime("%I:%M %p").lstrip('0').replace(' 0', ' ')

                return {
                    "success": True,
                    "origin": leg["start_address"],
                    "destination": leg["end_address"],
                    "distance_text": leg["distance"]["text"],
                    "distance": leg["distance"]["text"],
                    "normal_duration": normal_duration["text"],
                    "current_duration": duration_in_traffic["text"],
                    "duration_text": duration_in_traffic["text"],  # Alias for compatibility
                    "delay_minutes": max(0, delay_minutes),
                    "traffic_status": traffic_status,
                    "departure_time": departure_time_text,  # When to leave (if arrival_time specified)
                    "arrival_time_requested": arrival_time  # What user requested
                }
            else:
                return {
                    "success": False,
                    "error": f"API error: {data.get('status', 'Unknown error')}"
                }

        return {
            "success": False,
            "error": f"HTTP {response.status_code}"
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def get_public_transit(origin: str, destination: str, arrival_time: str = None) -> dict:
    """
    Get public transit directions

    Args:
        origin: Starting location (uses DEFAULT_LOCATION if None)
        destination: Destination location
        arrival_time: Optional arrival time string (e.g., "8am", "14:30")

    Returns:
        dict with transit information including departure time
    """
    if not GOOGLE_MAPS_API_KEY:
        return {
            "success": False,
            "error": "Google Maps API key not configured"
        }

    # Use default location if origin is None
    if origin is None:
        origin = DEFAULT_LOCATION

    try:
        # Build API parameters
        api_params = {
            "origin": origin,
            "destination": destination,
            "mode": "transit",
            "key": GOOGLE_MAPS_API_KEY
        }

        # Use arrival_time if provided, otherwise departure_time=now
        if arrival_time:
            timestamp = parse_time_to_timestamp(arrival_time)
            api_params["arrival_time"] = timestamp
        else:
            api_params["departure_time"] = "now"

        response = requests.get(
            "https://maps.googleapis.com/maps/api/directions/json",
            params=api_params,
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()

            if data["status"] == "OK" and data["routes"]:
                route = data["routes"][0]
                leg = route["legs"][0]

                # Extract transit steps and get first departure time
                transit_steps = []
                first_departure_time = None

                for step in leg["steps"]:
                    if step["travel_mode"] == "TRANSIT":
                        transit = step["transit_details"]

                        # Capture first departure time
                        if first_departure_time is None:
                            first_departure_time = transit["departure_time"]["text"]

                        transit_steps.append({
                            "line": transit["line"]["short_name"],
                            "vehicle": transit["line"]["vehicle"]["type"],
                            "departure_stop": transit["departure_stop"]["name"],
                            "arrival_stop": transit["arrival_stop"]["name"],
                            "departure_time": transit["departure_time"]["text"],
                            "arrival_time": transit["arrival_time"]["text"],
                            "num_stops": transit["num_stops"]
                        })

                return {
                    "success": True,
                    "origin": leg["start_address"],
                    "destination": leg["end_address"],
                    "distance": leg["distance"]["text"],
                    "distance_text": leg["distance"]["text"],  # Alias for compatibility
                    "duration": leg["duration"]["text"],
                    "duration_text": leg["duration"]["text"],  # Alias for compatibility
                    "departure_time": first_departure_time,  # When to leave
                    "arrival_time_requested": arrival_time,  # What user requested
                    "transit_steps": transit_steps
                }
            else:
                return {
                    "success": False,
                    "error": f"API error: {data.get('status', 'No transit available')}"
                }

        return {
            "success": False,
            "error": f"HTTP {response.status_code}"
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


if __name__ == '__main__':
    # Test functions
    print("Transport Functions Test\n" + "="*50)

    if not GOOGLE_MAPS_API_KEY:
        print("\nGOOGLE_MAPS_API_KEY not set!")
        print("Get your API key at: https://console.cloud.google.com/")
        print("Then set it: export GOOGLE_MAPS_API_KEY='your_key_here'")
    else:
        print("\n1. Travel Time (Driving):")
        travel = get_travel_time("Turin", "Milan", mode="driving")
        if travel["success"]:
            print(f"   From: {travel['origin']}")
            print(f"   To: {travel['destination']}")
            print(f"   Distance: {travel['distance']}")
            print(f"   Duration: {travel['duration']}")

        print("\n2. Traffic Status:")
        traffic = get_traffic_status("Turin", "Milan")
        if traffic["success"]:
            print(f"   Distance: {traffic['distance']}")
            print(f"   Normal: {traffic['normal_duration']}")
            print(f"   Current: {traffic['current_duration']}")
            print(f"   Traffic: {traffic['traffic_status']}")

        print("\n3. Public Transit:")
        transit = get_public_transit("Turin", "Milan")
        if transit["success"]:
            print(f"   Duration: {transit['duration']}")
            print(f"   Steps: {len(transit['transit_steps'])} transit segments")
