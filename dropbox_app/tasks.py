from celery import shared_task
from .views import *
from core_engine.models import *
import json
from zapier.logs import *

@shared_task
def trigger_task(zap_id):
    try:
        zap = Zaps.objects.get(id=zap_id)
        trigger_class = globals()[zap.trigger.name]
        trigger_auth = zap.trigger_app_auth
        trigger_instance = trigger_class(trigger_auth)

        zap.trigger_app_auth = trigger_instance.get_credential_json_object()
        zap_input_data = json.loads(zap.zap_input_data)
        zap.save()
        
        trigger_instance.create_setup_data(zap_input_data['trigger_data'])
        status, output = trigger_instance.execute_function()

        if type(output)==str:
            apps_logger.info(zap.trigger.app.extra_data['project']+":Tasks:TriggerOutput:"+output)
        return {'status':status, 'trigger_data':output}
    except Exception as e:
        apps_error_logger.info("DropBoxApp:Tasks:TriggerFailureException:ZapID="+str(zap_id)+":"+str(e))
        return {'status':False, 'trigger_data':"Failure, check logs"}

@shared_task
def action_task(trigger_info, zap_id):
    try:
        trigger_status = trigger_info['status']
        zap = Zaps.objects.get(id=zap_id)
        if trigger_status:
            trigger_data = trigger_info['trigger_data']
            
            action_class = globals()[zap.action.name]
            action_auth = zap.action_app_auth
            action_instance = action_class(action_auth)

            zap.action_app_auth = action_instance.get_credential_json_object()
            zap_input_data = json.loads(zap.zap_input_data)

            action_instance.create_setup_data(zap_input_data['action_data'])
            status = action_instance.execute_function(trigger_data)

        zap.last_run = datetime.datetime.utcnow()
        zap.save()
    except Exception as e:
        apps_error_logger.info("DropBoxApp:Tasks:ActionFailureException:ZapID="+str(zap_id)+":"+str(e))
        