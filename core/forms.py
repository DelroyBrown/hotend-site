from enum import unique
from django import forms

from base_models.base_view_classes.base_form_search_view import DATE_INPUT_FORMATS
from core.models import Machine, Operator, Sku
from core.production_steps import PRODUCTION_STEPS


class SkuCreateForm(forms.ModelForm):
    class Meta:
        model = Sku
        fields = "__all__"


class SkuUpdateForm(SkuCreateForm):
    code = forms.CharField(disabled=True)


class OperatorCreateForm(forms.ModelForm):
    class Meta:
        model = Operator
        fields = "__all__"


class OperatorUpdateForm(OperatorCreateForm):
    code = forms.CharField(disabled=True)


class MachineCreateForm(forms.ModelForm):
    class Meta:
        model = Machine
        fields = "__all__"


class MachineUpdateForm(MachineCreateForm):
    hostname = forms.CharField(disabled=True)


class ZeroingLogSearchForm(forms.Form):
    machine = forms.ModelChoiceField(queryset=Machine.objects.all(), required=False, empty_label="")
    production_step = forms.ChoiceField(
        choices=[(None, ""), *PRODUCTION_STEPS.choices],
        initial=None,
        required=False,
    )

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


class MachineUsageForm(forms.Form):
    machine = forms.ModelMultipleChoiceField(queryset=Machine.objects.all(), required=False)
    operator = forms.ModelMultipleChoiceField(queryset=Operator.objects.all(), required=False)

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

    logged_in = forms.BooleanField(
        required=False,
        label="Currently logged in"
    )
