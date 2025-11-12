# Tasks

[![Python](https://img.shields.io/badge/Made%20with-Python-1f425f.svg?style=flat&logo=python)](https://www.python.org/)
[![Qt](https://img.shields.io/badge/Made%20with-Qt-41CD52.svg?style=flat&logo=qt)](https://www.qt.io/)

A simple, cross-platform, PyQt-based Google Tasks client. Made for learning purposes.

## Setup

### 1. Google Cloud Console Setup

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google Tasks API:
   - Go to "APIs & Services" > "Library"
   - Search for "Tasks API"
   - Click on it and press "Enable"
4. Create credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - If prompted, configure the OAuth consent screen first
   - Choose "Desktop application" as the application type
   - Give it a name (e.g., "Tasks")
   - Download the JSON file
   - Go to "Audience" > "Test Users"
   - Add your preferred Google Account
5. Place the credentials file:
   Rename the downloaded file to `credentials.json` and place it in the correct directory for your operating system. You may need to create the tasks folder.

    - **Linux:** `~/.config/tasks/`
    - **Windows:** `%APPDATA%\tasks\`
    - **macOS:** `~/Library/Application Support/tasks/`

### 2. Installation

You must have Git and Python installed on your system and available in your PATH.

1. **Clone the repository:**

   ```bash
   git clone https://github.com/keiaa-75/tasks && cd tasks
   ```

2. **Create and activate a virtual environment:**

   For Linux/macOS:

   ```bash
   python3-m venv .venv
   source .venv/bin/activate
   ```

   For Windows:

   ```pwsh
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. **Install the application:**

   ```bash
   pip install .
   ```

### 3. Build an Executable (Optional)

You can also build a single-file executable. This project uses `PyInstaller`.

1. **Install PyInstaller:**

   ```bash
   pip install pyinstaller
   ```

2. **Run the build script:**

   ```bash
   python build.py
   ```

## Usage

Run the application:

```
tasks
```

On first run, it will open a browser window for Google authentication. Grant the necessary permissions to access your Google Tasks.
