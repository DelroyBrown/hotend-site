from django.db.models import Q
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.generics import CreateAPIView, ListAPIView
from rest_framework.response import Response


class GetOrCreateView(CreateAPIView):
    """
    Similar to CreateAPIView, but retrieves an object that matches the identity fields of the input if possible.

    Requires a `model` that inherits from GenerateSerializerMixin, and an `identity_fields` tuple that gives
    the fields used for the lookup. Other fields submitted in the incoming data will be used as `defaults`
    in `get_or_create()`. There's also an `exclude` parameter, which can remove fields from the `default`
    serializer.
    """
    model = None
    identity_fields = []
    exclude = []

    def create(self, request, *args, **kwargs):
        """Implement the get-or-create functionality."""
        serializers = self.model.generate_get_or_create_serializers(*self.identity_fields, exclude=self.exclude)
        context = self.get_serializer_context()

        # Use the `identity` serializer to parse the lookup fields.
        id_serializer = serializers["identity"](data=request.data, context=context)
        id_serializer.is_valid(raise_exception=True)

        # The `defaults` serializer parses the rest - these will be passed to a new object being created.
        data_serializer = serializers["defaults"](data=request.data, context=context)
        data_serializer.is_valid(raise_exception=True)

        # Use the normal Django get_or_create to perform the operation.
        # Any failures are raised as ValidationErrors.
        try:
            obj, created = self.model.objects.get_or_create(
                **id_serializer.validated_data,
                defaults=data_serializer.validated_data
            )
        except Exception as e:
            raise ValidationError(str(e))

        # Use the `result` serializer to return the full data back to the requester.
        response_serializer = serializers["result"](obj, context=context)

        headers = self.get_success_headers(response_serializer.data)
        status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response(response_serializer.data, status_code, headers=headers)

    def get_queryset(self):
        """
        This function contains an assertion for self.queryset, which we don't use.

        We've overridden create(), which is normally where get_queryset() would be called, but the
        Django REST Framework browsable API runs into it as well. For that case, provide a default implementation.
        """
        return self.model.objects.all()

    def get_serializer_class(self):
        """
        This function contains an assertion for self.serializer_class, which we don't use (and doesn't really fit
        a view that uses three serializers).

        We've overridden create(), which is normally where get_serializer_class() would be called, but the
        Django REST Framework browsable API runs into it as well. As such, we need some kind of default.
        Return the model's basic serializer, with all the fields in place.
        """
        return self.model.generate_serializer_class(exclude=self.exclude)


class SearchView(ListAPIView):
    """
    Searches `self.queryset` against a given list of search terms.
    Requires `self.search_fields` to be set to have any effect.

    Expects `search_terms` as a URL kwarg, with individual search terms separated by spaces.

    Returns a list of each item in the queryset where each term in the given search terms is found at least
    once in the search fields on that item.

    All matches are case-insensitive (using Django's __icontains).

    Set self.max_results to limit the number of returned items; the default is 30. When the list of results
    is above this limit, we sneakily return one more - so the actual maximum is 31 by default. This allows
    the caller to detect that there are more than 30 results and prompt the user to narrow their search.

    Optionally, set an `order_results_by` to sort the results. This is a list of arguments passed to
    a Django `.order_by()` queryset method.
    """
    max_results = 30
    search_fields = []
    order_results_by = []

    def get_search_filters(self, search_terms):
        """
        Accumulate a Django queryset filter using Q objects.

        For each search term, we need to construct a lookup for each field in self.search_fields by
        OR'ing together Q objects. The lookups for each search term are then ANDed together.
        """
        full_search_filter = Q()

        for term in search_terms:
            term_filter = Q()

            for field in self.search_fields:
                field_filter = {f"{field}__icontains": term}
                term_filter |= Q(**field_filter)

            full_search_filter &= term_filter

        return full_search_filter


    def run_filter(self, queryset, search_terms):
        search_filter = self.get_search_filters(search_terms)
        return queryset.filter(search_filter).distinct().order_by(*self.order_results_by)


    def filter_queryset(self, queryset):
        # Split the search string on spaces to turn it into a list. Remove any empty items or preceding/trailing
        # whitespace from individual search terms.
        terms = self.kwargs.get("search_terms", "")
        terms = terms.split(" ")
        terms = [t.strip() for t in terms if t.strip()]

        results = self.run_filter(queryset, terms)

        # Trim the list of results down to be no longer than _one more than_ the maximum quantity.
        # The presence of 'an extra one on the end' is a straightforward way to convey to the client
        # that more results exist beyond the limit, so it should ask the user to narrow their search.
        length_cutoff = self.max_results + 1
        results = list(results)[:length_cutoff]

        return results
