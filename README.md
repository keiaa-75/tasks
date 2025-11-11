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
   - Rename the downloaded file to `credentials.json`
   - Place it in `~/.config/tasks/credentials.json`
   - For Windows, place it in `%APPDATA%\Roaming\tasks`

### 2. Installation

You must have `git` and `python3-pip` installed. Clone this repository to install the application:

```bash
git clone http://github.com/keiaa-75/tasks && cd tasks
python3 -m venv .venv
pip install .
```

You may also opt to build a one-file executable:
```bash
python3 build.py
```

## Usage

Run the application:

```bash
tasks
```

On first run, it will open a browser window for Google authentication. Grant the necessary permissions to access your Google Tasks.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
