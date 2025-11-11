import os
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# Define the scope for the Google Tasks API
SCOPES = ["https://www.googleapis.com/auth/tasks"]


def get_credentials_path() -> Path:
    """Get the path to the credentials.json file."""
    return Path(__file__).parent / "credentials.json"


def get_token_path() -> Path:
    """Get the path to the token.json file following XDG specs."""
    xdg_data_home = os.environ.get("XDG_DATA_HOME")
    if xdg_data_home:
        data_home = Path(xdg_data_home)
    else:
        data_home = Path.home() / ".local" / "share"

    app_data_dir = data_home / "google-tasks-overlay"
    app_data_dir.mkdir(parents=True, exist_ok=True)

    return app_data_dir / "token.json"


def get_credentials() -> Credentials:
    """
    Get user credentials for the Google Tasks API.
    This will either load existing credentials or run the OAuth2 flow.
    """
    token_path = get_token_path()
    creds = None

    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            credentials_path = get_credentials_path()
            if not credentials_path.exists():
                raise FileNotFoundError(
                    f"Credentials file not found at {credentials_path}. "
                    "Please place your credentials.json from Google Cloud Console there."
                )

            flow = InstalledAppFlow.from_client_secrets_file(
                str(credentials_path), SCOPES
            )
            creds = flow.run_local_server(port=0)

        with open(token_path, "w") as token_file:
            token_file.write(creds.to_json())

    return creds
