from datetime import timedelta

from django.db.models import Q
from django.forms import model_to_dict

from base_models.base_view_classes.ajax import AjaxCreateFormView, AjaxUpdateFormView
from base_models.base_view_classes.base_form_search_view import BaseFormSearchView
from base_models.models.item import SingleItem
from .. import forms, models
from ..forms import ZeroingLogSearchForm, MachineUsageForm
from ..models import ZeroingLog, MachineUsage
from ..utils import reverse


class SkuCreateView(AjaxCreateFormView):
    form_class = forms.SkuCreateForm
    queryset = models.Sku.objects.all()
    id_field = "code"

    def get_action_url(self):
        return reverse("ajax:sku_create", code=self.get_object_id())


class SkuUpdateView(AjaxUpdateFormView):
    form_class = forms.SkuUpdateForm
    queryset = models.Sku.objects.all()
    id_field = "code"

    def get_action_url(self):
        return reverse("ajax:sku_update", code=self.get_object_id())


class OperatorCreateView(AjaxCreateFormView):
    form_class = forms.OperatorCreateForm
    queryset = models.Operator.objects.all()
    id_field = "code"

    def get_action_url(self):
        return reverse("ajax:operator_create", code=self.get_object_id())


class OperatorUpdateView(AjaxUpdateFormView):
    form_class = forms.OperatorUpdateForm
    queryset = models.Operator.objects.all()
    id_field = "code"

    def get_action_url(self):
        return reverse("ajax:operator_update", code=self.get_object_id())


class MachineCreateView(AjaxCreateFormView):
    form_class = forms.MachineCreateForm
    queryset = models.Machine.objects.all()
    id_field = "hostname"

    def get_action_url(self):
        return reverse("ajax:machine_create", hostname=self.get_object_id())


class MachineUpdateView(AjaxUpdateFormView):
    form_class = forms.MachineUpdateForm
    queryset = models.Machine.objects.all()
    id_field = "hostname"

    def get_action_url(self):
        return reverse("ajax:machine_update", hostname=self.get_object_id())


class ZeroingLogSearchView(BaseFormSearchView):
    """
    A specific search view for ZeroingLogs.
    """
    form_class = ZeroingLogSearchForm
    queryset = ZeroingLog.objects.all()
    ordering = "-date"

    def build_filter(self, data):
        """Assemble a Django queryset filter from the form data, using Q objects."""
        full_filter = Q()

        # Machine: The field is a dropdown, so perform exact matching on the chosen Machine object
        if data.get("machine", None):
            full_filter &= Q(machine=data["machine"])

        # Production step: Another dropdown, so perform direct matching on the related Machine's production step
        if data.get("production_step", None):
            full_filter &= Q(machine__production_step=data["production_step"])

        # Date matching: Both the from/to fields can be used on their own to have only a single bound
        # on the timeframe. Bump the `to_date` value up by a day, so the filter is inclusive.
        # This also allows someone to set an exact date by typing the same date twice.
        if data.get("from_date", None):
            full_filter &= Q(date__gte=data["from_date"])
        if data.get("to_date", None):
            full_filter &= Q(date__lte=(data["to_date"] + timedelta(days=1)))

        return full_filter


    def item_to_dict(self, zeroing_log):
        """
        Return a dictionary representation of this Event and some of its related models.

        Start with model_to_dict, and then fill in some fields that are shown with incomplete data
        or only pk fields. Exclude log fields, since they can get quite large; they can be retrieved
        separately.
        """
        result = model_to_dict(zeroing_log)

        result["date"] = zeroing_log.date.strftime("%d/%m/%Y %H:%M:%S")
        result["machine"] = model_to_dict(zeroing_log.machine)
        result["operator"] = model_to_dict(zeroing_log.operator)

        return result


    def get_action_url(self, page=0):
        return reverse("ajax:zeroing_search", page=page)


class MachineUsageSearchView(BaseFormSearchView):
    """
    A specific search view for ZeroingLogs.
    """
    form_class = MachineUsageForm
    queryset = MachineUsage.objects.all()
    ordering = "-logged_in_at"

    def build_filter(self, data):
        """Assemble a Django queryset filter from the form data, using Q objects."""
        full_filter = Q()

        # Machine: The field is a dropdown, so perform exact matching on the chosen Machine object
        if data.get("machine", None):
            full_filter &= Q(machine__in=data["machine"])

        # Production step: Another dropdown, so perform direct matching on the related Machine's production step
        if data.get("operator", None):
            full_filter &= Q(operator__in=data["operator"])

        # Date matching: Both the from/to fields can be used on their own to have only a single bound
        # on the timeframe. Bump the `to_date` value up by a day, so the filter is inclusive.
        # This also allows someone to set an exact date by typing the same date twice.
        if data.get("from_date", None):
            full_filter &= Q(logged_in_at__gte=data["from_date"])
        if data.get("to_date", None):
            full_filter &= Q(logged_out_at__lte=(data["to_date"] + timedelta(days=1)))

        if data.get("logged_in", None):
            full_filter &= Q(logged_out_at=None)

        return full_filter


    def item_to_dict(self, usage):
        """
        Return a dictionary representation of this Event and some of its related models.

        Start with model_to_dict, and then fill in some fields that are shown with incomplete data
        or only pk fields. Exclude log fields, since they can get quite large; they can be retrieved
        separately.
        """
        result = model_to_dict(usage)

        result["logged_in_at"] = usage.logged_in_at.strftime("%d/%m/%Y %H:%M:%S")
        result["logged_out_at"] = usage.logged_out_at.strftime("%d/%m/%Y %H:%M:%S") if usage.logged_out_at else None
        result["last_ping"] = usage.last_ping.strftime("%d/%m/%Y %H:%M:%S")
        result["machine"] = model_to_dict(usage.machine)
        result["operator"] = model_to_dict(usage.operator)

        return result


    def get_action_url(self, page=0):
        return reverse("ajax:machine_usage", page=page)
