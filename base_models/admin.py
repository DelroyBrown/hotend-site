from django.contrib import admin

from core.admin import AvailableModelAdmin, ReadOnlyAdmin
from .models import Event, AnyItem, BulkItem, SingleItem


class EventAdmin(ReadOnlyAdmin):
    list_display = ["item", "date_created", "work_order", "production_step", "operator", "result"]
    search_fields = [
        "work_order__code",
        "machine__name", "machine__hostname", "machine__production_step",
        "operator__code", "operator__name",
    ]
    list_filter = [
        "failed",
        "machine__production_step",
    ]

    def machine_name(self, obj):
        return obj.machine.name
    machine_name.short_description = "Machine"

    def production_step(self, obj):
        return obj.machine.production_step

    def result(self, obj):
        result = obj.fail_state
        if result == "None":
            result = "Passed"
        if obj.completed is False:
            result == "Incomplete"
        return result


class AnyItemAdmin(AvailableModelAdmin):
    list_display = ["__str__", "sku"]
    search_fields = ["sku__code"]


class BulkItemAdmin(AvailableModelAdmin):
    list_display = ["sku", "work_order"]
    search_fields = ["sku__code", "work_order__code"]


class SingleItemAdmin(AvailableModelAdmin):
    list_display = ["uid", "sku"]
    search_fields = ["sku__code", "uid__code"]


class ConfigurationAdmin(AvailableModelAdmin):
    list_display = ["sku", "production_step_field"]
    search_fields = ["sku", "production_step_field"]


admin.site.register(Event, EventAdmin)
admin.site.register(AnyItem, AnyItemAdmin)
admin.site.register(BulkItem, BulkItemAdmin)
admin.site.register(SingleItem, SingleItemAdmin)
