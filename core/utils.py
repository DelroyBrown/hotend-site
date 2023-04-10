import contextlib
import re
from datetime import datetime

from django.core.exceptions import FieldDoesNotExist
from django.urls import reverse as base_reverse


def get_past_date():
    return datetime(1970, 1, 1)


def reverse(url, **kwargs):
    """Convenience method wrapping reverse(), to make passing kwargs a bit simpler."""
    return base_reverse(url, kwargs=kwargs)


def readable_field_name(obj, field_name):
    """Return a cleaned, human-readable name for a model field."""
    try:
        readable_name = obj._meta.get_field(field_name).verbose_name
    except (FieldDoesNotExist, AttributeError):
        readable_name = field_name.replace("_", " ")

    unit = re.search(r' \(.*\)$', readable_name)
    readable_name = re.sub(r' \(.*\)$', '', readable_name)
    readable_name = readable_name.capitalize()

    if unit is not None:
        readable_name += unit[0]

    return readable_name


@contextlib.contextmanager
def suppress_autotime(model, fields):
    _original_values = {}
    # model._meta.get_fields()
    for field in model._meta.fields:
        if field.name in fields:
            _original_values[field.name] = {
                'auto_now': field.auto_now,
                'auto_now_add': field.auto_now_add,
            }
            field.auto_now = False
            field.auto_now_add = False
    try:
        yield
    finally:
        for field in model._meta.fields:
            if field.name in fields:
                field.auto_now = _original_values[field.name]['auto_now']
                field.auto_now_add = _original_values[field.name]['auto_now_add']
