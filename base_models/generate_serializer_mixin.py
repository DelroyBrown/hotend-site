from copy import copy

from rest_framework import serializers, validators


class GenerateSerializerMixin:
    """
    Provides convenience methods that return DRF serializers for any subclass of this and Django's Model.

    This is designed to work with ApiFactory and other class methods, dramatically reducing the amount of boilerplate
    required to set up basic views for a production operation.
    """
    @classmethod
    def generate_serializer_class(cls, *, fields="__all__", exclude=None):
        """
        Return a standard serializer for this model.
        Optionally, limit the fields used, by passing `fields` or `exclude` as kwargs. The latter takes precedence.
        """
        class BasicSerializer(serializers.ModelSerializer):
            class Meta:
                model = cls

        if exclude:
            BasicSerializer.Meta.exclude = exclude
        else:
            BasicSerializer.Meta.fields = fields

        return BasicSerializer


    @classmethod
    def generate_non_unique_serializer(cls, *fields):
        """
        Return a serializer class with all uniqueness and unique_together validation disabled.

        This is intended for use as part of generate_get_or_create_serializers, but has been separated out
        for easier overriding.
        """
        Base = cls.generate_serializer_class(fields=fields)

        # Remove the UniqueValidators from each field.
        # To do this, we need to use Meta.extra_kwargs to set each field's validators to a list that excludes
        # the UniqueValidator(s) and includes any others.
        meta_kwargs = {}
        for field in cls._meta.fields:
            non_unique_validators = [v for v in field.validators if not isinstance(v, validators.UniqueValidator)]
            meta_kwargs[field.name] = {"validators": non_unique_validators}

        # Construct the adjusted serializer.
        class NonUnique(Base):
            def run_validators(self, value):
                """Override this function to remove all unique_together validation."""
                for validator in copy(self.validators):
                    if isinstance(validator, (validators.UniqueTogetherValidator, validators.BaseUniqueForValidator)):
                        self.validators.remove(validator)
                super().run_validators(value)

            class Meta(Base.Meta):
                extra_kwargs = meta_kwargs

        return NonUnique


    @classmethod
    def generate_get_or_create_serializers(cls, *identity_fields, exclude=[]):
        """
        Return *three* serializer classes suitable for use in a GetOrCreateView.

        They come in a dictionary:
          * identity - parse only the given identity_fields from the data. Skips unique field validation.
          * defaults - parse everything *except* the identity_fields from the data.
          * result - parse all fields. Used for returning the object.
        """
        all_exclusions = [*identity_fields, *exclude]

        return {
            "identity": cls.generate_non_unique_serializer(*identity_fields),
            "defaults": cls.generate_serializer_class(exclude=all_exclusions),
            "result": cls.generate_serializer_class()
        }
