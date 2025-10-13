#!/usr/bin/env python3
"""
System Monitoring Functions for Alfred - Raspberry Pi Status
"""

import psutil
import subprocess

def get_cpu_usage() -> dict:
    """
    Get CPU usage statistics

    Returns:
        dict with CPU information
    """
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        cpu_freq = psutil.cpu_freq()

        return {
            "success": True,
            "usage_percent": cpu_percent,
            "core_count": cpu_count,
            "frequency_mhz": cpu_freq.current if cpu_freq else None,
            "max_frequency_mhz": cpu_freq.max if cpu_freq else None
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def get_memory_usage() -> dict:
    """
    Get memory usage statistics

    Returns:
        dict with memory information
    """
    try:
        memory = psutil.virtual_memory()

        return {
            "success": True,
            "total_gb": round(memory.total / (1024**3), 2),
            "used_gb": round(memory.used / (1024**3), 2),
            "available_gb": round(memory.available / (1024**3), 2),
            "usage_percent": memory.percent
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def get_disk_usage() -> dict:
    """
    Get disk usage statistics

    Returns:
        dict with disk information
    """
    try:
        disk = psutil.disk_usage('/')

        return {
            "success": True,
            "total_gb": round(disk.total / (1024**3), 2),
            "used_gb": round(disk.used / (1024**3), 2),
            "free_gb": round(disk.free / (1024**3), 2),
            "usage_percent": disk.percent
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def get_temperature() -> dict:
    """
    Get Raspberry Pi temperature

    Returns:
        dict with temperature information
    """
    try:
        # Try to get CPU temperature from vcgencmd (Raspberry Pi specific)
        result = subprocess.run(
            ['vcgencmd', 'measure_temp'],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode == 0:
            # Output format: "temp=45.0'C"
            temp_str = result.stdout.strip()
            temp_c = float(temp_str.split('=')[1].split("'")[0])
            temp_f = (temp_c * 9/5) + 32

            return {
                "success": True,
                "celsius": round(temp_c, 1),
                "fahrenheit": round(temp_f, 1)
            }
        else:
            # Fallback: try psutil sensors (may not work on all systems)
            temps = psutil.sensors_temperatures()
            if temps:
                # Try to find CPU temp
                for name, entries in temps.items():
                    if entries:
                        temp_c = entries[0].current
                        temp_f = (temp_c * 9/5) + 32
                        return {
                            "success": True,
                            "celsius": round(temp_c, 1),
                            "fahrenheit": round(temp_f, 1)
                        }

            return {
                "success": False,
                "error": "Temperature sensor not available"
            }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def get_system_status() -> dict:
    """
    Get comprehensive system status

    Returns:
        dict with all system information
    """
    cpu = get_cpu_usage()
    memory = get_memory_usage()
    disk = get_disk_usage()
    temperature = get_temperature()

    return {
        "success": True,
        "cpu": cpu,
        "memory": memory,
        "disk": disk,
        "temperature": temperature
    }


def get_uptime() -> dict:
    """
    Get system uptime

    Returns:
        dict with uptime information
    """
    try:
        boot_time = psutil.boot_time()
        uptime_seconds = psutil.time.time() - boot_time

        days = int(uptime_seconds // 86400)
        hours = int((uptime_seconds % 86400) // 3600)
        minutes = int((uptime_seconds % 3600) // 60)

        return {
            "success": True,
            "uptime_seconds": int(uptime_seconds),
            "days": days,
            "hours": hours,
            "minutes": minutes,
            "formatted": f"{days}d {hours}h {minutes}m"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


if __name__ == '__main__':
    # Test functions
    print("System Monitoring Test\n" + "="*50)

    print("\n1. CPU Usage:")
    cpu = get_cpu_usage()
    if cpu["success"]:
        print(f"   Usage: {cpu['usage_percent']}%")
        print(f"   Cores: {cpu['core_count']}")
        if cpu['frequency_mhz']:
            print(f"   Frequency: {cpu['frequency_mhz']} MHz")

    print("\n2. Memory Usage:")
    memory = get_memory_usage()
    if memory["success"]:
        print(f"   Total: {memory['total_gb']} GB")
        print(f"   Used: {memory['used_gb']} GB")
        print(f"   Usage: {memory['usage_percent']}%")

    print("\n3. Disk Usage:")
    disk = get_disk_usage()
    if disk["success"]:
        print(f"   Total: {disk['total_gb']} GB")
        print(f"   Used: {disk['used_gb']} GB")
        print(f"   Usage: {disk['usage_percent']}%")

    print("\n4. Temperature:")
    temp = get_temperature()
    if temp["success"]:
        print(f"   Temp: {temp['celsius']}C / {temp['fahrenheit']}F")

    print("\n5. Uptime:")
    uptime = get_uptime()
    if uptime["success"]:
        print(f"   Uptime: {uptime['formatted']}")

    print("\n6. Full System Status:")
    status = get_system_status()
    print(f"   All systems: {'OK' if status['success'] else 'ERROR'}")
