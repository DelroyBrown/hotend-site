import pandas as pd
from datetime import datetime

from django.contrib.postgres.fields import ArrayField
from django.core.validators import MinValueValidator
from django.db import models, IntegrityError
from django import forms
from django.forms import model_to_dict
from polymorphic.models import PolymorphicModel
from rest_framework.authentication import SessionAuthentication
from rest_framework.generics import CreateAPIView, UpdateAPIView, RetrieveAPIView
from rest_framework.response import Response as RestFrameworkResponse

from core.models import Machine, Operator, WorkOrder, MachineUsage
from core.utils import readable_field_name
from .item import AnyItem
from ..generate_serializer_mixin import GenerateSerializerMixin
from ..non_polymorphic_cascade import NON_POLYMORPHIC_CASCADE



class Event(GenerateSerializerMixin, PolymorphicModel):
    """
    Represents an occurrence of a production step (see core/production_steps.py) to an item.

    Expected to contain information about the overall results of the operation. Subclasses should implement data
    fields to store said information.

    Provides the following fields:
      * item - The item (single or bulk) that this Event applies to.
      * machine, operator, work_order - Where and when this Event took place.
      * date_created - Suitable for use as a start date for the operation, this field is set when
        the Event instance is created. It can be overridden with an exact value if needs be.
      * date_updated - Set to the current date and time whenever the Event is saved. Later on, this serves as a
        record of when the Event was completed.
      * failed - Tracks whether the Event recorded a failure or not. Set this to True when a failure is detected;
        an event with failed=False hasn't failed *yet*.
      * completed - Set this to true to confirm that the Event is finished.

    Moment-to-moment logging, if desired, is implemented using ArrayFields. The base model just has one.
      * log_timepoints - A list of timepoint values, each of which is a float value holding the number of
        seconds since the beginning of the Event. Optional - defaults to an empty list if not used.
        Should be strictly ordered for best effect.

    All logging ArrayFields are expected to be of the same length, and a given index in each list should correspond
    to the same timepoint.

    When subclassing Event and adding logging result fields, set _log_fields to a list of all log result fields,
    excluding log_timepoints.
    """
    item = models.ForeignKey(AnyItem, related_name="events", on_delete=NON_POLYMORPHIC_CASCADE)

    machine = models.ForeignKey(Machine, related_name="events", on_delete=NON_POLYMORPHIC_CASCADE)
    operator = models.ForeignKey(Operator, related_name="events", on_delete=NON_POLYMORPHIC_CASCADE)
    work_order = models.ForeignKey(WorkOrder, related_name="events", on_delete=NON_POLYMORPHIC_CASCADE)

    date_created = models.DateTimeField(default=datetime.now, editable=False)
    date_updated = models.DateTimeField(auto_now=True)

    failed = models.BooleanField(default=False)
    completed = models.BooleanField(default=False)
    fail_state = models.CharField(
        max_length=255,
        default="None"
    )

    log_timepoints = ArrayField(
        base_field=models.FloatField(
            validators=[MinValueValidator(0)],
        ),
        default=list,
        verbose_name="Timepoints (s)",
    )

    # A list of all the log results fields on an Event subclass, *excluding* `log_timepoints`.
    # This needs to be set (manually) in order for logs to be processed correctly.
    _log_fields = []

    class Meta:
        ordering = ["-date_created"]

    def __str__(self):
        return F"{self.machine.production_step} of {self.item} as part of {self.work_order}, {self.date_created}"

    def save(self, *args, **kwargs):
        if self.failed is True:
            if self.fail_state == "None":
                self.fail_state = "Unknown"
        return super().save(*args, **kwargs)

    def get_log_results(self):
        """
        Collect all the log results ArrayFields together into a single object.
        Validate them, and raise an exception if any of them are the wrong length.

        The results are of the following form:

        {
            timepoints: [ ... ],
            results: [
                {name: readable_field_name, data: [ ... ]},
            ]
        }

        where readable_field_name is a lightly-processed version of the field that
        is meant to be more clearly human-readable.
        """
        results = []

        for field_name in self._log_fields:
            data = getattr(self, field_name)
            if len(data) != len(self.log_timepoints):
                raise IntegrityError(
                    f"Log results field {field_name} has {len(data)} entries "
                    f"when it should have {len(self.log_timepoints)}"
                )

            results.append({
                "name": readable_field_name(self, field_name),
                "data": data,
            })

        return {
            "timepoints": self.log_timepoints,
            "results": results,
        }

    def to_dict(self, *, exclude_fields=None):
        """
        Return a dictionary representation of this model, with the standard ForeignKey fields
        nested as dictionaries as well.
        """
        to_exclude = ["log_timepoints", "date_created", "date_updated"] + self._log_fields + (exclude_fields or [])
        result = model_to_dict(self, exclude=to_exclude)

        result["date_and_time"] = self.date_created.strftime("%d/%m/%Y %H:%M:%S")
        result["duration"] = str(self.date_updated - self.date_created)

        result["item"] = model_to_dict(self.item)
        result["machine"] = model_to_dict(self.machine)
        result["operator"] = model_to_dict(self.operator)

        return result

    def to_readable_dict(self):
        """
        Return a dictionary of the Event's data with field names parsed into nice-looking,
        human-readable labels.
        """
        data_dict = self.to_dict(exclude_fields=["event_ptr"])
        item = data_dict.pop("item")

        # Handle some fields specifically. Collapse nested objects into flat values, and add a separate
        # field for the item UID.
        result = {
            "Database primary key": data_dict.pop("id"),
            "Item UID": item.get("uid", "N/A"),
            "Item SKU": item["sku"],

            # These fields aren't receiving any special processing - they're just being moved near the top
            # of the list, so they display above the rest of the Event's data.
            "Work order": data_dict.pop("work_order"),
            "Started at": data_dict.pop("date_and_time"),
            "Duration": data_dict.pop("duration"),

            "Machine": data_dict.pop("machine")["name"],
            "Operator": data_dict.pop("operator")["name"],
        }

        for key, value in data_dict.items():
            if isinstance(value, bool):
                value = "Yes" if value else "No"

            result[readable_field_name(self, key)] = value

        return result

    @classmethod
    def events_to_df(cls, events, include_fields=None, exclude_fields=None):
        fields = [field.name for field in cls._meta.get_fields()].copy()
        excluded_fields = ['polymorphic_ctype', 'event_ptr', 'log_timepoints'] + cls._log_fields + (exclude_fields or [])
        [fields.remove(field) for field in excluded_fields]
        has_uid = getattr(events.first().item, 'uid', False)
        if has_uid is not False:
            fields += ['item__singleitem__uid']
        fields += ['item__sku', 'machine__name', 'operator__name'] + (include_fields or [])

        df = pd.DataFrame(events.values(*fields))
        return df

    @classmethod
    def events_to_readable_df(cls, events):
        df = cls.events_to_df(events)
        results = pd.DataFrame()

        results["Event ID"] = df["id"]

        results['Item UID'] = getattr(df, "item__singleitem__uid", None)
        results["Item SKU"] = df["item__sku"]

        results["Work order"] = df["work_order"]
        results["Started at"] = df["date_created"].apply(lambda x: x.strftime("%d/%m/%Y %H:%M:%S"))
        results["Duration"] = (df["date_updated"] - df["date_created"])
        results["Time since prev"] = (df['date_created'] - df['date_created'].shift(-1)).astype(str)

        results["Machine"] = df["machine__name"]
        results["Operator"] = df["operator__name"]

        results["Failed"] = df["failed"]
        results["Completed"] = df["completed"]
        results["Fail State"] = df["fail_state"]

        sub_fields = [field.name for field in cls._meta.get_fields(include_parents=False)].copy()
        excluded_fields = ['event_ptr'] + cls._log_fields
        [sub_fields.remove(field) for field in excluded_fields]
        for field in sub_fields:
            results[readable_field_name(cls, field)] = df[field]

        return results

    @classmethod
    def events_to_log_df(cls, events):
        def expand_row(row):
            event_id = row['id']
            row_df = pd.DataFrame(columns=['id', 'log_timepoints'])

            row_df['log_timepoints'] = row['log_timepoints']
            for field in cls._log_fields:
                if not getattr(row, field, None):
                    return row_df
                row_df[field] = row[field]
            row_df['id'] = event_id

            return row_df

        fields = ['id', 'log_timepoints'] + cls._log_fields
        df = pd.DataFrame(events.values(*fields))

        event_logs = []
        df.apply(lambda x: event_logs.append(expand_row(x)), axis=1)

        return pd.concat(event_logs)

    @classmethod
    def events_to_readable_log_df(cls, events):
        df = cls.events_to_log_df(events)
        df.rename(columns={'id': "Event ID", 'log_timepoints': readable_field_name(cls, 'log_timepoints')}, inplace=True)
        for field in cls._log_fields:
            df.rename(columns={field: readable_field_name(cls, field)}, inplace=True)

        return df

    @classmethod
    def get_fail_states(cls):
        values = set(cls.objects.values_list('fail_state', flat=True))
        return zip(values, values)

    @classmethod
    def generate_start_view(cls):
        """
        Return a view that instantiates an Event with information on when and how it occurred.
        """
        class Create(CreateAPIView):
            queryset = cls.objects.all()
            serializer_class = cls.generate_serializer_class(
                fields=["pk", "item", "machine", "operator", "work_order"]
            )

            def perform_create(self, serializer):
                machine = self.request.data.get('machine', None)
                operator_id = self.request.data.get('operator', None)
                operator = Operator.objects.filter(code=operator_id).first()

                # track machine usage
                last_login = MachineUsage.objects.filter(machine=machine).first()
                if last_login is None:
                    MachineUsage.log_in(machine, operator)
                else:
                    last_login.ping(operator)
                return super().perform_create(serializer)

        return Create

    @classmethod
    def generate_finish_view(cls):
        """
        Return a view that allows an Event to be filled in with completion data.
        """
        class Update(UpdateAPIView):
            lookup_url_kwarg = "pk"
            queryset = cls.objects.all()
            serializer_class = cls.generate_serializer_class(
                exclude=["item", "machine", "operator", "work_order"]
            )

        return Update

    @classmethod
    def generate_retrieve_view(cls):
        """
        Return a view that contains the details of an Event
        """
        class Retrieve(RetrieveAPIView):
            lookup_url_kwarg = "pk"
            queryset = cls.objects.all()
            serializer_class = cls.generate_serializer_class()

        return Retrieve

    @classmethod
    def generate_search_form(cls):
        """
        Return a form to be used by cls.generate_search_view().

        Separated out for easy overriding, particularly to add result fields, which are supported
        in the base EventSearchView.
        """
        from base_models.views.event_search_view import EventSearchForm

        class Form(EventSearchForm):
            fail_state = forms.MultipleChoiceField(required=False, choices=cls.get_fail_states)

        return Form

    @classmethod
    def generate_search_view(cls, _project_name):
        """Return a view that searches Events based on the fields in a query parameter."""
        from base_models.views.event_search_view import EventSearchView

        class Search(EventSearchView):
            queryset = cls.objects.all()
            form_class = cls.generate_search_form()
            project_name = _project_name

        return Search

    @classmethod
    def generate_log_lookup_view(cls):
        class Logs(RetrieveAPIView):
            authentication_classes = [SessionAuthentication]
            lookup_field = "pk"
            lookup_url_kwarg = "pk"
            queryset = cls.objects.all()

            def retrieve(self, request, *args, **kwargs):
                instance = self.get_object()
                return RestFrameworkResponse(instance.get_log_results())

        return Logs

    @classmethod
    def generate_single_event_log_csv_view(cls):
        """Return an AJAX view that provides a CSV of the log fields on a given Event."""
        from base_models.views.event_csv_views import SingleEventLogCsvView

        class Csv(SingleEventLogCsvView):
            queryset = cls.objects.all()
            event_class = cls

        return Csv

    @classmethod
    def generate_multi_event_log_csv_view(cls, _project_name):
        """Return an AJAX view that provides a CSV of the log fields on a given Event."""
        from base_models.views.event_csv_views import MultiEventLogCsvView

        class Csv(MultiEventLogCsvView):
            queryset = cls.objects.all()
            event_class = cls
            project_name = _project_name

        return Csv

    @classmethod
    def generate_multi_event_details_csv_view(cls, _project_name):
        """Return an AJAX view that provides a CSV of the log fields on a given Event."""
        from base_models.views.event_csv_views import MultiEventDetailsCsvView

        class Csv(MultiEventDetailsCsvView):
            queryset = cls.objects.all()
            event_class = cls
            project_name = _project_name

        return Csv
