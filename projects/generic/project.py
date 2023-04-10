from django.urls import path

from base_models.models import BulkItem, Event
from base_models.project import Project
from . import models


generic_project = Project(
    name="generic",
    verbose_name="Generic rig",
    item_class=BulkItem,
    event_class=models.GenericEvent
)
