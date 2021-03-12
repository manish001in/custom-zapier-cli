# import views
import json
import base64, email
from bs4 import BeautifulSoup

# def get_specific_data_from_gdrive_file(fileId, auth_obj, field=''):
#     """Requires google drive scope in the auth object, you can get either the basic file info from google drive or a specific field info as a json"""

#     scope = "https://www.googleapis.com/auth/drive"
#     gdrive_obj = views.GoogleDrive(auth_obj, scope)
#     drive = gdrive_obj.service
#     fieldJSON = drive.files().get(fileId=fileId, fields=field).execute()

#     return fieldJSON

def get_text_from_email(base64string):
    msg_str = base64.urlsafe_b64decode(base64string.encode('latin1'))
    mime_msg = email.message_from_string(msg_str)
    if type(mime_msg.get_payload())==list:
        val = (mime_msg.get_payload()[0]).get_payload()
    else:
        val = mime_msg.get_payload()
    parsed_email=BeautifulSoup(val, 'html.parser')

    email_text = ""

    if len(parsed_email.find_all("body"))>0:
        email_text = parsed_email.body.get_text()
    else:
        email_text = parsed_email.get_text()

    return email_text
