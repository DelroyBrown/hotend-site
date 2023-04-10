from math import ceil

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.views.generic import FormView


DATE_INPUT_FORMATS = ["%d/%m/%Y", "%d-%m-%Y", "%d %m %Y"]


class BaseFormSearchView(LoginRequiredMixin, FormView):
    """
    A search view that uses a form to collect complex search filters.
    Supports pagination, with the `page` set as a URL kwarg.

    Despite being a Django FormView, a successful POST request returns a JSON blob of information.
    This is a little tricky compared to ordinary FormView functionality, but it has a major strength -
    we don't have to manually replicate and maintain the form fields on the frontend. The form
    can be completely defined in Django, and changes made for subclasses, without having to
    perform the corresponding work on the frontend to match a changed API.

    When subclassing, provide a `form_class` and `project_name` as well as implementations
    for the abstract methods. An `ordering` can optionally be supplied to sort the results.
    """
    max_results = 20
    template_name = "web_interface/ajax/search_form.html"
    project_name = None
    ordering = ""

    def build_filter(self, data):
        """Assemble a Django queryset filter from the form data, using Q objects."""
        raise NotImplementedError


    def item_to_dict(self, obj):
        """
        Return a dictionary representation of an object in the list of results. and some of its related models.
        """
        raise NotImplementedError


    def get_action_url(self, page=0):
        """Return the URL pointing to this view, incorporating the pagination `page` if necessary."""
        raise NotImplementedError


    def form_valid(self, form):
        """
        On a successful form submission, return a JSON response instead of a normal form page.

        The JSON includes:
          * Up to `self.max_results` objects that match the criteria the user set via the form
          * The form itself, with the user's data still included, so that any error state can be cleared
          * Pagination information
        """
        form_response = self.render_to_response(self.get_context_data(form=form))

        # Retrieve the desired page from the URL.
        page = self.kwargs.get("page", 0)

        # Use the form data to construct a filter on the queryset.
        data = form.cleaned_data
        queryset_filter = self.build_filter(data)

        # Run the filter to retrieve all relevant objects.
        results = self.queryset.filter(queryset_filter).order_by(self.ordering)
        total_count = results.count()

        # Trim the list of results to the requested page.
        from_index = self.max_results * page
        to_index = self.max_results * (page + 1)
        results = results[from_index:to_index]

        # Build URLs to the next and previous pages, if they exist.
        has_next_page = (to_index < total_count)
        next_page_url = self.get_action_url(page=(page + 1)) if has_next_page else None

        has_prev_page = (page > 0)
        prev_page_url = self.get_action_url(page=(page - 1)) if has_prev_page else None

        # Convert the items to a dictionary of carefully-processed data.
        items = [self.item_to_dict(m) for m in results]

        # Compile all of the data we've generated and return it to the user.
        json_data = {
            "items": items,
            "form": form_response.rendered_content,
            "current_page": page,
            "page_count": ceil(total_count / self.max_results),
            "total_count": total_count,
            "next_page": next_page_url,
            "prev_page": prev_page_url,
        }
        return JsonResponse(json_data, safe=False)


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["action_url"] = self.get_action_url(page=0)
        return context
