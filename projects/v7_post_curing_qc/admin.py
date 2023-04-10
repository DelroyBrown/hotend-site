import csv

from django.contrib import admin
from django.http import HttpResponse

from base_models.admin import EventAdmin, ConfigurationAdmin
from .models import (
    V7CuringQCConfig,
    V7CuringQCEvent,
)


class V7CuringQCEventAdmin(EventAdmin):
    list_display = EventAdmin.list_display + ["successful_thermal_cycles"]
    actions = ["export_all_to_csv"]

    def export_all_to_csv(self, request, queryset):
        events = V7CuringQCEvent.objects.all()

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = ("attachment; filename=v7_qc_events.csv")
        writer = csv.writer(response)

        writer.writerow([
            "SKU",
            "Part ID",
            "Work order",
            "Completed",
            "Fail State",
            "Leakage tested",
            "Circuit tested",
            "Thermal cycling tested",
            "Successful thermal cycles",
            "Temperatures",
        ])

        for event in events:
            writer.writerow([
                event.item.sku,
                event.item.uid,
                event.work_order,
                event.completed,
                event.fail_state,
                event.tested_leakage,
                event.tested_circuit,
                event.tested_thermal_cycling,
                event.successful_thermal_cycles,
                *(event.log_temperatures),
            ])

        return response
    export_all_to_csv.short_description = "Export all events to a CSV"


admin.site.register(V7CuringQCConfig, ConfigurationAdmin)
admin.site.register(V7CuringQCEvent, V7CuringQCEventAdmin)
