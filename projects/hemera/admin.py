from django.contrib import admin

from base_models.admin import EventAdmin, ConfigurationAdmin
from .models import (
    HemeraGreaseConfig,
    HemeraGreaseEvent,
)

admin.site.register(HemeraGreaseConfig, ConfigurationAdmin)
admin.site.register(HemeraGreaseEvent, EventAdmin)
