from django.conf import settings
from oauth2client import client, tools, file
from core_engine import auth
import google_file

class GoogleAuth(auth.BaseAuth):
    def __init__(self, scope):
        self.auth_type='OAuth2'
        self.name='GoogleOAuth'
        self.auth_cred=settings.GOOGLE_OAUTH_CREDENTIALS
        if type(scope)==str or type(scope)==unicode:
            if ',' in scope:
                scope=scope.split(',')
            else:
                scope=[scope]
        self.scope=' '.join(scope)
        self.credentials=None

    def authorize(self):
        #Creating OauthFlow object from Google API
        flow = client.OAuth2WebServerFlow(client_id=self.auth_cred['client_id'],
                                          client_secret=self.auth_cred['client_secret'],
                                          scope=self.scope,
                                          redirect_uri=self.auth_cred['redirect_uris'][0])
        
        #Argument namespace to set no auth local webserver, to use for cli project
        args = tools.argparser.parse_args()
        args.noauth_local_webserver = True

        store = google_file.Storage()
        try:
            credentials = tools.run_flow(flow,store,flags=args)
            self.credentials = credentials
        except Exception as e:
            print "Following error raised while authentication: "+str(e)
        return self.credentials
