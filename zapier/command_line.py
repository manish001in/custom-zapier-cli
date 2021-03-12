from django.core.exceptions import PermissionDenied, ValidationError, ObjectDoesNotExist
from django.core.validators import validate_email
from core_engine import views
from core_engine.models import Triggers, Actions
from logs import core_logger
from django.conf import settings

class Context(object):
    def __init__(self):
        self.user=''
        self.logged_in=False
        self.email=''
        self.current_path=[]
        self.extra_info = {}

def color(string):
    return settings.YELLOWSTARTCOLOR+str(string)+settings.ENDCOLOR

def greenColor(string):
    return settings.GREENSTARTCOLOR+str(string)+settings.ENDCOLOR

def start_app():

    return "Welcome to LilZaps, an experiment to create Zapier in command line terminal.\n" \
          "To start, either login or create a new user.\n" \
          "1. To Login, enter command 'login'\n" \
          "2. To create a new user, enter command 'createuser'\n\n" + color("Enter input:")

def logged_in_options(context_obj):

    return "You have now logged in to LilZaps "+str(context_obj.user.username)+", an experiment to create Zapier in command line terminal.\n" \
          "You can do following actions now.\n" \
          "1. List all available apps, enter command 'listapps'\n" \
          "2. List all your zaps, enter command 'listzaps'\n" \
          "3. Create a zap, enter command 'createzap'\n" \
          "Note: Use command 'mainmenu' to reach this menu at any time/stage\n" + color("Enter your command:")
           

def parse_command(command, context_obj):
    return_string = ''
    
    if not context_obj.logged_in:
        return_string = login_handling(command, context_obj)

    elif command=='' and context_obj.current_path==[]:
        return_string = logged_in_options(context_obj)

    elif command=='mainmenu':
        context_obj.current_path = []
        return_string = logged_in_options(context_obj)

    elif command=='createzap' or (len(context_obj.current_path)>0 and context_obj.current_path[0]=='createzap'):
        return_string = create_zap(command, context_obj)

    else:
        return_string = listing_handling(command, context_obj)
    
    return return_string

def login_handling(command, context_obj):
    return_string = ''

    if len(context_obj.current_path)==0:

        if command=='login':
            print "Please login with your username and password.\n"
            context_obj.current_path.append('login')
            return_string = color("Enter your username:")
        elif command=='createuser':
            print "Let's create a new user for you.\n"
            context_obj.current_path.append('createuser')
            return_string = color("Enter the username that you want to setup:")
        else:
            print "To start, either login or create a new user.\n" \
                    "1. To Login, enter command 'login'\n" \
                    "2. To create a new user, enter command 'createuser'\n"+color("Enter input:")

    else:
        current_path = '__'.join(context_obj.current_path)

        if current_path=='createuser':
            try:
                return_string = views.user_exists(command)
                context_obj.user=command
                context_obj.current_path.append("username")
            
            except PermissionDenied:
                print "That username already exists,\n"
                return_string = color("Enter a different username:")
        
        elif current_path=='createuser__username':
            try:
                validate_email(command)
                return_string = color("Please enter the password now:")
                context_obj.email=command
                context_obj.current_path.append("email")
            
            except ValidationError:
                print "Invalid email\n"
                return_string = color("Enter a correct email:")
        
        elif current_path=='createuser__username__email':
            try:
                return_string, context_obj.user = views.new_user(context_obj.user, command, context_obj.email)
                context_obj.logged_in=True
                context_obj.current_path=[]
                return_string = greenColor(return_string)+'\n'+logged_in_options(context_obj)
        
            except Exception as e:
                core_logger.info("CommandLine:ErrorNewUser:"+str(e))
                print "Unknown error occured "+str(e)+"\n"
                context_obj.current_path=[]
                return_string = color("Please exit and start again\n")

        elif current_path=='login':
            context_obj.user=command
            context_obj.current_path.append("username")
            return_string = color("Enter password now:")
        
        elif current_path=='login__username':
            try:
                return_string, context_obj.user = views.authenticate_user(context_obj.user, command)
                context_obj.email=context_obj.user.email
                context_obj.logged_in=True
                context_obj.current_path=[]
                return_string = greenColor(return_string)+'\n'+logged_in_options(context_obj)
        
            except Exception as e:
                core_logger.info("CommandLine:ErrorAuthenticateUser:"+str(e))
                print "Following error occured "+str(e)+"\n"
                context_obj.current_path=[]
                return_string = color("Please exit and start again\n")

    return return_string

def listing_handling(command, context_obj):
    return_string = ''
    if len(context_obj.current_path)<1:
        if command=='listapps':
            try:
                return_string = greenColor(views.list_apps())
                return_string += "\nSelect one of these app to see triggers and actions associated with it, "+color("type command 'select <app name>' :")
                context_obj.current_path.append('listapps')
            except Exception as e:
                core_logger.info("CommandLine:ListingAppsError:"+str(e))
                print "Following error occured "+str(e)+"\n"
                return_string = color("Please 'exit' and start again\n")
        elif command=='listzaps':
            try:
                return_string = greenColor(views.list_zaps(user=context_obj.user))
                return_string += "\nTo activate a zap, enter command 'mark <zapname> active'" \
                                 "\nTo deactivate a zap, enter command 'mark <zapname> inactive'" \
                                 "\nElse use command 'mainmenu' to go to the main menu.\n"+color("Enter your command:")
                context_obj.current_path.append('listzaps')
            except Exception as e:
                core_logger.info("CommandLine:ListingZapsError:"+str(e))
                print "Following error occured "+str(e)+"\n"
                return_string = color("Please 'exit' and start again\n")

    else:
        current_path = '__'.join(context_obj.current_path)
        if current_path=='listapps':
            try:
                selected_app = command.split('select')[1].strip()
                triggers = views.list_app_triggers(app_name=selected_app)
                actions = views.list_app_actions(app_name=selected_app)
                return_string = greenColor("For app, "+str(selected_app)+"\n\n"+triggers+"\n"+actions+"\n")
                context_obj.current_path = []
                return_string+="\n\n"+logged_in_options(context_obj)
            except ObjectDoesNotExist as e:
                print "Following error occured "+str(e)+"\n"
                return_string = color("Please choose an existing app, type command 'select <app name>' without the quotes\n")
        if current_path=='listzaps':
            try:
                mark_status = command.split()[-1]
                selected_zap = ' '.join(command.split()[1:-1])
                return_string = greenColor(views.update_zap(zap_name=selected_zap, mark_status=mark_status, user=context_obj.user))
                context_obj.current_path = []
                return_string+="\n\n\n"+logged_in_options(context_obj)
            except Exception as e:
                print "Following error occured "+str(e)+"\n"
                return_string = color("Please make sure you have given the right command or 'exit' and start again.\n")
    return return_string

def create_zap(command, context_obj):
    return_string = ''
    if len(context_obj.current_path)==0:
        if command=='createzap':
            return_string = greenColor(views.list_apps('trigger'))
            return_string += "\nLet's set up your trigger app, Select one of these app to see triggers associated with it, "+color("type command 'select <app name>' :")
            context_obj.current_path.append('createzap')

    else:
        current_path = '__'.join(context_obj.current_path)
        if current_path=='createzap':
            try:
                selected_app = command.split('select')[1].strip()
                triggers = greenColor(views.list_app_triggers(app_name=selected_app))

                return_string = "You have chosen "+str(selected_app)+"\n"+str(triggers)+"\nSelect the trigger you want to choose, "+color("use command '<trigger name>' :")

                context_obj.extra_info['trigger_app']=selected_app
                context_obj.current_path.append('triggerapp')

            except Exception as e:
                core_logger.info("CommandLine:CreateZapError:TriggerAppSelect:"+str(e))
                print "Following error occured "+str(e)+"\n"
                return_string = "Please choose an existing app, "+color("type command 'select <app name>' without the quotes:\n")

        elif current_path=='createzap__triggerapp':
            try:
                selected_trigger = command
                trigger = Triggers.objects.get(app__name=context_obj.extra_info['trigger_app'], name=selected_trigger)

                print "You have chosen "+str(selected_trigger)+" as your trigger\nLet's set that up.\n"

                context_obj.extra_info['trigger_app_trigger']=trigger
                status, return_string = views.handle_trigger_setup(command, context_obj)

                return_string = greenColor(return_string)

                if status:
                    context_obj.current_path.remove('triggerapp')
                    context_obj.current_path.append('triggerset')                
                else:
                    if return_string=='Exit setup called':
                        context_obj.extra_info['trigger_app_trigger']=None
                        return_string = color("You exited the trigger setup. Let's try selecting the trigger again or you can type 'exit' to exit the program or 'mainmenu' to go to the mainmenu.")
                        triggers = greenColor(views.list_app_triggers(app_name=context_obj.extra_info['trigger_app']))
                        return_string += "\nYou have chosen "+str(context_obj.extra_info['trigger_app'])+"\n"+str(triggers)+"\nSelect the trigger you want to choose, "+color("use command '<trigger name>' :")
                    else:
                        return_string = color("Some issue occured, try again by pressing enter or exit the app and try again.\n")

            except Exception as e:
                core_logger.info("CommandLine:CreateZapError:TriggerAppSetup:"+str(e))
                print "Following error occured "+str(e)+"\n"
                return_string = "Please choose an existing trigger, "+color("type command '<trigger name>' without the quotes:\n")

        elif current_path=='createzap__triggerset':

            return_string = greenColor(views.list_apps('action'))
            return_string += "\nLet's set up your action app, Select one of these app to see actions associated with it, "+color("type command 'select <app name>' :")
            context_obj.current_path.append('actionapp')

        elif current_path=='createzap__triggerset__actionapp':
            try:
                selected_app = command.split('select')[1].strip()
                actions = greenColor(views.list_app_actions(app_name=selected_app))

                return_string = "You have chosen "+str(selected_app)+"\n"+str(actions)+"\nSelect the action you want to choose, "+color("use command '<action name>' :")

                context_obj.extra_info['action_app']=selected_app
                context_obj.current_path.append('action')

            except Exception as e:
                core_logger.info("CommandLine:CreateZapError:ActionAppSelect:"+str(e))
                print "Following error occured "+str(e)+"\n"
                return_string = color("Please choose an existing app, type command 'select <app name>' without the quotes:\n")

        elif current_path=='createzap__triggerset__actionapp__action':
            try:
                selected_action = command
                action = Actions.objects.get(app__name=context_obj.extra_info['action_app'], name=selected_action)

                print "You have chosen "+str(selected_action)+" as your action\nLet's set that up.\n"

                context_obj.extra_info['action_app_action']=action
                status, return_string = views.handle_action_setup(command, context_obj)

                return_string = greenColor(return_string)

                if status:
                    context_obj.current_path = ['createzap','triggerset','actionset']
                    return_string += "\nEnter the name of this zap. Please try to keep it different than your other zap names.\n"+color("Enter the name:")
                else:
                    if return_string=='Exit setup called':
                        context_obj.extra_info['action_app_action']=None
                        return_string = color("You exited the action setup. Let'try selecting the action again or you can type 'exit' to exit the program or 'mainmenu' to go to the mainmenu.")
                        action = greenColor(views.list_app_actions(app_name=context_obj.extra_info['action_app']))
                        return_string += "\nYou have chosen "+str(context_obj.extra_info['action_app'])+"\n"+str(action)+"\nSelect the action you want to choose, "+color("use command '<action name>' :")
                    else:
                        return_string = color("Some issue occured, please try again or exit and try again.\n")

            except Exception as e:
                core_logger.info("CommandLine:CreateZapError:ActionAppSetup:"+str(e))
                print "Following error occured "+str(e)+"\n"
                return_string = "Please choose an existing action, "+color("type command '<action name>' without the quotes:\n")

        elif current_path=='createzap__triggerset__actionset':
            try:
                context_obj.extra_info['zap_object__name']=command
                created, return_string = views.make_zap_object(context_obj)

                if created:
                    context_obj.current_path = []
                    return_string += "\nYour zap "+str(command)+" has been created and set to run every 15 minutes starting now. It will check for the trigger and then run the action if the trigger is a success.\n" \
                                      "You can mark it not running if needed. Thank you for using us.\nType 'mainmenu' to check the mainmenu"
                else:
                    context_obj.extra_info = {}
                    context_obj.current_path = []
                    return_string += "Could not make the zap, Some issue occured, please exit and try again. Or, press enter.\n"

            except Exception as e:
                context_obj.extra_info = {}
                context_obj.current_path = []
                core_logger.info("CommandLine:CreateZapError:ZapName:"+str(e))
                print "Following error occured "+str(e)+"\n"
                return_string = "Following error occured "+str(e)+"\nPlease exit or try again.\nOr, Press enter."
    
    return return_string