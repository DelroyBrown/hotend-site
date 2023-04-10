from django.urls import path

from base_models.models import SingleItem
from base_models.project import Project
from . import models
from .views.api import GetPastEvents


hemera_grease_dispenser_project = Project(
    name="hemera_grease_dispenser",
    verbose_name="Hemera greasing rig",
    item_class=SingleItem,
    configuration_class=models.HemeraGreaseConfig,
    event_class=models.HemeraGreaseEvent,
    additional_api_urls=[
        path(
            "past_events/<int:uid>/",
            GetPastEvents.as_view(),
            name="hemera_grease_dispenser_past_events"
        ),
    ],
)
