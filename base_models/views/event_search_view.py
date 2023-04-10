from datetime import timedelta

from django import forms
from django.db.models import Q

from core.models import Machine, Operator
from core.production_steps import PRODUCTION_STEPS
from core.utils import reverse
from ..base_view_classes.base_form_search_view import BaseFormSearchView, DATE_INPUT_FORMATS
from ..models import SingleItem


class EventSearchForm(forms.Form):
    item_sku = forms.CharField(max_length=255, label="SKU", required=False)
    item_uid = forms.CharField(
        max_length=255,
        label="Unique ID",
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "Serial no., barcode, etc"}),
    )

    machine = forms.ModelChoiceField(queryset=Machine.objects.all(), required=False, empty_label="")
    production_step = forms.ChoiceField(
        choices=[(None, ""), *PRODUCTION_STEPS.choices],
        initial=None,
        required=False,
    )

    operator = forms.ModelChoiceField(queryset=Operator.objects.all(), required=False, empty_label="")
    work_order = forms.CharField(max_length=255, required=False)

    from_date = forms.DateField(
        required=False,
        label="From date",
        input_formats=DATE_INPUT_FORMATS,
        widget=forms.TextInput(attrs={"placeholder": "dd-mm-yyyy"}),
    )
    to_date = forms.DateField(
        required=False,
        label="To date",
        input_formats=DATE_INPUT_FORMATS,
        widget=forms.TextInput(attrs={"placeholder": "dd-mm-yyyy"}),
    )

    failed = forms.NullBooleanField(
        required=False,
        widget=forms.Select(
            choices=((None, ""), (True, "Yes"), (False, "No"))
        ),
    )
    completed = forms.NullBooleanField(
        required=False,
        widget=forms.Select(
            choices=((None, ""), (True, "Yes"), (False, "No"))
        ),
    )


class EventSearchView(BaseFormSearchView):
    """
    A specific search view for Events.
    """
    form_class = EventSearchForm
    ordering = "-date_created"

    def build_filter(self, data):
        """
        Assemble a Django queryset filter from the form data, using Q objects.

        Each field is handled slightly differently. Some fields correspond to related models,
        not all Events have an `item__uid` filter available, and some need to match exactly
        whereas some are partial matches or ranges.

        If overriding this method, it's recommended to call super() and accumulate any changes
        onto the result of the super call using `&=`. Any fields that are removed from the form
        won't break the super call, since all lookups are done using `.get(field_name, None)`.
        """
        full_filter = Q()

        # SKU: Case-insensitive text matching on the item's SKU code, since a dropdown of SKUs would be
        # enormous, and being able to match multiple SKUs (e.g. searching "V6-" to find all V6 variants)
        # is useful functionality.
        if data.get("item_sku", None):
            full_filter &= Q(item__sku__code__icontains=data["item_sku"])

        # UID: Only SingleItems and subclasses have UIDs - BulkItems and AnyItems don't - so trying to
        # perform `item__uid` filters throws errors. As such, we need to filter SingleItem itself for the
        # required UID, then filter the Event queryset on whether any item is in the filtered SingleItems.
        if data.get("item_uid", None):
            item_or_nothing = SingleItem.objects.filter(uid__code__icontains=data["item_uid"])
            full_filter &= Q(item__in=item_or_nothing)

        # Machine: The field is a dropdown, so perform exact matching on the chosen Machine object
        if data.get("machine", None):
            full_filter &= Q(machine=data["machine"])

        # Production step: Another dropdown, so perform direct matching on the related Machine's production step
        if data.get("production_step", None):
            full_filter &= Q(machine__production_step=data["production_step"])

        # Operator: Another dropdown, another direct match on a ForeignKey field.
        if data.get("operator", None):
            full_filter &= Q(operator=data["operator"])

        # Work order: Case-insensitive matching on the work order code, since a dropdown would be
        # massive and unnavigable.
        if data.get("work_order", None):
            full_filter &= Q(work_order__code__icontains=data["work_order"])

        # Date matching: Both the from/to fields can be used on their own to have only a single bound
        # on the timeframe. Bump the `to_date` value up by a day, so the filter is inclusive.
        # This also allows someone to set an exact date by typing the same date twice.
        if data.get("from_date", None):
            full_filter &= Q(date_created__gte=data["from_date"])
        if data.get("to_date", None):
            full_filter &= Q(date_created__lte=(data["to_date"] + timedelta(days=1)))

        # Failure status: This is a NullBooleanField, so we need to compare `is not None` explicitly to
        # ensure we don't throw away "False" submissions.
        if data.get("failed", None) is not None:
            full_filter &= Q(failed=data["failed"])

        # Completed: Another NullBooleanField, so use an `is not None` comparison.
        if data.get("completed", None) is not None:
            full_filter &= Q(completed=data["completed"])

        # Fail State: These fields are implemented on the base `EventSearchForm`
        # If they exist in the submitted data, filter the queryset based on them.
        # Implemented using a MultipleChoiceField, for flexible filtering.
        if data.get("fail_state", None):
            full_filter &= self.get_multiselect_filter("fail_state", data["fail_state"])

        return full_filter


    def get_multiselect_filter(self, field_name, choices):
        """Return a filter that matches objects where the given field equals any one of the given choices."""
        result_filter = Q()
        for choice in choices:
            result_filter |= Q(**{field_name: choice})
        return result_filter


    def item_to_dict(self, event):
        """
        Return the event as a dictionary, but also nest its "human-readable" representation.
        This helps with displaying the fields nicely to the user.
        """
        data = event.to_dict()
        data["_readable_data"] = event.to_readable_dict()
        return data


    def get_action_url(self, page=0):
        return reverse(f"ajax:{self.project_name}_event_search", page=page)
