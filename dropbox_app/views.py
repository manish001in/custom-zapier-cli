from __future__ import unicode_literals
import contextlib, os
from . import auth
from dropbox import Dropbox, files, exceptions
from zapier.logs import apps_logger, apps_error_logger
from core_engine import utility

def setup_authentication(context_obj, zap_step):
    """
    Authentication function for the dropbox app, used to get access token from users.
    """
    dropbox_auth_obj = auth.DropboxAuth()
    credentials = dropbox_auth_obj.authorize()

    context_obj[zap_step+'_app_auth'] = {'access_token': credentials.access_token, 'account_id': credentials.account_id}


class DropBoxObject(object):
    """
    Base object for triggers and actions, returns a dropbox instance.
    """
    def __init__(self, auth_obj):
        if auth_obj is None or '':
            dropbox_auth_obj = auth.DropboxAuth()
            credentials = dropbox_auth_obj.authorize()
            auth_obj = {'access_token': credentials.access_token, 'account_id': credentials.account_id}
        self.auth_obj=auth_obj
        self.dropbox_obj = Dropbox(self.auth_obj['access_token'])
        self.execute_function = None

    def get_credential_json_object(self):
        return self.auth_obj


class UploadAction(DropBoxObject):
    """
    Upload Action, uploads certain data to a file in dropbox as the action to a trigger.
    Path can be used to upload a file at a certain location, inside folders etc.
    """
    def __init__(self, auth_obj):
        super(UploadAction, self).__init__(auth_obj)
        self.data_obj={}
        self.execute_function=self.upload_file

    def create_setup_data(self, setup_object):
        """
        create setup data receives information stored in the database to populate needed arguments for triggers/actions
        """
        self.data_obj = setup_object

    def upload_file(self, trigger_data):
        try:
            if self.data_obj['path'] is not None:
                upload_path = self.data_obj['path']+'/'+self.data_obj['filename']
            else:
                upload_path = '/'+self.data_obj['filename']

            self.dropbox_obj.files_upload(trigger_data['upload_data'], upload_path, mode=files.WriteMode('overwrite'))
            apps_logger.info("Dropbox:UploadAction:ActionSuccessful - ZapID="+str(self.data_obj['zap_id']))

        except Exception as e:
            apps_error_logger.info("DropboxError:UploadAction:ActionFailed:"+str(e))

class DownloadAction(DropBoxObject):
    """
    Unlikely usage, but just in case.
    Downloads a certain file, when a certain action is triggered.
    """

    def __init__(self, auth_obj):
        super(DownloadAction, self).__init__(auth_obj)
        self.data_obj={}
        self.execute_function=self.download_file

    def create_setup_data(self, setup_object):
        self.data_obj = setup_object

    def download_file(self, trigger_data=None):
        try:
            if self.data_obj['path'] is not None:
                download_path = self.data_obj['path']+'/'+self.data_obj['filename']
            else:
                download_path = '/'+self.data_obj['filename']

            metadata = self.dropbox_obj.files_get_metadata(download_path)
            dropbox_filename = metadata.name
            if metadata.name is not None:
                dropbox_filename = metadata.name
            else:
                dropbox_filename = 'downloaded_file'

            metadata = self.dropbox_obj.files_download_to_file(DOWNLOAD_LOCATION+dropbox_filename, download_path)

            apps_logger.info("Dropbox:DownloadAction:ActionSuccessful - ZapID="+str(self.data_obj['zap_id']))

        except Exception as e:
            apps_error_logger.info("DropboxError:DownloadAction:ActionFailed:"+str(e))

class FileUpdateTrigger(DropBoxObject):
    """
    File Update trigger, when a certain file is modified in last certain seconds, it returns true, else false.
    Can be used to take actions based on latest updation of the file within last certain seconds.
    """
    def __init__(self, auth_obj):
        super(FileUpdateTrigger, self).__init__(auth_obj)
        self.data_obj={}
        self.execute_function=self.check_last_update_time

    def create_setup_data(self, setup_object):
        self.data_obj = setup_object

    def check_last_update_time(self):
        try:
            if self.data_obj['path'] != None:
                file_path = self.data_obj['path']+'/'+self.data_obj['filename']
            else:
                file_path = '/'+self.data_obj['filename']

            update_duration = int(self.data_obj['check_update_duration_seconds'])
            file_revision_list = self.dropbox_obj.files_list_revisions(file_path, mode=files.ListRevisionsMode('path', None), limit=1)

            if file_revision_list.is_deleted:
                return False, "File was deleted at "+str(file_revision_list.server_deleted)

            else:
                list_entries = file_revision_list.entries
                latest_revision_datetime = list_entries[0].server_modified
                current_datetime = utility.get_current_datetime()

                if (current_datetime-latest_revision_datetime).total_seconds()<update_duration:
                    apps_logger.info("Dropbox:FileUpdateTrigger:Triggered ZapID="+str(self.data_obj['zap_id']))
                    return True, "File updated in last "+str(int(update_duration)/60)+" minutes"

                apps_logger.info("Dropbox:FileUpdateTrigger:Triggered:NoUpdate ZapID="+str(self.data_obj['zap_id']))
                return False, "File was not updated in last "+str(int(update_duration)/60)+" minutes"

        except KeyError as err:
            apps_error_logger.info("DropboxError:FileUpdateTrigger:TriggerFailed"+str(err))
            return False, "Some data missing"

        except Exception as e:
            apps_error_logger.info("DropboxError:FileUpdateTrigger:TriggerFailed:"+str(e))
            return False, "Some error occured"
