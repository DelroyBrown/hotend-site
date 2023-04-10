from django.contrib import admin

from base_models.admin import EventAdmin, ConfigurationAdmin
from . import models


admin.site.register(models.GenericEvent, EventAdmin)
