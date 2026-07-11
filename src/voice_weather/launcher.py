"""macOS window launcher for the interactive application."""

import platform
import shlex
import subprocess
import sys

from .app import main as app_main

APPLESCRIPT = r'''
on run argv
    set launchCommand to item 1 of argv
    tell application "Terminal"
        activate
        set weatherTab to do script launchCommand
        repeat while busy of weatherTab
            delay 0.2
        end repeat
        delay 0.2
        try
            close (window of weatherTab)
        end try
    end tell
end run
'''


def launch_window() -> int:
    command = f"clear; exec {shlex.quote(sys.executable)} -m voice_weather"
    result = subprocess.run(["osascript", "-e", APPLESCRIPT, "--", command], check=False)
    return result.returncode


def main() -> int:
    # Parameters are intentionally kept in the caller's terminal for scripting.
    if len(sys.argv) > 1 or platform.system() != "Darwin":
        return app_main()
    return launch_window()
