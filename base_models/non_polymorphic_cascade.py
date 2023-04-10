from django.db import models


def NON_POLYMORPHIC_CASCADE(collector, field, sub_objs, using):
    """
    Work around a bug or weird interaction in django-polymorphic and model deletion:
    https://github.com/django-polymorphic/django-polymorphic/issues/229
    This particular fix is suggested in this comment:
    https://github.com/django-polymorphic/django-polymorphic/issues/229#issuecomment-398434412
    """
    return models.CASCADE(collector, field, sub_objs.non_polymorphic(), using)
