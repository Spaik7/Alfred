#!/usr/bin/env python3
"""
Volume Control for Alfred - Controls Pi speaker volume
"""

import subprocess
import re

class VolumeController:
    """Control local Pi speaker volume using amixer"""

    def __init__(self, control='PCM'):
        """
        Initialize volume controller

        Args:
            control: ALSA control name (default: PCM for Pi)
        """
        self.control = control
        self.min_vol = 0
        self.max_vol = 255  # Pi PCM range is 0-255

    def get_current_volume(self) -> int:
        """
        Get current volume level (0-100 percentage)

        Returns:
            Current volume as percentage (0-100)
        """
        try:
            result = subprocess.run(
                ['amixer', 'get', self.control],
                capture_output=True,
                text=True,
                check=True
            )

            # Parse output like: "Mono: Playback 192 [75%] [on]"
            match = re.search(r'Playback (\d+) \[(\d+)%\]', result.stdout)
            if match:
                return int(match.group(2))  # Return percentage
            return 50  # Default fallback

        except subprocess.CalledProcessError:
            return 50  # Default fallback

    def set_volume(self, level: int) -> bool:
        """
        Set volume to specific level

        Args:
            level: Volume level (0-100)

        Returns:
            True if successful
        """
        # Clamp to 0-100
        level = max(0, min(100, level))

        try:
            subprocess.run(
                ['amixer', 'set', self.control, f'{level}%'],
                capture_output=True,
                check=True
            )
            return True
        except subprocess.CalledProcessError:
            return False

    def increase_volume(self, amount: int = 10) -> int:
        """
        Increase volume by amount

        Args:
            amount: Amount to increase (default: 10)

        Returns:
            New volume level
        """
        current = self.get_current_volume()
        new_level = min(100, current + amount)
        self.set_volume(new_level)
        return new_level

    def decrease_volume(self, amount: int = 10) -> int:
        """
        Decrease volume by amount

        Args:
            amount: Amount to decrease (default: 10)

        Returns:
            New volume level
        """
        current = self.get_current_volume()
        new_level = max(0, current - amount)
        self.set_volume(new_level)
        return new_level

    def mute(self) -> bool:
        """
        Mute the volume

        Returns:
            True if successful
        """
        return self.set_volume(0)


# Singleton instance
_controller = None

def get_controller() -> VolumeController:
    """Get singleton volume controller instance"""
    global _controller
    if _controller is None:
        _controller = VolumeController()
    return _controller


# Convenience functions
def set_volume(level: int) -> bool:
    """Set volume to specific level (0-100)"""
    return get_controller().set_volume(level)

def increase_volume(amount: int = 10) -> int:
    """Increase volume by amount (default 10)"""
    return get_controller().increase_volume(amount)

def decrease_volume(amount: int = 10) -> int:
    """Decrease volume by amount (default 10)"""
    return get_controller().decrease_volume(amount)

def get_current_volume() -> int:
    """Get current volume level (0-100)"""
    return get_controller().get_current_volume()

def mute() -> bool:
    """Mute the volume"""
    return get_controller().mute()


if __name__ == '__main__':
    # Test volume control
    controller = VolumeController()

    print("Testing Volume Control")
    print("=" * 40)

    current = controller.get_current_volume()
    print(f"Current volume: {current}%")

    print("\nIncreasing volume by 10...")
    new_vol = controller.increase_volume(10)
    print(f"New volume: {new_vol}%")

    print("\nDecreasing volume by 10...")
    new_vol = controller.decrease_volume(10)
    print(f"New volume: {new_vol}%")

    print("\nSetting volume to 50%...")
    controller.set_volume(50)
    current = controller.get_current_volume()
    print(f"Current volume: {current}%")
