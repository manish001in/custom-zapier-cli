import os
import sys
import json

if __name__ == "__main__":
    # Setup environ
    sys.path.append(os.getcwd())
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "zapier.settings")

    # Setup django
    import django

    django.setup()

    from core_engine.models import *

    #### Apps database objects ####

    extra_data = {"project": "dropbox_app", "class": "DropBoxObject"}
    dropbox_app, _ = Apps.objects.get_or_create(
        name="DropboxApp",
        defaults={
            "description": "Dropbox is a file hosting service operated by the American company Dropbox, Inc., headquartered in San Francisco, California, that offers cloud storage, file synchronization, personal cloud, and client software.",
            "website": "https://dropbox.com",
            "extra_data": json.dumps(extra_data),
        },
    )
    extra_data = {"project": "google_apps", "class": "GoogleMail"}
    gmail_app, _ = Apps.objects.get_or_create(
        name="GMailApp",
        defaults={
            "description": "Gmail is a free email service developed by Google.",
            "website": "https://gmail.com",
            "extra_data": json.dumps(extra_data),
        },
    )
    extra_data = {"project": "google_apps", "class": "GoogleDrive"}
    gdrive_app, _ = Apps.objects.get_or_create(
        name="GoogleDriveApp",
        defaults={
            "description": "Google Drive is a file storage and synchronization service developed by Google. Google Drive allows users to store files on their servers, synchronize files across devices, and share files.",
            "website": "https://drive.google.com",
            "extra_data": json.dumps(extra_data),
        },
    )
    extra_data = {"project": "google_apps", "class": "GoogleSheets"}
    gsheets_app, _ = Apps.objects.get_or_create(
        name="GoogleSheetsApp",
        defaults={
            "description": "Google Sheets is a spreadsheet program included as part of a free, web-based software office suite offered by Google within its Google Drive service.",
            "website": "https://docs.google.com/spreadsheets/",
            "extra_data": json.dumps(extra_data),
        },
    )

    #### Triggers database apps ####
    setup_data = {
        "text_input": [
            {"name": "filename", "not_empty": True, "type": "str"},
            {"name": "path", "type": "str"},
            {"name": "check_update_duration_seconds", "not_empty": True, "type": "int"},
        ]
    }
    dropbox_file_update_trigger, _ = Triggers.objects.get_or_create(
        app=dropbox_app,
        name="FileUpdateTrigger",
        defaults={
            "description": "Checks when a file is updated in last certain seconds in dropbox",
            "setup_data": setup_data,
        },
    )

    setup_data = {
        "text_input": [
            {"name": "file_id", "not_empty": True, "type": "str"},
            {"name": "check_update_duration_seconds", "not_empty": True, "type": "int"},
        ]
    }
    gdrive_file_modified_trigger, _ = Triggers.objects.get_or_create(
        app=gdrive_app,
        name="FileModifiedTrigger",
        defaults={
            "description": "Checks when a file is modified in last certain seconds in google drive",
            "setup_data": setup_data,
        },
    )

    setup_data = {
        "text_input": [
            {
                "name": "headers",
                "type": "str",
                "options": ["From", "To", "Date", "Subject"],
                "input_string": "Select the headers you wanna add to your trigger data, if any, in a comma separated way.",
                "example": "From,To or Subject,To",
            },
            {
                "name": "mailBodyBool",
                "type": "bool",
                "not_empty": True,
                "input_string": "Should we include the mail body text in trigger data?\nPlease answer in yes or no.",
            },
            {
                "name": "search_query",
                "type": "str",
                "example": "from:someuser@example.com rfc822msgid:<somemsgid@example.com> is:unread",
            },
        ]
    }
    gmail_email_trigger, _ = Triggers.objects.get_or_create(
        app=gmail_app,
        name="EMailTrigger",
        defaults={
            "description": "Checks every few minutes and then processes the emails matching a certain query with the collected data sent to an action",
            "setup_data": setup_data,
        },
    )

    #### Actions database apps ####
    setup_data = {
        "text_input": [
            {
                "name": "filename",
                "not_empty": True,
                "type": "str",
                "input_string": "Enter the file's name on dropbox in which the data will be uploaded.",
            },
            {"name": "path", "type": "str"},
        ]
    }
    dropbox_file_upload_action, _ = Actions.objects.get_or_create(
        app=dropbox_app,
        name="UploadAction",
        defaults={
            "description": "Uploads certain data to a file in dropbox(makes an update)",
            "setup_data": setup_data,
        },
    )

    setup_data = {
        "text_input": [
            {
                "name": "filename",
                "type": "str",
                "not_empty": True,
                "input_string": "Enter the file's name on dropbox.",
            },
            {
                "name": "path",
                "type": "str",
                "input_string": "Enter the file's path on dropbox.",
            },
        ]
    }
    dropbox_file_download_action, _ = Actions.objects.get_or_create(
        app=dropbox_app,
        name="DownloadAction",
        defaults={
            "description": "Downloads a file from dropbox",
            "setup_data": setup_data,
        },
    )

    setup_data = {"text_input": [{"name": "file_id", "type": "str", "not_empty": True}]}
    gdrive_file_download_action, _ = Actions.objects.get_or_create(
        app=gdrive_app,
        name="DownloadFileAction",
        defaults={
            "description": "Downloads a file from google drive and stores in a location on server",
            "setup_data": setup_data,
        },
    )

    setup_data = {
        "text_input": [
            {"name": "sheet_id", "not_empty": True, "type": "str"},
            {
                "name": "sheet_name",
                "type": "str",
                "input_string": "Please enter sheet name such as sheet1, sheet2 etc. Do NOT enter the entire spreadsheet name.",
            },
            {
                "name": "sheet_range",
                "type": "str",
                "not_empty": True,
                "input_string": "Enter sheet range in A1 notation, the rows will be appended after the range.",
                "example": "A1:E1",
            },
        ]
    }
    gsheets_appendrow_action, _ = Actions.objects.get_or_create(
        app=gsheets_app,
        name="AppendRowAction",
        defaults={
            "description": "Takes the received data and adds a row to the google sheets",
            "setup_data": setup_data,
        },
    )
