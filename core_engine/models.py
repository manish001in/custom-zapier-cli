# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.contrib.auth.models import User
from django.db import models
from django.contrib.postgres.fields import JSONField
import datetime

# Model user profile, mapped to User, can store additional values for users
class UserProfile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_date = models.DateTimeField(auto_now_add=True, null=True)
    modified_date = models.DateTimeField(auto_now=True, null=True)

class Apps(models.Model):
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField()
    website = models.URLField()
    extra_data = models.TextField()
    created_date = models.DateTimeField(auto_now_add=True, null=True)
    modified_date = models.DateTimeField(auto_now=True, null=True)

class Triggers(models.Model):
    app = models.ForeignKey(Apps, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    description = models.TextField()
    setup_data = JSONField()
    created_date = models.DateTimeField(auto_now_add=True, null=True)
    modified_date = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        unique_together = ("app", "name")

class Actions(models.Model):
    app = models.ForeignKey(Apps, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    description = models.TextField()
    setup_data = JSONField()
    created_date = models.DateTimeField(auto_now_add=True, null=True)
    modified_date = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        unique_together = ("app", "name")

class Zaps(models.Model):
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    active = models.BooleanField(default=False)
    trigger = models.ForeignKey(Triggers, on_delete=models.CASCADE)
    action = models.ForeignKey(Actions, on_delete=models.CASCADE)
    trigger_app_auth = JSONField(default=None)
    action_app_auth = JSONField(default=None)
    zap_input_data = models.TextField()
    last_run = models.DateTimeField(null=True)
    created_date = models.DateTimeField(auto_now_add=True, null=True)
    modified_date = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        unique_together = ("user_profile", "name")