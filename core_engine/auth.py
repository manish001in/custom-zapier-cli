from django.conf import settings


class BaseAuth(object):
    def __init__(self):
        self.auth_type = ""
        self.name = "BaseAuth"
