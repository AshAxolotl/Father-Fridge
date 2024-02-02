import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/drive"]


def create_service():
    """create serivce for Forms v1 API."""
    creds = None
    if os.path.exists("google/token.json"):
        creds = Credentials.from_authorized_user_file("google/token.json", SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "google/client_secrets.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("google/token.json", "w") as token:
            token.write(creds.to_json())

    service = build("forms", "v1", credentials=creds)
    return service


if __name__ == "__main__":
    create_service()