from core_engine import auth
from django.conf import settings
from dropbox import DropboxOAuth2FlowNoRedirect


class DropboxAuth(auth.BaseAuth):
    def __init__(self):
        self.auth_type='OAuth2'
        self.name='DropboxOAuth'
        self.auth_cred=settings.DROPBOX_CREDENTIALS
        self.credentials=None

    def authorize(self):
        
        flow = DropboxOAuth2FlowNoRedirect(self.auth_cred['client_id'], self.auth_cred['client_secret'])
        auth_url = flow.start()
        print "1. Go to: " + auth_url
        print "2. Click \"Allow\" (you might have to log in first)."
        print "3. Copy the authorization code."
        auth_code = raw_input("Enter the authorization code here: ").strip()

        try:
            oauth_result = flow.finish(auth_code)
            self.credentials = oauth_result
        except Exception as e:
            print "Following error raised while authentication: "+str(e)
        return self.credentials
