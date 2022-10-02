from __future__ import absolute_import, unicode_literals
from django.conf import settings
import logging

LOGS_DIR = settings.BASE_DIR + "/logs/"

# Logger for core engine app
core_logger = logging.getLogger("core")
handler = logging.FileHandler(LOGS_DIR + "core.log")
formatter = logging.Formatter("%(asctime)s %(name)-12s %(levelname)-8s %(message)s")
handler.setFormatter(formatter)
core_logger.addHandler(handler)
core_logger.setLevel(logging.INFO)

# Error Logger for various apps, their triggers and actions and any auth related issue with them.
apps_error_logger = logging.getLogger("apps_error")
handler = logging.FileHandler(LOGS_DIR + "apps_error.log")
formatter = logging.Formatter("%(asctime)s %(name)-12s %(levelname)-8s %(message)s")
handler.setFormatter(formatter)
apps_error_logger.addHandler(handler)
apps_error_logger.setLevel(logging.INFO)

# Success Logger for various apps, their triggers and actions etc.
apps_logger = logging.getLogger("apps")
handler = logging.FileHandler(LOGS_DIR + "apps.log")
formatter = logging.Formatter("%(asctime)s %(name)-12s %(levelname)-8s %(message)s")
handler.setFormatter(formatter)
apps_logger.addHandler(handler)
apps_logger.setLevel(logging.INFO)
