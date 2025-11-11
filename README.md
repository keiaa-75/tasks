# Tasks

A simple, PyQt-based Google Tasks client for Linux.

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
5. Rename the downloaded file to `credentials.json` and place it in `src/tasks/`

### 2. Installation

You must have `git` and `python3-pip` installed. Clone this repository to install the application:

```bash
git clone http://github.com/keiaa-75/tasks && cd tasks
pip install .
```

## Usage

Run the application:

```bash
tasks
```

On first run, it will open a browser window for Google authentication. Grant the necessary permissions to access your Google Tasks.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
