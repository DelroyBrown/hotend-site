from django.contrib.auth.mixins import LoginRequiredMixin
from django.forms import model_to_dict
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import CreateView, UpdateView, DetailView, FormView


class AjaxMixin():
    """A mixin for Django views that rejects non-AJAX requests."""
    def dispatch(self, request, *args, **kwargs):
        if not request.is_ajax():
            raise Http404("Attempted to send a non-AJAX request to an AJAX view!")
        return super().dispatch(request, *args, **kwargs)


class AjaxFormMixin(AjaxMixin):
    """
    A mixin for Django form views. Provides shared code for AjaxCreateFormView and AjaxUpdateFormView.

    Adds the following members:
      * id_field - a unique (in context) field on the model that provides some way to identify the object
        we're creating or updating.
      * id_url_kwarg - a URL kwarg that contains this identifying value. Defaults to id_field if not set.
      * action_url - the URL to POST form changes to. May require reverse_lazy if you're setting it
        as a class member. You can opt to override get_action_url() instead of setting this member.
    """
    template_name = "web_interface/ajax/create_or_update_form.html"
    id_field = None
    id_url_kwarg = None
    action_url = None

    def get_object_id(self):
        if self.id_url_kwarg is None:
            self.id_url_kwarg = self.id_field

        if self.id_url_kwarg is None:
            raise ValueError("Either id_field or id_url_kwarg must be set on AjaxFormMixin.")

        return self.kwargs.get(self.id_url_kwarg, None)

    def get_action_url(self):
        if self.action_url is None:
            raise ValueError("No action URL was available. Either set self.action_url or override get_action_url().")

        return self.action_url

    def get_success_url(self):
        return reverse("success_notification")

    def get_context_data(self, **kwargs):
        id_value = self.get_object_id()
        context = super().get_context_data(**kwargs)

        context["action_url"] = self.get_action_url()
        context["id_field"] = id_value
        context["has_errors"] = bool(context["form"].errors)

        return context


class AjaxCreateFormView(AjaxFormMixin, LoginRequiredMixin, CreateView):
    """
    A form view designed to be interacted with through AJAX requests, with the form contents embedded into a page.
    Creates a new object, with the new instance identified through an ID field given (by default)
    in a URL argument.

    Requires the following members on any subclass to function:
      * form_class - a Django form class.
      * queryset - a queryset of models to look up.
      * id_field - a unique (in context) field on the model that provides some way to identify the object
        we're creating or updating.
      * id_url_kwarg - a URL kwarg that contains this identifying value. Defaults to id_field if not set.
      * action_url - the URL to POST form changes to. May require reverse_lazy if you're setting it
        as a class member. You can opt to override get_action_url() instead of setting this member.
    """
    def extra_initial_data(self):
        """Custom data added to the form's defaults, if needed."""
        return {}

    def get_initial(self):
        initial_data = super().get_initial()
        initial_data[self.id_field] = self.get_object_id()
        initial_data.update(self.extra_initial_data())
        return initial_data

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["operation_label"] = "Create"
        return context


class AjaxUpdateFormView(AjaxFormMixin, LoginRequiredMixin, UpdateView):
    """
    A form view designed to be interacted with through AJAX requests, with the form contents embedded into a page.
    Updates an existing object, retrieved through an ID field given (by default) in a URL argument as per
    the normal Django UpdateView behaviour.

    Requires the following members on any subclass to function:
      * form_class - a Django form class.
      * queryset - a queryset of models to look up.
      * id_field - a unique (in context) field on the model that provides some way to identify the object
        we're creating or updating.
      * id_url_kwarg - a URL kwarg that contains this identifying value. Defaults to id_field if not set.
      * action_url - the URL to POST form changes to. May require reverse_lazy if you're setting it
        as a class member. You can opt to override get_action_url() instead of setting this member.
    """
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["operation_label"] = "Edit"
        return context

    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.get_queryset()

        id_value = self.get_object_id()
        if id_value is None:
            raise Http404(f"Missing required URL argument: `{self.id_url_kwarg}`")

        self.object = get_object_or_404(queryset, **self.get_object_lookup_parameters(id_value))
        return self.object

    def get_object_lookup_parameters(self, id_value):
        return {self.id_field: id_value}


class AjaxDetailView(AjaxMixin, LoginRequiredMixin, DetailView):
    def format_data(self, obj_as_dict):
        return obj_as_dict

    def get(self, request, *args, **kwargs):
        data = model_to_dict(self.get_object())
        data = self.format_data(data)
        return JsonResponse(data)


class AjaxFormView(AjaxMixin, LoginRequiredMixin, FormView):
    """
    Returns a HTTP response with rendered data if the request contained valid form data,
    and a JSON dictionary of errors if it didn't.
    """
    def form_invalid(self, form):
        return JsonResponse(form.errors, status=400)
