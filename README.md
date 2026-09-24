# Biomerich TUI (SolRich Fork)

A refactored, terminal-native fork of the original SolRich (formerly Biomerich) project — a biome logger, Discord notifier, and automation tool for Roblox's Sol's RNG.

---

## 📌 About this Fork

This project is an open-source fork of the original SolRich / Biomerich codebase, created with the following goals:
- **Remove Bloated Web GUI**: Fully stripped out heavy web-based UI dependencies (Eel, WebView, and the NodeJS/React frontend) to drastically reduce memory footprint and background process bloat.
- **Native TUI Experience**: Built an interactive Terminal User Interface powered by **Textual** and **Rich**.
- **Resource Optimization**: Decreased RAM usage by over 30% and minimized CPU consumption, making it ideal for persistent, long-running sessions.
- **Streamlined Data Flow**: Refactored account management, configurations, and real-time state synchronization between the Macro Engine and the interface.

---

## 🚀 Getting Started (Terminal / CLI)

Biomerich TUI runs directly via Python inside your terminal (Windows Terminal, PowerShell, or Command Prompt).

### 1. Requirements
- **Operating System**: Windows 10 / 11 (64-bit)
- **Python**: Version **3.10 or newer** (Python **3.11** or **3.12** recommended)
- Standard user privileges (does not require running as Administrator).

### 2. Setting Up a Virtual Environment (Recommended)
Open your terminal in the project root directory and create a virtual environment:

```powershell
# Create the virtual environment
python -m venv .venv

# Activate on Windows PowerShell:
.venv\Scripts\Activate.ps1

# Or activate on Command Prompt (cmd):
.venv\Scripts\activate.bat
```

### 3. Installing Dependencies
Install the lightweight dependencies from `requirements.txt`:

```bash
pip install -r requirements.txt
```

> **Note on Text Reading (OCR):** Certain features like Merchant Detection and Auto Pop require Tesseract OCR to read on-screen text. If Tesseract is not installed on your system, the application can automatically download and set it up on demand.

### 4. Running the Application
Launch the TUI application directly from the project root:

```bash
python main_tui.py
```

---

## 🖥️ TUI Features Overview

The terminal interface organizes all tools into accessible tabs:
- **Dashboard**: Real-time status of the Macro Engine, online accounts, and active biomes.
- **Accounts**: Multi-account management, secure token storage, VIP server links, and module toggles.
- **Settings**: Global configurations, delays, and dynamic hotkey re-binding that applies instantly upon saving.
- **Automation / Modules**: Automation workflows including Auto Pop, Fishing, Merchant, and Eden mode.
- **Performance**: Background window throttling, CPU optimization, and automatic RAM trimming.
- **Logs & Timeline**: Live Activity Log, Event Log, and account duration timeline.
- **Webhooks**: Discord webhook configuration supporting modern Discord Components v2 layouts.

---

## 📜 License & Disclaimers

### 1. Source Code License
The source code for this fork is distributed and maintained under the open-source **[MIT License](LICENSE)**. You are free to use, modify, distribute, and contribute in accordance with the terms of the license.

### 2. Media & Image Assets Disclaimer
- All image assets, icons, GIFs, and thumbnails utilized across the application (such as webhook notifications, logos, and biome previews) were **randomly sourced from the internet** purely for personal research, testing, and development purposes.
- The author plans to continuously review these assets to **attribute proper credits/sources** or **replace them entirely with original, self-made media** in future updates.

### 3. General Disclaimer
This is an unofficial, non-commercial fan-made project developed by the community. It is not affiliated with, endorsed by, or authorized by Roblox Corporation or the developers of Sol's RNG. Use at your own discretion.
