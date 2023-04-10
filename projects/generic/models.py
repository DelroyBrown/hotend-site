from django import forms
from django.db import models

from base_models.models import Configuration, Event
from core.production_steps import PRODUCTION_STEPS


class GenericEvent(Event):
    def __str__(self):
        return F"Generic event from {self.date_created}"
