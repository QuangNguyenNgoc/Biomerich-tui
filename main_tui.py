"""
SolRich_TUI entry point.

Usage:
    python main_tui.py
"""

import sys
import os

# Ensure the project root is in the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def _maybe_relaunch_deelevated():
    """If running as admin on Windows, relaunch without elevation."""
    if sys.platform != "win32":
        return
    if not getattr(sys, "frozen", False):
        return
    try:
        import ctypes

        if not ctypes.windll.shell32.IsUserAnAdmin():
            return
    except Exception:
        return
    try:
        import ctypes

        exe = sys.executable
        print(
            "[SolRich_TUI] Started as administrator — relaunching without "
            "elevation (admin isn't needed)."
        )
        ctypes.windll.shell32.ShellExecuteW(
            None, "open", "explorer.exe", f'"{exe}"', None, 1
        )
        sys.exit(0)
    except SystemExit:
        raise
    except Exception as e:
        print(f"[SolRich_TUI] Could not de-elevate ({e}); continuing as admin.")


if __name__ == "__main__":
    _maybe_relaunch_deelevated()

    from tui.app import SolRichTUI

    app = SolRichTUI()
    app.run()
