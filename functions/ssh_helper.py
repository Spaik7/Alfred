"""
SSH Helper Module for Alfred - Phase 2 Mac Integration

This module provides SSH connectivity between:
- Mac -> Raspberry Pi (uses sshpass with password authentication)
- Pi -> Mac (uses expect for keyboard-interactive authentication)

Configuration:
Set the following environment variables in your .env file:
- SSH_PI_HOST: Raspberry Pi IP address
- SSH_PI_USER: Raspberry Pi username
- SSH_PI_PASSWORD: Raspberry Pi password
- SSH_MAC_HOST: Mac IP address
- SSH_MAC_USER: Mac username
- SSH_MAC_PASSWORD: Mac password

Usage from Alfred (running on Pi):
    helper = get_ssh_helper()
    result = helper.execute_on_mac("osascript -e 'tell application \"Mail\" to get name of every account'")
"""

import subprocess
import logging
from typing import Dict, Any, Optional, List
import tempfile
import os

logger = logging.getLogger(__name__)

class SSHHelper:
    """
    SSH helper for executing commands on Mac from Raspberry Pi.
    Uses expect scripts for reliable keyboard-interactive authentication.
    """

    def __init__(self):
        # Load SSH credentials from environment variables
        mac_user = os.getenv("SSH_MAC_USER", "user")
        mac_host = os.getenv("SSH_MAC_HOST", "192.168.1.5")
        self.mac_host = f"{mac_user}@{mac_host}"
        self.mac_password = os.getenv("SSH_MAC_PASSWORD", "password")

        pi_user = os.getenv("SSH_PI_USER", "pi")
        pi_host = os.getenv("SSH_PI_HOST", "192.168.1.9")
        self.pi_host = f"{pi_user}@{pi_host}"
        self.pi_password = os.getenv("SSH_PI_PASSWORD", "password")

        self.timeout = 30  # seconds

        # Check if running on Pi or Mac
        self.running_on_pi = self._is_running_on_pi()

        if self.running_on_pi:
            logger.info("[SSH] SSH Helper initialized (running on Pi)")
        else:
            logger.info("[SSH] SSH Helper initialized (running on Mac)")

    def _is_running_on_pi(self) -> bool:
        """Detect if we're running on Raspberry Pi"""
        try:
            result = subprocess.run(
                ['uname', '-n'],
                capture_output=True,
                text=True,
                timeout=5
            )
            hostname = result.stdout.strip()
            return 'rkiran' in hostname.lower() or 'raspberrypi' in hostname.lower()
        except Exception as e:
            logger.warning(f"Could not detect hostname: {e}")
            return False

    def execute_on_mac(self, command: str, timeout: Optional[int] = None) -> Dict[str, Any]:
        """
        Execute a shell command on the Mac.

        Args:
            command: The shell command to execute on Mac
            timeout: Optional timeout in seconds (default: 30)

        Returns:
            Dict with keys:
                - success: bool
                - stdout: str
                - stderr: str
                - exit_code: int
        """
        if not self.running_on_pi:
            # If we're already on Mac, just run locally
            return self._execute_local(command, timeout)

        # Running on Pi - SSH to Mac
        timeout = timeout or self.timeout

        try:
            # Create expect script for keyboard-interactive authentication
            expect_script = self._create_expect_script(command)

            # Execute the expect script
            result = subprocess.run(
                ['expect', '-'],
                input=expect_script,
                capture_output=True,
                text=True,
                timeout=timeout
            )

            # Parse output
            stdout = result.stdout
            stderr = result.stderr
            exit_code = result.returncode

            # Remove expect-specific output
            stdout = self._clean_expect_output(stdout)

            success = exit_code == 0

            if success:
                logger.debug(f"[SSH] Mac command succeeded: {command[:50]}...")
            else:
                logger.warning(f"[ERR] Mac command failed (exit {exit_code}): {command[:50]}...")

            return {
                'success': success,
                'stdout': stdout,
                'stderr': stderr,
                'exit_code': exit_code
            }

        except subprocess.TimeoutExpired:
            logger.error(f"[TIME] Mac command timed out after {timeout}s: {command[:50]}...")
            return {
                'success': False,
                'stdout': '',
                'stderr': f'Command timed out after {timeout} seconds',
                'exit_code': -1
            }
        except Exception as e:
            logger.error(f"[ERR] Error executing Mac command: {e}")
            return {
                'success': False,
                'stdout': '',
                'stderr': str(e),
                'exit_code': -1
            }

    def execute_applescript(self, script: str, timeout: Optional[int] = None) -> Dict[str, Any]:
        """
        Execute AppleScript on the Mac.

        Args:
            script: AppleScript code to execute
            timeout: Optional timeout in seconds (default: 30)

        Returns:
            Dict with keys:
                - success: bool
                - result: str (AppleScript output)
                - error: str
        """
        # Escape single quotes in the script
        escaped_script = script.replace("'", "'\"'\"'")

        # Build osascript command
        command = f"osascript -e '{escaped_script}'"

        result = self.execute_on_mac(command, timeout)

        return {
            'success': result['success'],
            'result': result['stdout'].strip(),
            'error': result['stderr']
        }

    def execute_applescript_file(self, script_lines: List[str], timeout: Optional[int] = None) -> Dict[str, Any]:
        """
        Execute multi-line AppleScript on the Mac.
        Useful for complex scripts with multiple lines.

        Args:
            script_lines: List of AppleScript lines
            timeout: Optional timeout in seconds (default: 30)

        Returns:
            Dict with keys:
                - success: bool
                - result: str (AppleScript output)
                - error: str
        """
        # Build osascript command with multiple -e flags
        command_parts = ['osascript']
        for line in script_lines:
            escaped_line = line.replace("'", "'\"'\"'")
            command_parts.append(f"-e '{escaped_line}'")

        command = ' '.join(command_parts)
        result = self.execute_on_mac(command, timeout)

        return {
            'success': result['success'],
            'result': result['stdout'].strip(),
            'error': result['stderr']
        }

    def _create_expect_script(self, command: str) -> str:
        """
        Create an expect script for SSH authentication.

        Args:
            command: The command to execute on the remote host

        Returns:
            Complete expect script as string
        """
        # Escape special characters for expect
        escaped_command = command.replace('\\', '\\\\').replace('"', '\\"').replace('$', '\\$')
        escaped_password = self.mac_password.replace('\\', '\\\\').replace('"', '\\"')

        script = f"""#!/usr/bin/expect -f
set timeout {self.timeout}

# Spawn SSH connection
spawn ssh -o StrictHostKeyChecking=no {self.mac_host} "{escaped_command}"

# Handle password prompt
expect {{
    "password:" {{
        send "{escaped_password}\\r"
        expect eof
    }}
    "Password:" {{
        send "{escaped_password}\\r"
        expect eof
    }}
    eof {{
        # Command completed without password prompt (key auth worked)
    }}
    timeout {{
        puts "ERROR: SSH connection timed out"
        exit 1
    }}
}}

# Capture exit status
catch wait result
set exit_code [lindex $result 3]
exit $exit_code
"""
        return script

    def _clean_expect_output(self, output: str) -> str:
        """
        Remove expect-specific output and SSH prompts from the result.

        Args:
            output: Raw output from expect script

        Returns:
            Cleaned output
        """
        lines = output.split('\n')
        cleaned_lines = []

        for line in lines:
            # Skip expect control lines
            if line.startswith('spawn '):
                continue
            if 'password:' in line.lower():
                continue
            if line.strip().startswith('ERROR:'):
                continue

            cleaned_lines.append(line)

        return '\n'.join(cleaned_lines).strip()

    def _execute_local(self, command: str, timeout: Optional[int] = None) -> Dict[str, Any]:
        """
        Execute a command locally (used when already on Mac).

        Args:
            command: Shell command to execute
            timeout: Optional timeout in seconds

        Returns:
            Dict with execution results
        """
        timeout = timeout or self.timeout

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout
            )

            return {
                'success': result.returncode == 0,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'exit_code': result.returncode
            }

        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'stdout': '',
                'stderr': f'Command timed out after {timeout} seconds',
                'exit_code': -1
            }
        except Exception as e:
            return {
                'success': False,
                'stdout': '',
                'stderr': str(e),
                'exit_code': -1
            }

    def test_connection(self) -> bool:
        """
        Test SSH connection to Mac.

        Returns:
            True if connection successful, False otherwise
        """
        logger.info("[TEST] Testing SSH connection to Mac...")

        result = self.execute_on_mac("echo 'SSH test successful' && hostname")

        if result['success']:
            hostname = result['stdout'].strip().split('\n')[-1]
            logger.info(f" SSH connection successful to {hostname}")
            return True
        else:
            logger.error(f"[ERR] SSH connection failed: {result['stderr']}")
            return False


# Singleton instance
_ssh_helper_instance: Optional[SSHHelper] = None

def get_ssh_helper() -> SSHHelper:
    """
    Get the singleton SSH helper instance.

    Returns:
        SSHHelper instance
    """
    global _ssh_helper_instance

    if _ssh_helper_instance is None:
        _ssh_helper_instance = SSHHelper()

    return _ssh_helper_instance


# Convenience functions for common operations

def check_mail() -> Dict[str, Any]:
    """
    Check Apple Mail for unread messages.

    Returns:
        Dict with mail information
    """
    helper = get_ssh_helper()

    script_lines = [
        'tell application "Mail"',
        'set unreadCount to count of (messages of inbox whose read status is false)',
        'return unreadCount',
        'end tell'
    ]

    result = helper.execute_applescript_file(script_lines)

    if result['success']:
        try:
            unread_count = int(result['result'])
            return {
                'success': True,
                'unread_count': unread_count
            }
        except ValueError:
            return {
                'success': False,
                'error': f"Could not parse unread count: {result['result']}"
            }
    else:
        return {
            'success': False,
            'error': result['error']
        }


def get_recent_emails(count: int = 5) -> Dict[str, Any]:
    """
    Get recent emails from Apple Mail inbox.

    Args:
        count: Number of recent emails to retrieve (default: 5, max: 20)

    Returns:
        Dict with keys:
            - success: bool
            - emails: List[Dict] with keys: number, sender, subject, date, is_read
            - count: int (number of emails returned)
            - error: str (if failed)
    """
    helper = get_ssh_helper()

    # Limit count to reasonable range
    count = max(1, min(count, 20))

    # AppleScript to get recent emails from inbox
    script_lines = [
        'tell application "Mail"',
        '    set recentMessages to messages of inbox',
        f'    set emailCount to count of recentMessages',
        f'    if emailCount > {count} then',
        f'        set emailCount to {count}',
        '    end if',
        '    ',
        '    set emailList to ""',
        '    repeat with i from 1 to emailCount',
        '        set msg to item i of recentMessages',
        '        set msgSender to sender of msg',
        '        set msgSubject to subject of msg',
        '        set msgDate to date received of msg',
        '        set msgRead to read status of msg',
        '        ',
        '        -- Format: number|sender|subject|date|read_status',
        '        set emailList to emailList & i & "|" & msgSender & "|" & msgSubject & "|" & (msgDate as string) & "|" & msgRead & "\\n"',
        '    end repeat',
        '    ',
        '    return emailList',
        'end tell'
    ]

    result = helper.execute_applescript_file(script_lines)

    if result['success']:
        try:
            output = result['result'].strip()
            if not output:
                return {
                    'success': True,
                    'emails': [],
                    'count': 0
                }

            emails = []
            lines = output.split('\\n')

            for line in lines:
                if not line.strip():
                    continue

                parts = line.split('|')
                if len(parts) >= 5:
                    emails.append({
                        'number': int(parts[0]),
                        'sender': parts[1].strip(),
                        'subject': parts[2].strip(),
                        'date': parts[3].strip(),
                        'is_read': parts[4].strip().lower() == 'true'
                    })

            return {
                'success': True,
                'emails': emails,
                'count': len(emails)
            }

        except Exception as e:
            logger.error(f"[ERR] Failed to parse email list: {e}")
            return {
                'success': False,
                'error': f"Failed to parse email list: {str(e)}"
            }
    else:
        return {
            'success': False,
            'error': result.get('error', 'Unknown error')
        }


def get_calendar_events_for_date(date_offset: int = 0) -> Dict[str, Any]:
    """
    Get calendar events for a specific date relative to today.

    Args:
        date_offset: Days from today (0=today, -1=yesterday, 1=tomorrow)

    Returns:
        Dict with keys:
            - success: bool
            - count: int (number of events)
            - calendar_name: str (name of calendar checked)
            - date: str (date checked)
    """
    helper = get_ssh_helper()

    # AppleScript to get events for specific date - handles recurring events
    # Strategy: Get non-recurring events in target date range, plus ALL recurring events to check manually
    script_lines = [
        'tell application "Calendar"',
        '    set targetDate to (current date)',
        '    set hours of targetDate to 0',
        '    set minutes of targetDate to 0',
        '    set seconds of targetDate to 0',
        f'    set targetDate to targetDate + ({date_offset} * days)',
        '    set endDate to targetDate + (1 * days)',
        '    ',
        '    set targetDay to day of targetDate',
        '    set targetMonth to month of targetDate',
        '    set targetYear to year of targetDate',
        '    set targetDateStr to short date string of targetDate',
        '    ',
        '    set eventCount to 0',
        '    set eventDetails to ""',
        '    ',
        '    repeat with cal in calendars',
        '        try',
        '            -- Strategy: Check events in two passes',
        '            -- Pass 1: Get ALL events in target date range first',
        '            set allEventsInRange to (every event of cal whose start date >= targetDate and start date < endDate)',
        '            repeat with evt in allEventsInRange',
        '                try',
        '                    set evtRecurs to recurrence of evt',
        '                    if evtRecurs is missing value then',
        '                        -- Non-recurring event, add it',
        '                        set eventCount to eventCount + 1',
        '                        set eventDetails to eventDetails & (summary of evt) & " (" & (name of cal) & "), "',
        '                    end if',
        '                end try',
        '            end repeat',
        '            ',
        '            -- Pass 2: Recurring events - limit search to avoid timeout',
        '            -- Only check events that started within past year (catches yearly/weekly/monthly)',
        '            set searchWindow to targetDate - (400 * days)',
        '            set recurringEvents to (every event of cal whose recurrence is not missing value and start date >= searchWindow)',
        '            repeat with evt in recurringEvents',
        '                try',
        '                    set evtStart to start date of evt',
        '                    set evtRecurs to recurrence of evt',
        '                    set matchesDate to false',
        '                    ',
        '                    if evtRecurs contains "FREQ=YEARLY" then',
        '                        -- Check if same day and month',
        '                        if (day of evtStart) = targetDay and (month of evtStart) = targetMonth then',
        '                            -- Make sure event started before or on target year',
        '                            if (year of evtStart) <= targetYear then',
        '                                set matchesDate to true',
        '                            end if',
        '                        end if',
        '                    else if evtRecurs contains "FREQ=WEEKLY" then',
        '                        -- Check if target date is the same day of week AND N weeks after start',
        '                        set targetDayOfWeek to weekday of targetDate',
        '                        set eventDayOfWeek to weekday of evtStart',
        '                        -- Check if same day of week',
        '                        if targetDayOfWeek = eventDayOfWeek then',
        '                            set daysDiff to (((targetDate - evtStart) / days) as integer)',
        '                            -- Must be exact multiple of 7 days apart and after start',
        '                            if daysDiff >= 0 and (daysDiff mod 7) = 0 then',
        '                                -- Check UNTIL date if present',
        '                                set hasEnded to false',
        '                                if evtRecurs contains "UNTIL=" then',
        '                                    -- Event has end date, check if target is before it',
        '                                    -- For now, assume it matches (full UNTIL parsing is complex)',
        '                                    set matchesDate to true',
        '                                else',
        '                                    -- No end date, matches',
        '                                    set matchesDate to true',
        '                                end if',
        '                            end if',
        '                        end if',
        '                    else if evtRecurs contains "FREQ=DAILY" then',
        '                        -- Daily events: check if target is after start',
        '                        if targetDate >= evtStart then',
        '                            set matchesDate to true',
        '                        end if',
        '                    end if',
        '                    ',
        '                    if matchesDate then',
        '                        set eventCount to eventCount + 1',
        '                        set eventDetails to eventDetails & (summary of evt) & " (" & (name of cal) & "), "',
        '                    end if',
        '                end try',
        '            end repeat',
        '            ',
        '            -- Pass 3: Check yearly recurring events outside our 400-day window',
        '            -- These are typically birthdays that started many years ago',
        '            set veryOldYearlyEvents to (every event of cal whose recurrence contains "FREQ=YEARLY" and start date < searchWindow)',
        '            repeat with evt in veryOldYearlyEvents',
        '                try',
        '                    set evtStart to start date of evt',
        '                    -- Check if same day and month as target',
        '                    if (day of evtStart) = targetDay and (month of evtStart) = targetMonth then',
        '                        -- Make sure event started before or on target year',
        '                        if (year of evtStart) <= targetYear then',
        '                            set eventCount to eventCount + 1',
        '                            set eventDetails to eventDetails & (summary of evt) & " (" & (name of cal) & "), "',
        '                        end if',
        '                    end if',
        '                end try',
        '            end repeat',
        '        end try',
        '    end repeat',
        '    ',
        '    set calCount to count of calendars',
        '    return (eventCount as string) & "|" & (calCount as string) & " calendars|" & targetDateStr & "|" & eventDetails',
        'end tell'
    ]

    result = helper.execute_applescript_file(script_lines)

    if result['success']:
        output = result['result']
        if '|' in output:
            parts = output.split('|')
            count = int(parts[0])
            calendar_name = parts[1] if len(parts) > 1 else "Calendar"
            date_checked = parts[2] if len(parts) > 2 else "unknown"
            event_details = parts[3] if len(parts) > 3 else ""

            # Determine date label
            if date_offset == 0:
                date_label = "today"
            elif date_offset == -1:
                date_label = "yesterday"
            elif date_offset == 1:
                date_label = "tomorrow"
            else:
                date_label = f"{abs(date_offset)} days {'ago' if date_offset < 0 else 'from now'}"

            # Log debug info
            logger.info(f"[CALENDAR DEBUG] Checked date: {date_checked}, Found: {count} events")
            if event_details:
                logger.info(f"[CALENDAR DEBUG] Events: {event_details}")

            return {
                'success': True,
                'count': count,
                'calendar_name': calendar_name,
                'date': date_label,
                'debug_date': date_checked,
                'debug_events': event_details
            }
        else:
            return {
                'success': False,
                'error': 'Invalid response format'
            }
    else:
        return {
            'success': False,
            'error': result.get('error', str(result))
        }


def get_calendar_events_today() -> Dict[str, Any]:
    """
    Get today's calendar events from Apple Calendar.

    Returns:
        Dict with keys:
            - success: bool
            - count: int (number of events)
            - calendar_name: str (name of calendar checked)
            - date: str (always "today")
    """
    return get_calendar_events_for_date(0)


def get_calendar_events_yesterday() -> Dict[str, Any]:
    """
    Get yesterday's calendar events from Apple Calendar.

    Returns:
        Dict with keys:
            - success: bool
            - count: int (number of events)
            - calendar_name: str (name of calendar checked)
            - date: str (always "yesterday")
    """
    return get_calendar_events_for_date(-1)


def get_calendar_events_tomorrow() -> Dict[str, Any]:
    """
    Get tomorrow's calendar events from Apple Calendar.

    Returns:
        Dict with keys:
            - success: bool
            - count: int (number of events)
            - calendar_name: str (name of calendar checked)
            - date: str (always "tomorrow")
    """
    return get_calendar_events_for_date(1)


def get_calendar_events_specific(calendar_name: str, date_offset: int = 0) -> Dict[str, Any]:
    """
    Get calendar events from a specific calendar by name.

    Args:
        calendar_name: Name of the calendar to check (e.g., "Casa", "Lavoro", "Google")
        date_offset: Days from today (0=today, -1=yesterday, 1=tomorrow)

    Returns:
        Dict with keys:
            - success: bool
            - count: int (number of events)
            - calendar_name: str (name of calendar checked)
            - date: str (date checked)
            - found: bool (whether the calendar was found)
    """
    helper = get_ssh_helper()

    # AppleScript to get events from specific calendar
    # Escape calendar name for AppleScript
    escaped_name = calendar_name.replace('"', '\\"')

    script_lines = [
        'tell application "Calendar"',
        '    set targetDate to (current date)',
        '    set hours of targetDate to 0',
        '    set minutes of targetDate to 0',
        '    set seconds of targetDate to 0',
        f'    set targetDate to targetDate + ({date_offset} * days)',
        '    set endDate to targetDate + (1 * days)',
        '    set eventCount to 0',
        '    set calendarFound to false',
        '    set actualCalName to ""',
        '    repeat with cal in calendars',
        f'        if name of cal contains "{escaped_name}" then',
        '            set calendarFound to true',
        '            set actualCalName to name of cal',
        '            set calEvents to (every event of cal whose start date >= targetDate and start date < endDate)',
        '            set eventCount to eventCount + (count of calEvents)',
        '        end if',
        '    end repeat',
        '    if calendarFound then',
        '        return (eventCount as string) & "|" & actualCalName & "|found"',
        '    else',
        '        return "0|not found|notfound"',
        '    end if',
        'end tell'
    ]

    result = helper.execute_applescript_file(script_lines)

    if result['success']:
        output = result['result']
        if '|' in output:
            parts = output.split('|')
            if len(parts) >= 3:
                if parts[2] == 'notfound':
                    return {
                        'success': False,
                        'found': False,
                        'error': f'Calendar "{calendar_name}" not found',
                        'calendar_name': calendar_name
                    }
                else:
                    count = int(parts[0])
                    actual_cal_name = parts[1]

                    # Determine date label
                    if date_offset == 0:
                        date_label = "today"
                    elif date_offset == -1:
                        date_label = "yesterday"
                    elif date_offset == 1:
                        date_label = "tomorrow"
                    else:
                        date_label = f"{abs(date_offset)} days {'ago' if date_offset < 0 else 'from now'}"

                    return {
                        'success': True,
                        'found': True,
                        'count': count,
                        'calendar_name': actual_cal_name,
                        'date': date_label
                    }

        return {
            'success': False,
            'error': 'Invalid response format'
        }
    else:
        return {
            'success': False,
            'error': result['error']
        }
