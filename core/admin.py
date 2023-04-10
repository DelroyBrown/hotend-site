from django.contrib import admin

from .models import Sku, WorkOrder, UniqueID, Machine, Operator, ZeroingLog, MachineUsage


class AvailableModelAdmin(admin.ModelAdmin):
    """Allow staff users access to these models too."""
    def has_add_permission(self, request):
        return True

    def has_change_permission(self, request, obj=None):
        return True

    def has_module_permission(self, request):
        return True


class ReadOnlyAdmin(AvailableModelAdmin):
    def has_change_permission(self, request, obj=None):
        return False

    def has_view_permission(self, request, obj=None):
        return True


class MachineAdmin(AvailableModelAdmin):
    list_display = ["name", "hostname", "production_step", "idealised_cycle_time",
                    "planned_production_time", "required_ping_interval", "auto_update"]
    ordering = ["name"]


admin.site.register(UniqueID, AvailableModelAdmin)
admin.site.register(Machine, MachineAdmin)
admin.site.register(MachineUsage, AvailableModelAdmin)
admin.site.register(Operator, AvailableModelAdmin)
admin.site.register(Sku, AvailableModelAdmin)
admin.site.register(WorkOrder, AvailableModelAdmin)
admin.site.register(ZeroingLog, AvailableModelAdmin)