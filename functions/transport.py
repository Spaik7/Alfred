#!/usr/bin/env python3
"""
Transport Functions for Alfred - Traffic and Transit Information
Requires Google Maps API or other transport APIs
"""

import requests
import sys
from pathlib import Path
from typing import Optional

# Import from config.py
try:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from config import GOOGLE_MAPS_API_KEY
except ImportError:
    GOOGLE_MAPS_API_KEY = None

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


def get_traffic_status(origin: str, destination: str) -> dict:
    """
    Get current traffic status between two locations

    Args:
        origin: Starting location
        destination: Destination location

    Returns:
        dict with traffic information
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
                "mode": "driving",
                "departure_time": "now",
                "traffic_model": "best_guess",
                "key": GOOGLE_MAPS_API_KEY
            },
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

                return {
                    "success": True,
                    "origin": leg["start_address"],
                    "destination": leg["end_address"],
                    "distance": leg["distance"]["text"],
                    "normal_duration": normal_duration["text"],
                    "current_duration": duration_in_traffic["text"],
                    "delay_minutes": max(0, delay_minutes),
                    "traffic_status": traffic_status
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


def get_public_transit(origin: str, destination: str) -> dict:
    """
    Get public transit directions

    Args:
        origin: Starting location
        destination: Destination location

    Returns:
        dict with transit information
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
                "mode": "transit",
                "departure_time": "now",
                "key": GOOGLE_MAPS_API_KEY
            },
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()

            if data["status"] == "OK" and data["routes"]:
                route = data["routes"][0]
                leg = route["legs"][0]

                # Extract transit steps
                transit_steps = []
                for step in leg["steps"]:
                    if step["travel_mode"] == "TRANSIT":
                        transit = step["transit_details"]
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
                    "duration": leg["duration"]["text"],
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
