from rest_framework.exceptions import ValidationError


class UniqueTogetherMixin:
    """
    A mixin that replaces some slightly broken functionality in Django.

    The problem:
      * Create a ForeignKey on a model to another model with a `primary_key=True` field (e.g. Sku, WorkOrder, etc).
      * Include that ForeignKey in a `UniqueConstraint` (or a `unique_together` declaration).
      * When attempting to run the migration, an error pops up about how `sku_id` (for a Sku FK) isn't a field.
        The `UniqueConstraint` seems to be expecting the primary key to be under `id`, and doesn't check for the
        existence of a `primary_key` field on the target model.

    As far as I can tell, this is not intended behaviour, but nobody else seems to have run into it.

    This mixin overrides a Django model's validate_unique() and save() methods to reimplement the uniqueness check
    manually. To set it up, set the `_unique_together` field on the model class. The field expects
    a tuple of tuples, supporting multiple unique_together constraints:

    class MyModel(UniqueTogetherMixin):
        _unique_together = (
            ("sku", "production_step"),
        )
    """
    _unique_together = ()

    def mixin_validate_unique_constraint(self, unique_together_fields):
        """Check a single set of unique fields."""
        filter_kwargs = {
            f: getattr(self, f)
            for f in unique_together_fields
        }

        equivalents = self.__class__.objects.filter(**filter_kwargs)
        if self.pk:
            equivalents = equivalents.exclude(pk=self.pk)
        if equivalents.exists():
            raise ValidationError(F"Found another model with the same unique fields: {filter_kwargs}")


    def validate_unique(self, exclude=None):
        """Hook into Django's validation by overriding this method."""
        for unique_together_fields in self._unique_together:
            self.mixin_validate_unique_constraint(unique_together_fields)

        super().validate_unique(exclude=exclude)


    def save(self, *args, **kwargs):
        """
        Ensure validate_unique() is called when saving at any time - normally, it's only used for form validation.
        https://docs.djangoproject.com/en/3.1/ref/models/instances/#django.db.models.Model.full_clean
        """
        self.validate_unique()
        super().save(*args, **kwargs)
