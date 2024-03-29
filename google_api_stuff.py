from googleapiclient.discovery import build  # Added
from google.oauth2 import service_account
from googleapiclient.errors import HttpError
from bot_config import SERVICE_ACCOUNT


SCOPES = ["https://www.googleapis.com/auth/drive"]
creds = service_account.Credentials.from_service_account_info(SERVICE_ACCOUNT)

# Create service 
def create_service(type: str, version: str):
    service = build(serviceName=type, version=version, credentials=creds)
    return service


# Delets the place holder forms that where made from testing 
def delete_place_holder_forms():
    try:
        drive_service = create_service(type="drive", version="v3")

        # Call the Drive v3 API
        results = drive_service.files().list(pageSize=10, fields="nextPageToken, files(id, name)").execute()
        items = results.get("files", [])

        if not items:
            print("No files found.")
            return
        print("Files:")
        for item in items:
            if item["name"] in ["Art Contest: PLACE HOLDER", "Art Contest: Test Theme", "Art Contest: THEME", "Art Contest: test"]:
                drive_service.files().delete(fileId=item["id"]).execute()
            else:
                print(f"{item['name']} ({item['id']})")
    
    except HttpError as error:
        print(f"An error occurred: {error}")
    


# if this script get run directly it runs delete_place_holder_forms()
if __name__ == "__main__":
    delete_place_holder_forms()