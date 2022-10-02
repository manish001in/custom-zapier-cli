# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from views import *
from models import *
from django.test import TestCase
from django.core.exceptions import PermissionDenied
from zapier.command_line import Context
from contextlib import contextmanager


@contextmanager
def mockRawInput(mock):
    original_raw_input = __builtins__["raw_input"]
    __builtins__["raw_input"] = lambda _: mock.pop(0)
    yield
    __builtins__["raw_input"] = original_raw_input


# Create your tests here.
class UserTestCase(TestCase):
    def setUp(self):
        self.username = "manish"
        self.password = "manish"
        self.email = "manish@example.com"

    def tests_user_create(self):
        self.assertIn(
            "New User Created and UserAuthenticated",
            new_user(self.username, self.password, None),
        )
        self.assertIn(
            "New User Created and UserAuthenticated",
            new_user(self.username + "1", self.password + "1", self.email),
        )

        with self.assertRaises(TypeError):
            new_user()
        with self.assertRaises(TypeError):
            new_user(self.username)

        with self.assertRaises(PermissionDenied):
            user_exists(self.username)
        self.assertEqual(user_exists("manish2"), "Enter email now:")

    def tests_user_authenticate(self):
        self.assertIn(
            "New User Created and UserAuthenticated",
            new_user(self.username, self.password, self.email),
        )

        with self.assertRaises(TypeError):
            authenticate_user()
        with self.assertRaises(TypeError):
            authenticate_user(self.username)
        with self.assertRaisesMessage(
            PermissionDenied,
            "User with username " + self.username + "abc" + " does not exist",
        ):
            authenticate_user(self.username + "abc", None)
        with self.assertRaisesMessage(PermissionDenied, "Incorrect credentials!"):
            authenticate_user(self.username, self.password + "abc")

        self.assertEqual(
            authenticate_user(self.username, self.password)[0], "UserAuthenticated"
        )


class ListingTestCase(TestCase):
    def setUp(self):

        string, self.user = new_user("manish", "manish", None)

        extra_data = {"project": "dropbox_app", "class": "DropBoxObject"}
        dropbox_app, _ = Apps.objects.get_or_create(
            name="DropboxApp",
            defaults={
                "description": "Dropbox is a file hosting service operated by the American company Dropbox, Inc., headquartered in San Francisco, California, that offers cloud storage, file synchronization, personal cloud, and client software.",
                "website": "https://dropbox.com",
                "extra_data": json.dumps(extra_data),
            },
        )
        extra_data = {"project": "google_apps", "class": "GoogleSheets"}
        gsheets_app, _ = Apps.objects.get_or_create(
            name="GoogleSheetsApp",
            defaults={
                "description": "Google Sheets is a spreadsheet program included as part of a free, web-based software office suite offered by Google within its Google Drive service.",
                "website": "https://docs.google.com/spreadsheets/",
                "extra_data": json.dumps(extra_data),
            },
        )

        setup_data = {
            "text_input": [
                {"name": "filename", "type": "str"},
                {"name": "path", "type": "str"},
                {"name": "check_update_duration_seconds", "type": "int"},
            ]
        }
        dropbox_file_update_trigger, _ = Triggers.objects.get_or_create(
            app=dropbox_app,
            name="FileUpdateTrigger",
            defaults={
                "description": "Checks when a file is updated in last certain seconds in dropbox",
                "setup_data": setup_data,
            },
        )

        setup_data = {
            "text_input": [
                {"name": "filename", "type": "str"},
                {"name": "path", "type": "str"},
            ]
        }
        dropbox_file_upload_action, _ = Actions.objects.get_or_create(
            app=dropbox_app,
            name="UploadAction",
            defaults={
                "description": "Uploads certain data to a file in dropbox(makes an update)",
                "setup_data": setup_data,
            },
        )

    def tests_listing(self):
        # Testing appropriate listing for triggers and checking response when given app doesn't exist
        with self.assertRaisesMessage(Exception, "does not exist."):
            list_app_triggers(app_name="dropbox1")
        self.assertIn("Triggers for app", list_app_triggers(app_name="DropboxApp"))
        self.assertIn(
            "No triggers exist for this app.",
            list_app_triggers(app_name="GoogleSheetsApp"),
        )

        # Testing appropriate listing for actions and checking response when given app doesn't exist
        with self.assertRaisesMessage(Exception, "does not exist."):
            list_app_actions(app_name="dropbox1")
        self.assertIn("Actions for app", list_app_actions(app_name="DropboxApp"))
        self.assertIn(
            "No actions exist for this app.",
            list_app_actions(app_name="GoogleSheetsApp"),
        )

        self.assertIn("You have no zaps available", list_zaps(user=self.user))


class ZapTestCase(TestCase):
    def setUp(self):

        self.context_obj = Context()
        _, self.user = new_user("manish", "manish", None)
        self.trigger_vals = None
        self.action_vals = None

        extra_data = {"project": "google_apps", "class": "GoogleSheets"}
        gsheets_app, _ = Apps.objects.get_or_create(
            name="GoogleSheetsApp",
            defaults={
                "description": "Google Sheets is a spreadsheet program included as part of a free, web-based software office suite offered by Google within its Google Drive service.",
                "website": "https://docs.google.com/spreadsheets/",
                "extra_data": json.dumps(extra_data),
            },
        )
        extra_data = {"project": "google_apps", "class": "GoogleMail"}
        gmail_app, _ = Apps.objects.get_or_create(
            name="GMailApp",
            defaults={
                "description": "Gmail is a free email service developed by Google.",
                "website": "https://gmail.com",
                "extra_data": json.dumps(extra_data),
            },
        )

        setup_data = {
            "text_input": [
                {
                    "name": "headers",
                    "type": "str",
                    "options": ["From", "To", "Date", "Subject"],
                    "input_string": "Select the headers you wanna add to your trigger data, if any, in a comma separated way.",
                    "example": "From,To or Subject,To",
                },
                {
                    "name": "mailBodyBool",
                    "type": "bool",
                    "not_empty": True,
                    "input_string": "Should we include the mail body text in trigger data?\nPlease answer in yes or no.",
                },
                {
                    "name": "search_query",
                    "type": "str",
                    "example": "from:someuser@example.com rfc822msgid:<somemsgid@example.com> is:unread",
                },
            ]
        }
        gmail_email_trigger, _ = Triggers.objects.get_or_create(
            app=gmail_app,
            name="EMailTrigger",
            defaults={
                "description": "Checks every few minutes and then processes the emails matching a certain query with the collected data sent to an action",
                "setup_data": setup_data,
            },
        )

        setup_data = {
            "text_input": [
                {"name": "sheet_id", "type": "str", "not_empty": True},
                {
                    "name": "sheet_name",
                    "type": "str",
                    "input_string": "Please enter sheet name such as sheet1, sheet2 etc. Do NOT enter the entire spreadsheet name.",
                },
                {
                    "name": "sheet_range",
                    "type": "str",
                    "not_empty": True,
                    "input_string": "Enter sheet range in A1 notation, the rows will be appended after the range.",
                    "example": "A1:E1",
                },
            ]
        }
        gsheets_appendrow_action, _ = Actions.objects.get_or_create(
            app=gsheets_app,
            name="AppendRowAction",
            defaults={
                "description": "Takes the received data and adds a row to the google sheets",
                "setup_data": setup_data,
            },
        )

    def tests_zap(self):
        # Assuming authentication for trigger and action app is not an issue

        trigger_setup_data = Triggers.objects.get().setup_data
        action_setup_data = Actions.objects.get().setup_data

        trigger_answers = ["From,To", "yes", "from:manish"]
        trigger_answers_1 = ["", "no", ""]
        trigger_fail_answers_1 = ["From,No,Why", "no", ""]
        trigger_fail_answers_2 = ["From,To", "noooo", "from:uber"]

        # Testing different inputs for triggers to get data from the user
        with mockRawInput(trigger_fail_answers_1):
            self.assertEqual(
                False,
                get_text_input_setup_data(trigger_setup_data["text_input"], True)[0],
            )

        with mockRawInput(trigger_fail_answers_2):
            self.assertEqual(
                False,
                get_text_input_setup_data(trigger_setup_data["text_input"], True)[0],
            )

        with mockRawInput(trigger_answers_1):
            status, self.trigger_vals = get_text_input_setup_data(
                trigger_setup_data["text_input"], True
            )
            self.assertEqual(True, status)

        with mockRawInput(trigger_answers):
            status, self.trigger_vals = get_text_input_setup_data(
                trigger_setup_data["text_input"], True
            )
            self.assertEqual(True, status)

        # Testing different inputs for actions to get data from the user
        action_answers = ["1_dskjhc2873", "sheet1", "A1:E1"]
        action_answers_1 = ["", "1_dskjhc2873", "sheet1", "A1:E1"]

        with mockRawInput(action_answers_1):
            status, self.action_vals = get_text_input_setup_data(
                action_setup_data["text_input"], True
            )
            self.assertEqual(True, status)

        with mockRawInput(action_answers):
            status, self.action_vals = get_text_input_setup_data(
                action_setup_data["text_input"], True
            )
            self.assertEqual(True, status)

        # Again assuming that authentication is handled. We try to create a zap
        trigger_auth = {}
        action_auth = {}

        self.context_obj.extra_info["zap_object__name"] = "testzap"

        self.context_obj.extra_info["trigger_app_trigger"] = Triggers.objects.get()
        self.context_obj.extra_info["action_app_action"] = Actions.objects.get()

        self.context_obj.extra_info["zap_object__trigger_auth"] = trigger_auth
        self.context_obj.extra_info["zap_object__action_auth"] = action_auth

        self.context_obj.extra_info["zap_object__trigger_data"] = self.trigger_vals
        self.context_obj.extra_info["zap_object__action_data"] = self.action_vals

        # Providing a None user, leads to inability to find the user profile and failing of the function
        self.assertEqual(False, make_zap_object(self.context_obj)[0])
        self.assertIn("invalid literal", make_zap_object(self.context_obj)[1])

        self.context_obj.user = self.user
        self.assertEqual((True, ""), make_zap_object(self.context_obj))

        # Trying to update zap status to inactive
        self.assertIn(
            "Successfully marked zap",
            update_zap(zap_name="testzap", mark_status="inactive", user=self.user),
        )

        # No zap with this name exists, so zap query does not exist is expected.
        self.assertIn(
            "query does not exist",
            update_zap(zap_name="testzap_fail", mark_status="tive", user=self.user),
        )

        # No zap with user None exists, so zap query does not exist is expected.
        self.assertIn(
            "query does not exist",
            update_zap(zap_name="testzap_fail", mark_status="tive", user=None),
        )
