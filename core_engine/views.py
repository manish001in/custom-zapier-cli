# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from core_engine.models import *
from django.contrib.auth import authenticate
from django.core.exceptions import PermissionDenied
import json, random
from importlib import import_module
from zapier.logs import core_logger
from django.conf import settings 
# from decorators import pass_userid


def user_exists(username):
    user_exists = User.objects.filter(username=username).exists()
    if user_exists:
        raise PermissionDenied("User already exists")
    else:
        return "Enter email now:"

def new_user(username, password, email=None):
    try:
        user = User.objects.create_user(username, email, password)
        user_profile = UserProfile.objects.create(user=user)
        res_str, user = authenticate_user(username, password)
    except Exception as e:
        core_logger.info("CoreEngine:UserError:"+str(e))
        raise Exception(str(e))
    return "New User Created and "+res_str, user

def authenticate_user(username, password):
    user_exists = User.objects.filter(username=username).exists()
    if not user_exists:
        raise PermissionDenied("User with username {} does not exist".format(username))
    user = authenticate(username=username, password=password)
    if user is None:
        raise PermissionDenied("Incorrect credentials!")
    else:
        return "UserAuthenticated", user


def list_apps(appType=None):
    if appType=='trigger':
        app_ids = Triggers.objects.filter().values_list('app', flat=True)
        apps = Apps.objects.filter(id__in=app_ids)
    elif appType=='action':
        app_ids = Actions.objects.filter().values_list('app', flat=True)
        apps = Apps.objects.filter(id__in=app_ids)
    else:
        apps = Apps.objects.filter()

    return_text = 'List of apps\n'

    if len(apps)==0:
        return_text += "Sorry, no apps exist."

    for app in apps:
        return_text+='\n'
        return_text+='Name: '+app.name+'\t'
        return_text+=app.website+'\n'
        return_text+='Description:'+app.description+'\n'

    return return_text

def list_app_triggers(**kwargs):
    try:
        app_name = kwargs.get('app_name','')
        app = Apps.objects.get(name=app_name)

        trigger_list = Triggers.objects.filter(app=app)

        return_text = 'Triggers for app '+str(app_name)

        if len(trigger_list)==0:
            return_text+='\nNo triggers exist for this app.'

        for trigger in trigger_list:
            return_text+='\n'
            return_text+=trigger.name+' :\t'
            return_text+=trigger.description+'\n'

        return return_text
    except Exception as e:
        raise Exception(e)

def list_app_actions(**kwargs):
    try:
        app_name = kwargs.get('app_name','')
        app = Apps.objects.get(name=app_name)

        action_list = Actions.objects.filter(app=app)

        return_text = 'Actions for app '+str(app_name)

        if len(action_list)==0:
            return_text+='\nNo actions exist for this app.'

        for action in action_list:
            return_text+='\n'
            return_text+=action.name+' :\t'
            return_text+=action.description+'\n'

        return return_text
    except Exception as e:
        raise Exception(e)

def list_zaps(**kwargs):
    user = kwargs.get('user', None)
    zaps = Zaps.objects.filter(user_profile__user=user)

    return_text = 'User '+str(user.username)+' has following zaps'

    if len(zaps)==0:
        return_text += "\n\tYou have no zaps available, go ahead, create a new one."

    for zap in zaps:
        return_text+='\n'
        return_text+='Name: '+zap.name+'\n'
        return_text+='Trigger Name: '+zap.trigger.name+'\t'
        return_text+='Action Name: '+zap.action.name+'\t'
        return_text+='Is active: '+str(zap.active)+'\t\n'
    
    return return_text

def make_zap_object(ctx_obj):
    try:

        ctx_info=ctx_obj.extra_info
        zap_input_data = {'trigger_data': ctx_info['zap_object__trigger_data'], 'action_data': ctx_info['zap_object__action_data']}
        
        user_profile = UserProfile.objects.get(user=ctx_obj.user)
        zap = Zaps.objects.create(user_profile=user_profile, name=ctx_info['zap_object__name'], active=True, trigger=ctx_info['trigger_app_trigger'], action=ctx_info['action_app_action'],
                                    trigger_app_auth=ctx_info['zap_object__trigger_auth'], action_app_auth=ctx_info['zap_object__action_auth'], zap_input_data=json.dumps(zap_input_data))

        zap_input_data['trigger_data']['zap_id'] = zap.id
        zap_input_data['action_data']['zap_id'] = zap.id
        zap.zap_input_data = json.dumps(zap_input_data)
        zap.save()

        return True, ""
    except Exception as e:
        core_logger.info("CoreEngine:MakeZap:Error:"+str(e))
        return False, str(e)

def update_zap(**kwargs):
    zap_name = kwargs.get('zap_name', '')
    status = kwargs.get('mark_status', 'inactive')
    user = kwargs.get('user', None)
    if status=='active':
        isactive=True
    else:
        isactive=False
        status='inactive'
    try:
        zap = Zaps.objects.get(name=zap_name, user_profile__user=user)
        zap.active=isactive
        zap.save()
        return "Successfully marked zap "+str(zap_name)+" as "+str(status)
    except Exception as e:
        core_logger.info("CoreEngine:UpdateZap:Error:"+str(e))
        return "Follwing error occured "+str(e)+"\n"+"Please make sure you have given the right command or 'exit' and start again.\n"
  
def get_text_input_setup_data(text_inputs, recalled=False):
    try:
        answer_values = {}

        for text_input in text_inputs:
            name = text_input['name']
            valType = text_input['type']
            print_user_string = "\nWhat would be the "+str(name)+". Please make sure the value you type is a "+str(valType)

            if "input_string" in text_input:
                input_string= text_input['input_string']
                print_user_string = "\n"+input_string
            if "options" in text_input:
                options = str(text_input['options'])
                print_user_string+="\nFollowing are the possible options. Select multiple values using comma separated style.\n"+options
            if "example" in text_input:
                example= str(text_input['example'])
                print_user_string+="\nFor example:"+example
            
            print print_user_string+"\n(You can type 'exitsetup' to exit this setup at any point.)"
            user_input = (raw_input(settings.YELLOWSTARTCOLOR+"==> "+settings.ENDCOLOR)).strip()

            if "not_empty" in text_input and text_input['not_empty']:
                while len(user_input)==0:
                    print print_user_string+"\n(You can type 'exitsetup' to exit this setup at any point.)"
                    print "\nPlease don't leave this field empty, it's a compulsory field."    
                    user_input = (raw_input(settings.YELLOWSTARTCOLOR+"==> "+settings.ENDCOLOR)).strip()
                
        
            if user_input=='exitsetup':
                return False, "Exit setup called"
            
            if valType=='int':
                user_input = int(user_input)
            elif valType=='bool':
                if user_input.lower()=='yes':
                    user_input=True
                elif user_input.lower()=='no':
                    user_input=False
                else:
                    print "\nWrong user input. Try one more time."
                    user_reinput = (raw_input(settings.YELLOWSTARTCOLOR+"==> "+settings.ENDCOLOR)).strip()
                    if user_reinput.lower()=='yes':
                        user_input=True
                    elif user_reinput.lower()=='no':
                        user_input=False
                    else:
                        return False, {}

            if "options" in text_input:
                list_input = user_input.split(',')
                user_input = set(map(lambda x: x.strip(), list_input))
                if (len(user_input)==1 and list(user_input)[0]=='') or user_input.issubset(set(text_input['options'])):
                    user_input=list(user_input)
                else:
                    print "\nWrong input for "+str(name)+". Options need to be entered as comma separated values"
                    return False, {}
            
            answer_values[name]=user_input

        return True, answer_values

    except Exception as e:
        if not recalled:
            print "\nThere was some issue with your inputs. Here is the error "+str(e)+"\n\nPlease make sure you follow the instructions and enter correct type of values."
            get_text_input_setup_data(text_inputs, recalled=True)
        else:
            print "\nThere is some issue with your inputs. Here is the error "+str(e)+"\n\nPlease start over again."
            return False, answer_values


def handle_trigger_setup(command, context_obj):
    
    trigger = context_obj.extra_info['trigger_app_trigger']
    print "\nSetting up trigger data for "+str(trigger.name)+" in "+str(context_obj.extra_info['trigger_app'])
    
    trigger_setup_data = trigger.setup_data
    trigger_app_extra_data = json.loads(trigger.app.extra_data)

    project_name = trigger_app_extra_data['project']
    class_name = trigger_app_extra_data['class']

    import_class = getattr(import_module(project_name+".views"), str(trigger.name))
    print "\nWe would now gain authentication on your behalf from the app. Please follow the coming instructions."
    
    try:
        trigger_obj = import_class(None)
        auth_obj = trigger_obj.get_credential_json_object()
        print "\nAuthentication successfully done. Thank you."

        setup_status, answer_values = get_text_input_setup_data(trigger_setup_data['text_input'])
        
        if setup_status:
            context_obj.extra_info['zap_object__trigger_data'] = answer_values
            context_obj.extra_info['zap_object__trigger_auth'] = auth_obj
            return True, "Trigger setup is done. Please press enter"
        else:
            if answer_values=='Exit setup called':
                return False, answer_values
            return False, "Trigger setup was unsuccessful. "
    
    except Exception as e:
        return False, str(e)


def handle_action_setup(command, context_obj):

    action = context_obj.extra_info['action_app_action']
    print "\nSetting up action data for "+str(action.name)+" in "+str(context_obj.extra_info['action_app'])
    
    action_setup_data = action.setup_data
    action_app_extra_data = json.loads(action.app.extra_data)

    project_name = action_app_extra_data['project']
    class_name = action_app_extra_data['class']

    import_class = getattr(import_module(project_name+".views"), str(action.name))
    print "\nWe would now gain authentication on your behalf from the app. Please follow the coming instructions."

    try:
        action_obj = import_class(None)
        auth_obj = action_obj.get_credential_json_object()
        print "\nAuthentication successfully done. Thank you."
        
        setup_status, answer_values = get_text_input_setup_data(action_setup_data['text_input'])

        if setup_status:
            context_obj.extra_info['zap_object__action_data'] = answer_values
            context_obj.extra_info['zap_object__action_auth'] = auth_obj
            return True, "Action setup is done. "
        else:
            if answer_values=='Exit setup called':
                return False, answer_values

            return False, "Action setup was unsuccessful. "

    except Exception as e:
        return False, str(e)