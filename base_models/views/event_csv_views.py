import csv
import pandas as pd
from datetime import datetime

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, Http404, HttpResponseBadRequest
from django.views.generic import DetailView

from base_models.views.event_search_view import EventSearchView
from core.utils import readable_field_name


def generate_log_csv_response(event_class, events, filename):
    """
    Return a HttpResponse containing a CSV of all the log data for the given events.

    The Python CSV library writes to file-like objects, and conveniently, Django's HttpResponse
    class is a file-like object. https://docs.djangoproject.com/en/3.2/howto/outputting-csv/
    This means we can construct the response first and write directly to it instead of dumping
    our CSV data to an intermediary string or list.
    """
    # Raise a 404 for Event classes that never have any logs in the first place.
    if len(event_class._log_fields) == 0:
        raise Http404(f"Event class {event_class.__name__} doesn't record any logs")

    response = HttpResponse(
        content_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={filename}.csv"
        },
    )

    df = event_class.events_to_readable_log_df(events)
    df.to_csv(response)

    return response


class SingleEventLogCsvView(LoginRequiredMixin, DetailView):
    """
    An AJAX view that returns a downloadable CSV file of all the logs for a specific Event.
    The Event is retrieved via a `pk` URL argument.

    Requires a `queryset` to function, like other Django DetailViews. Also requires an
    `event_class` in order to correctly generate the CSV.
    """
    lookup_field = "pk"
    lookup_url_kwarg = "pk"
    event_class = None

    def get(self, request, *args, **kwargs):
        """
        Look up the requested object and return its logs in a CSV file.
        Provide informative 404 responses for objects that don't have any logs.
        """
        self.object = self.get_object()

        # Raise a 404 for Event classes that never have any logs in the first place.
        if len(self.event_class._log_fields) == 0:
            raise Http404(f"Event class {self.event_class.__name__} doesn't record any logs")

        # Perform the lookup. If the resulting object doesn't have any logs recorded
        # against it - perhaps due to a bug, or being incomplete - raise a 404.
        if len(self.object.log_timepoints) == 0:
            raise Http404(f"Event object {self.object.pk} doesn't have any logs recorded")

        return generate_log_csv_response(self.event_class, self.event_class.objects.filter(id=self.object.id), f"event_{self.object.pk}")


class BaseMultiEventCsvView(EventSearchView):
    """
    Return a CSV of a given search filter of Events. Override `render_to_csv` to implement the actual
    CSV generation.

    Support filtering using GET query parameters instead of POST. This is because file downloads
    aren't available over Ajax for security reasons - instead, we need to use a simple `<a href>`.
    To get around this limitation, look for form data in request.GET and, if it's present,
    handle this request like a search submission.

    If the filter returns more than settings.MAX_CSV_EVENT_COUNT, return a 400 with an explanatory
    error message.

    On top of EventSearchView's requirements (`project_name` and `queryset` at minimum), supply an
    `event_class` to ensure the CSV output works correctly.
    """
    event_class = None

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()

        if self.request.method == "GET":
            kwargs.update({"data": self.request.GET})

        return kwargs


    def get(self, request, *args, **kwargs):
        # For GET requests without any query parameters, behave normally.
        if not request.GET:
            return super().get(request, *args, **kwargs)

        # When there *are* query parameters, handle this like a form submission.
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            raise Http404("Invalid form data supplied via request.GET parameters")


    def render_to_csv(self, events, filename):
        raise NotImplementedError


    def form_valid(self, form):
        """
        On a successful form submission, return a CSV of logs instead of a normal form page.
        """
        # Use the form data to construct a filter on the queryset.
        data = form.cleaned_data
        queryset_filter = self.build_filter(data)

        # Run the filter to retrieve all relevant objects.
        events = self.queryset.filter(queryset_filter).order_by(self.ordering)

        if events.count() > settings.MAX_CSV_EVENT_COUNT:
            return HttpResponseBadRequest(
                f"Event filters returned more than {settings.MAX_CSV_EVENT_COUNT} results; please refine your search."
            )
        if events.count() == 0:
            return HttpResponseBadRequest("Event filters returned no results.")

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%m-%s")
        return self.render_to_csv(events, timestamp)


class MultiEventLogCsvView(BaseMultiEventCsvView):
    def render_to_csv(self, events, timestamp):
        return generate_log_csv_response(self.event_class, events, f"event_logs_{timestamp}")


class MultiEventDetailsCsvView(BaseMultiEventCsvView):
    def render_to_csv(self, events, timestamp):
        """
        Return a HttpResponse containing a CSV of all the detail data for the given events.
        The data uses the processed values and readable field names from event.to_readable_dict().
        """
        filename = f"event_details_{timestamp}"

        response = HttpResponse(
            content_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={filename}.csv"
            },
        )

        df = self.event_class.events_to_readable_df(events)
        df.to_csv(response)

        return response
