from __future__ import unicode_literals
from zapier.logs import apps_error_logger, apps_logger
import auth
from core_engine import utility as core_utility
from oauth2client import client
import datetime, io, json, os
from googleapiclient import discovery, http
from googleapiclient.errors import HttpError
from utility import get_text_from_email
from django.conf import settings

DOWNLOAD_LOCATION = settings.DOWNLOAD_DIR+'google_apps/'
os.system("mkdir -p "+DOWNLOAD_LOCATION)

def setup_authentication(context_obj, zap_step):
    """
    Authentication function for the dropbox app, used to get access token from users.
    """
    google_auth_obj = auth.GoogleAuth(context_obj[zap_step+'_app_scope'])
    credentials = google_auth_obj.authorize()

    context_obj[zap_step+'_app_auth'] = credentials.to_json()


class GoogleObject(object):
    """
    Base object for triggers and actions, returns a dropbox instance.
    """
    def __init__(self, auth_obj, scope):
        self.auth_obj=auth_obj
        self.service = None
        self.execute_function = None
        
        if scope is None or scope=='':
            self.scope = 'https://www.googleapis.com/auth/userinfo.email'
        else:
            self.scope = scope
        
        try:
            if auth_obj is None or auth_obj=='':
                google_auth_obj = auth.GoogleAuth(self.scope)
                credentials = google_auth_obj.authorize()
                self.auth_obj = credentials
            else:
                credentials = client.Credentials()
                self.auth_obj = credentials.new_from_json(auth_obj)

            if self.auth_obj.invalid:
                google_auth_obj = auth.GoogleAuth(self.scope)
                credentials = google_auth_obj.authorize()

                self.auth_obj = credentials
        
        except Exception as err:
            apps_error_logger.info("GoogleAuthError:In "+str(self.__class__.__name__)+", "+str(err))

    def get_credential_json_object(self):
        
        if type(self.auth_obj)==client.OAuth2Credentials:
            return self.auth_obj.to_json()
        else:
            apps_error_logger.info("GoogleAuthError:In "+str(self.__class__.__name__)+", auth object is not credential type")
            raise Exception("Auth Object is not credential type")


class GoogleDrive(GoogleObject):
    
    def __init__(self, auth_obj):
        scope = "https://www.googleapis.com/auth/drive"
        super(GoogleDrive, self).__init__(auth_obj, scope)
        self.service = discovery.build('drive', 'v3', credentials=self.auth_obj, cache_discovery=False)
    
class DownloadFileAction(GoogleDrive):
    
    def __init__(self, auth_obj):
        super(DownloadFileAction, self).__init__(auth_obj)
        self.data_obj={}
        self.execute_function=self.download_file

    def create_setup_data(self,setup_object):
        self.data_obj = setup_object

    def download_file(self, trigger_data=None):
        try:
            file_id = self.data_obj['file_id']
            drive = self.service
            file_response = drive.files().get(fileId=file_id).execute()

            filename = file_response["name"]
            mimeType = file_response["mimeType"]

            response = drive.about().get(fields='exportFormats').execute()
            exportFormats = response['exportFormats']

            useMimeType = exportFormats[mimeType][0]

            file_data = drive.files().get_media(fileId=file_id)
            file_handle = io.BytesIO()

            downloader = http.MediaIoBaseDownload(file_handle, file_data)
            done = False
            
            while done is False:
                status, done = downloader.next_chunk()
            
            f = open(DOWNLOAD_LOCATION+filename, 'wb+')
            f.write(file_handle.getvalue())
            f.close()
            
            apps_logger.info("GoogleDrive:DownloadFileAction:ActionSuccessful - ZapID:"+str(self.data_obj['zap_id']))

        except HttpError as httperr:
            apps_logger.info("GoogleDrive:DownloadFileAction:ActionException:Got HTTP error, using export_media - ZapID:"+str(self.data_obj['zap_id']))

            file_data = drive.files().export_media(fileId=file_id, mimeType=useMimeType)
            file_handle = io.BytesIO()

            downloader = http.MediaIoBaseDownload(file_handle, file_data)
            done = False
            
            while done is False:
                status, done = downloader.next_chunk()
            
            f = open(DOWNLOAD_LOCATION+filename, 'wb+')
            f.write(file_handle.getvalue())
            f.close()

            apps_logger.info("GoogleDrive:DownloadFileAction:ActionSuccessful - ZapID:"+str(self.data_obj['zap_id']))            
        
        except Exception as err:
            apps_error_logger.info("GoogleDriveError:DownloadFileAction:ActionFailed:"+str(err))

class FileModifiedTrigger(GoogleDrive):
    
    def __init__(self, auth_obj):
        super(FileModifiedTrigger, self).__init__(auth_obj)
        self.data_obj={}
        self.execute_function=self.file_modified

    def create_setup_data(self,setup_object):
        self.data_obj = setup_object

    def file_modified(self):
        try:
            file_id = self.data_obj['file_id']
            update_check_duration_seconds = self.data_obj['check_update_duration_seconds']
            drive = self.service
    
            response = drive.files().get(fileId=file_id, fields='modifiedTime').execute()

            modifiedTime = datetime.datetime.strptime(response["modifiedTime"], "%Y-%m-%dT%H:%M:%S.%fZ")
            currentUTCTime = core_utility.get_current_utc_datetime()
            
            if (currentUTCTime-modifiedTime).total_seconds()<float(update_check_duration_seconds):
                apps_logger.info("GoogleDrive:FileModifiedTrigger:Triggered - ZapID:"+str(self.data_obj['zap_id']))
                return True, "File Modified in last check duration"
            else:
                return False, "Not modified in last check duration"
    
        except Exception as err:
            apps_error_logger.info("GoogleDriveError:FileModifiedTrigger:TriggerFailed:"+str(err))
            return False, "Some error occured"

      

class GoogleSheets(GoogleObject):
    
    def __init__(self, auth_obj):
        scope = "https://www.googleapis.com/auth/spreadsheets"
        super(GoogleSheets, self).__init__(auth_obj, scope)
        self.service = discovery.build('sheets', 'v4', credentials=self.auth_obj, cache_discovery=False)
    
class AppendRowAction(GoogleSheets):
    
    def __init__(self, auth_obj):
        super(AppendRowAction, self).__init__(auth_obj)
        self.data_obj={}
        self.execute_function=self.append_row

    def create_setup_data(self,setup_object):
        self.data_obj = setup_object

    def append_row(self, trigger_data):
        try:
            sheets = self.service
            sheet_id = self.data_obj['sheet_id']
            sheet_name = self.data_obj['sheet_name']
            sheet_range = self.data_obj['sheet_range']
    
            if ' ' in sheet_name:
                sheet_name = '"'+sheet_name+'"'
            sheet_range = sheet_name+"!"+sheet_range
            
            value_list = []
            msg_data_list = trigger_data

            for msg in msg_data_list:
                msg_array = []
    
                if 'headers' in msg:
                    header_list = msg['headers_list']
                    header_data = msg['headers']
                    for header in header_list:
                        for header_dict in header_data:
                            if header==header_dict['name']:
                                msg_array.append(header_dict['value'])
                                continue
    
                for key in msg:
                    if key=='headers' or key=='headers_list':
                        pass
                    else:
                        msg_array.append(msg[key])
                
                value_list.append(msg_array)

            insertDataOption = "INSERT_ROWS"
            valueInputOption = "USER_ENTERED"

            body = {
                "majorDimension": "ROWS",
                "values": value_list
            }

            sheet_update_response = sheets.spreadsheets().values().append(spreadsheetId=sheet_id, range=sheet_range, body=body, insertDataOption=insertDataOption, valueInputOption=valueInputOption).execute()
            apps_logger.info("GoogleDrive:AppendRowAction:ActionSuccessful - ZapID:"+str(self.data_obj['zap_id']))

        except Exception as err:
            apps_error_logger.info("GoogleDriveError:AppendRowAction:ActionFailed:"+str(err))



class GoogleMail(GoogleObject):
    
    def __init__(self, auth_obj):
        scope = "https://mail.google.com/"
        super(GoogleMail, self).__init__(auth_obj, scope)
        self.service = discovery.build('gmail', 'v1', credentials=self.auth_obj, cache_discovery=False)
    
class EMailTrigger(GoogleMail):
    
    def __init__(self, auth_obj):
        super(EMailTrigger, self).__init__(auth_obj)
        self.data_obj={}
        self.execute_function=self.email_trigger

    def create_setup_data(self,setup_object):
        self.data_obj = setup_object

    def email_trigger(self):
        try:
            after_time = core_utility.get_current_epoch()-900    # assumes last run time would be 15 mins back and gets that.
            email = self.service
            query = self.data_obj["search_query"]
            query += " after:"+str(after_time)

            response = email.users().messages().list(userId="me", q=query).execute()

            messages = []
            if 'messages' in response:
                messages.extend(response['messages'])

            while 'nextPageToken' in response:
                page_token = response['nextPageToken']
                response = email.users().messages().list(userId="me", q=query, pageToken=page_token).execute()
                messages.extend(response['messages'])

            header_values = self.data_obj["headers"]
            get_mail_body = self.data_obj["mailBodyBool"]

            return_body = []

            for message in messages:
                msg_dict = {}
    
                if len(header_values)>0:
                    msg_dict['headers_list'] = header_values
                    response = email.users().messages().get(userId="me", id=message["id"], format="metadata", metadataHeaders=header_values).execute()
                    msg_dict["headers"] = response["payload"]["headers"]
    
                if get_mail_body:
                    response = email.users().messages().get(userId="me", id=message["id"], format="raw").execute()
                    msg_dict["body"] = get_text_from_email(response["raw"])
    
                return_body.append(msg_dict)

            if len(return_body)>0:
                apps_logger.info("GoogleDrive:EMailTrigger:Triggered - ZapID:"+str(self.data_obj['zap_id']))
                return True, return_body
            else:
                return False, return_body
    
        except Exception as err:
            apps_error_logger.info("GoogleDriveError:EMailTrigger:TriggerFailed:"+str(err), exc_info=True)
            return False, return_body