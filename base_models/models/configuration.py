from django import forms
from django.db import models
from django.db.models import Q
from django.http import Http404
from django.urls import reverse
from polymorphic.models import PolymorphicModel
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.generics import RetrieveAPIView, get_object_or_404
from rest_framework.response import Response

from base_models.base_view_classes.ajax import AjaxCreateFormView, AjaxUpdateFormView
from base_models.non_polymorphic_cascade import NON_POLYMORPHIC_CASCADE
from base_models.generate_serializer_mixin import GenerateSerializerMixin
from base_models.unique_together_mixin import UniqueTogetherMixin
from core.models import Sku
from core.production_steps import PRODUCTION_STEPS
from core.views.api import SearchSku


class Configuration(UniqueTogetherMixin, GenerateSerializerMixin, PolymorphicModel):
    """
    An abstract base class for settings applied to any production operation.

    Each SKU can be configured individually for a given machine. Subclasses of Configuration can implement specific
    data fields required by any given kind of item. The configuration settings might include initial conditions,
    guidance on running the operation, pass/fail thresholds, or anything else that's useful.

    This base class can't be instantiated by itself, because it doesn't have an associated production step.
    Each non-abstract Configuration subclass must set the cls._production_step member variable. This is stored in the
    database as well, for lookups and uniqueness validation, under production_step_field.

    Provides the following fields:
      * production_step_field - The operation these settings apply to. This is an uneditable field, set to mirror
        cls._production_step during __init__().
      * sku - The SKU these settings apply to.
    """
    _production_step = None  # Override this in subclasses

    production_step_field = models.CharField(max_length=255, choices=PRODUCTION_STEPS.choices, editable=False)
    sku = models.ForeignKey(Sku, related_name="configurations", on_delete=NON_POLYMORPHIC_CASCADE)

    _unique_together = (
        ("production_step_field", "sku"),
    )

    class Meta:
        ordering = ["sku"]

    def __str__(self):
        return F"Configuration for {self.sku} on {self._production_step} rigs"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not self.pk:
            assert self._production_step is not None, (
                F"Configuration class {self.__class__.__name__} does not have a production step!"
            )
            assert self._production_step in PRODUCTION_STEPS, (
                F"Configuration class {self.__class__.__name__} has an invalid production step of {self._production_step}!"
            )
            self.production_step_field = self._production_step


    @classmethod
    def generate_lookup_view(cls):
        class Get(RetrieveAPIView):
            # This endpoint is used by both the label generator and the production API.
            authentication_classes = [SessionAuthentication, TokenAuthentication]

            queryset = cls.objects.all()
            serializer_class = cls.generate_serializer_class()

            def get_object(self):
                queryset = self.filter_queryset(self.get_queryset())

                filter_kwargs = {
                    "sku": self.kwargs["sku"],
                    "production_step_field": cls._production_step,
                }

                obj = get_object_or_404(queryset, **filter_kwargs)
                return obj

        return Get


    @classmethod
    def generate_sku_search_view(cls):
        """
        Return a SKU search endpoint that includes information on whether each found SKU has a Configuration
        of this class.
        """
        class Search(SearchSku):
            authentication_classes = [SessionAuthentication]

            def list(self, request, *args, **kwargs):
                # Return only SKUs that either a) already have a configuration for this class, or b)
                # don't already have a configuration for this *production step*. You can't have multiple
                # configurations for the same combination of SKU and production step, so don't offer that
                # option to the user.
                production_step_configurations = Configuration.objects.filter(
                    production_step_field=cls._production_step
                )
                no_configuration_skus = self.get_queryset().exclude(
                    configurations__in=production_step_configurations
                ).values_list("code", flat=True)

                skus_with_configuration = set(cls.objects.values_list("sku__code", flat=True))

                all_available_skus = self.get_queryset().filter(
                    Q(code__in=no_configuration_skus) | Q(code__in=skus_with_configuration)
                )
                skus = self.filter_queryset(all_available_skus)

                data = []
                for sku in skus:
                    data.append({
                        "code": sku.code,
                        "has_configuration": (sku.code in skus_with_configuration),
                    })

                return Response(data)

        return Search


    @classmethod
    def generate_create_form_view(cls, project_name):
        """
        Set up a Create view for a configuration for the given SKU, retrieved from a kwarg.
        """
        class Form(forms.ModelForm):
            sku = forms.ModelChoiceField(queryset=Sku.objects.all(), widget=forms.HiddenInput())
            production_step_field = forms.CharField(widget=forms.HiddenInput())

            class Meta:
                model = cls
                fields = "__all__"

        class Create(AjaxCreateFormView):
            form_class = Form
            queryset = cls.objects.all()
            id_field = "sku"

            def extra_initial_data(self):
                return {"production_step_field": cls._production_step}

            def get_action_url(self):
                return reverse(F"ajax:{project_name}_config_create", kwargs={"sku": self.get_object_id()})

        return Create


    @classmethod
    def generate_update_form_view(cls, project_name):
        """
        Return an AJAX-only UpdateView that creates the object first if it doesn't exist.

        Looks for a `sku` entry in self.kwargs. This must match a preexisting Sku object.
        """
        class Form(forms.ModelForm):
            class Meta:
                model = cls
                exclude = ["sku"]

        class Update(AjaxUpdateFormView):
            form_class = Form
            queryset = cls.objects.all()
            id_field = "sku"

            def get_object_lookup_parameters(self, id_value):
                return {
                    **super().get_object_lookup_parameters(id_value),
                    "production_step_field": cls._production_step,
                }

            def get_action_url(self):
                return reverse(F"ajax:{project_name}_config_update", kwargs={"sku": self.get_object_id()})

        return Update
