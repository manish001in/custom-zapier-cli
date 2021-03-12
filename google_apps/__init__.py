from django.conf import settings
import os

DOWNLOADS_DIR = settings.BASE_DIR+'/downloads/google_apps/'

if not os.path.exists(DOWNLOADS_DIR):
    os.makedirs(DOWNLOADS_DIR)