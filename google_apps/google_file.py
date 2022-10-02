from oauth2client import client
import threading


class Storage(client.Storage):
    """Store and retrieve a single credential to and from Django DB.
    Need to provide json credential string as init.
    """

    def __init__(self, json_cred_string=""):
        super(Storage, self).__init__(lock=threading.Lock())
        self._cred = json_cred_string

    def locked_get(self):
        """Retrieve Credential from file.

        Returns:
            oauth2client.client.Credentials

        Raises:
            IOError if the file is a symbolic link.
        """
        credentials = None
        try:
            content = self._cred
        except Exception:
            return credentials

        try:
            credentials = client.Credentials.new_from_json(content)
            credentials.set_store(self)
        except ValueError:
            pass

        return credentials

    def locked_put(self, credentials):
        """Returns Credentials as a json string.

        Args:
            credentials: Credentials, the credentials to store.

        Raises:
        """
        return credentials.to_json()
