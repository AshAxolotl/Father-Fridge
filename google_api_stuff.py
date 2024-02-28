from googleapiclient.discovery import build  # Added
from google.oauth2 import service_account
from googleapiclient.errors import HttpError
from bot_config import BASE_FORM_ID, SERVICE_ACCOUNT


# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/drive"]
creds = service_account.Credentials.from_service_account_info(SERVICE_ACCOUNT)

origin_file_id = {"formId": BASE_FORM_ID, "responderUri": "https://docs.google.com/forms/d/e/ERROR/viewform"}

# Create service 
def create_service(type: str, version: str):
    service = build(serviceName=type, version=version, credentials=creds)
    return service

# Create Form
def create_form(data) -> dict:
    # copy the origin art contest form
    theme = data["artContestTheme"]
    try:
        drive_service = create_service(type="drive", version="v3")
        copied_file_info = {"title": f"Art Contest: {theme}", "name": f"Art Contest: {theme}"}
        copy_results = drive_service.files().copy(fileId=origin_file_id["formId"], body=copied_file_info).execute()

    except HttpError as error:
        print(f"An error occurred while coping the base form: {error}")
        return origin_file_id
    except:
        print("An unknown error occurred while coping the base form")
        return origin_file_id

    return update_form(form_id=copy_results["id"], data=data)



def update_form(form_id, data) -> dict:
    try: 
        # Update to the form to add description and base quistion
        forms_service = create_service(type="forms", version="v1")
        theme = data["artContestTheme"]

        form_update = { 
            "requests": [
                {
                    "updateFormInfo": {
                        "info": {
                            "title": f"Art Contest: {theme}",
                            "description": "vote for the art contest!\nREMEMBER: DONT VOTE ON OWN ART AND DONT VOTE MORE THAN ONCE!",
                        },
                        "updateMask": "*",
                    }
                },
                {
                    "createItem": {
                        "item": {
                            "title": "what is your username?",
                            "questionItem": {
                                "question": {
                                    "required": True,
                                    "questionId":"0000aaaa",
                                    "textQuestion": {
                                        "paragraph": False
                                    }
                                }
                            }
                        },
                        "location": {"index": 0},
                    }
                },
            ]
        }

        # adds all of the voting quistons to the update
        for key in data["artContestSubmissions"]:
            username = data["artContestSubmissions"][key]["username"]
            title = data["artContestSubmissions"][key]["title"]
            id = data["artContestSubmissions"][key]["id"]
            form_update["requests"].append(
                        {
                    "createItem": {
                        "item": {
                            "title": f"{username}: {title}",
                            "itemId": f"{id}a",
                            "questionGroupItem": {
                                "image": {
                                    "sourceUri": data["artContestSubmissions"][key]["url"],
                                },
                                "grid": {
                                    "columns": {
                                        "type": "RADIO",
                                        "options": [{"value": "1"}, {"value": "2"}, {"value": "3"}, {"value": "4"}, {"value": "5"}]
                                    }
                                },
                                "questions": [
                                    {
                                        "questionId": f"{id}b",
                                        "rowQuestion": {"title": "How it look"}
                                    },
                                    {
                                        "questionId": f"{id}c",
                                        "rowQuestion": {"title": "Originality"}
                                    },
                                    {
                                        "questionId": f"{id}d",
                                        "rowQuestion": {"title": "How well does it use the theme"}
                                    }
                                ]
                            }
                        },
                        "location": {"index": 1}
                    }
                },
            )

        # Update the form with the form_update
        forms_service.forms().batchUpdate(formId=form_id, body=form_update).execute()
        form_data = forms_service.forms().get(formId=form_id).execute()
        return {"formId": form_data["formId"], "responderUri": form_data["responderUri"]}
    
    except HttpError as error:
        print(f"An error occurred while updating the form: {error}")
        return origin_file_id
    except:
        print("An unknown error occurred while updating the form")
        return origin_file_id


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