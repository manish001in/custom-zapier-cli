from __future__ import absolute_import, unicode_literals
from celery import shared_task, chain
from .models import *
from importlib import import_module
from zapier.logs import core_logger
import json


@shared_task
def call_zaps():
    core_logger.info("Tasks:call_zaps called")
    zaps = Zaps.objects.filter(active=True)
    for zap in zaps:
        trigger_app_data = json.loads(zap.trigger.app.extra_data)
        action_app_data = json.loads(zap.action.app.extra_data)

        trigger_app_module = trigger_app_data["project"]
        action_app_module = action_app_data["project"]

        trigger_app_module = import_module(trigger_app_module + ".tasks")
        action_app_module = import_module(action_app_module + ".tasks")

        trigger_app_trigger_task = getattr(trigger_app_module, "trigger_task")
        action_app_action_task = getattr(action_app_module, "action_task")

        response = chain(
            trigger_app_trigger_task.s(zap.id), action_app_action_task.s(zap.id)
        ).delay()
