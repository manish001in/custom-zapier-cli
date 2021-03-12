from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zapier.settings')

app = Celery('zapier')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()

app.conf.beat_schedule = {
    'create-zap-instances': {
        'task': 'core_engine.tasks.call_zaps',
        'schedule': 300.0,
    },
}