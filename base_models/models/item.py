from django.db import models
from polymorphic.models import PolymorphicModel
from rest_framework.fields import SerializerMethodField
from rest_framework.generics import UpdateAPIView

from base_models.non_polymorphic_cascade import NON_POLYMORPHIC_CASCADE
from base_models.base_view_classes.api import GetOrCreateView
from base_models.generate_serializer_mixin import GenerateSerializerMixin
from base_models.unique_together_mixin import UniqueTogetherMixin
from core.models import Sku, UniqueID, WorkOrder


class AnyItem(GenerateSerializerMixin, PolymorphicModel):
    """
    A base class for SingleItem and BulkItem.

    A class inheriting from AnyItem represents one or more "types" of item - for instance, we could have
    a Heater class, a V6HotEnd class, and so on. An instance of the (sub)class then represents one or more of these
    items being processed through the production facility. There's no requirement to make specific item classes
    unless custom functionality is needed.

    Intended for use as a ForeignKey target. It's useful for a BulkItem to not be a SingleItem and vice versa,
    but we still want them to be part of the same class hierarchy so they can be linked from Events and other models.

    When creating new items, inherit from SingleItem or BulkItem rather than this one.

    Provides the following fields:
      * sku - All items must have a SKU, so that we can track their stock as well as production progress.
    """
    sku = models.ForeignKey(Sku, related_name="items", on_delete=NON_POLYMORPHIC_CASCADE)

    def __str__(self):
        return F"Item of SKU {self.sku}"

    def is_bulk(self):
        """Convenience method to distinguish between BulkItem and SingleItem instances."""
        raise NotImplementedError

    @classmethod
    def generate_lookup_view(cls):
        """Return an API view that can look up this item, creating it if it doesn't exist."""
        raise NotImplementedError

    @classmethod
    def generate_update_view(cls):
        """Return an API view that can edit this item."""
        raise NotImplementedError



class BulkItem(UniqueTogetherMixin, AnyItem):
    """
    Represents a group of items that are processed together as part of the same work order. We don't attach
    barcodes to small elements like heaters or sensors; their QC results are only tracked in aggregate.

    Provides the following fields:
      * work_order - All items are processed as part of a work order. In theory, an item can be part of
        multiple work orders - for instance, it might go through assembly again after a product recall or a failed
        QC stage. However, the anonymous items in a BulkItem can't be tracked this way.
    """
    work_order = models.ForeignKey(WorkOrder, related_name="bulk_items", on_delete=NON_POLYMORPHIC_CASCADE)

    _unique_together = (
        ("work_order", "sku"),
    )

    def __str__(self):
        return F"Bulk {self.sku} (work order {self.work_order})"

    def is_bulk(self):
        return True


    @classmethod
    def generate_serializer_class(cls, *, fields="__all__", exclude=None):
        """When looking up BulkItems, include a value counting how many have already been successfully processed."""
        BaseClass = super().generate_serializer_class(fields=fields, exclude=exclude)

        class BasicSerializer(BaseClass):
            quantity_succeeded = SerializerMethodField()

            def get_quantity_succeeded(self, obj):
                return obj.events.filter(failed=False, completed=True).count()

        return BasicSerializer


    @classmethod
    def generate_lookup_view(cls):
        """
        Return a view that accepts a POST request with at least a `sku` and `WorkOrder`, and returns a BulkItem.
        Extra data supplied by the POST request is passed to get_or_create as a set of defaults.
        """
        class GetOrCreate(GetOrCreateView):
            model = cls
            identity_fields = ["work_order", "sku"]

        return GetOrCreate


    @classmethod
    def generate_update_view(cls):
        """Return a basic PUT view that can be used to update an item."""
        class Update(UpdateAPIView):
            lookup_url_kwarg = "pk"
            queryset = cls.objects.all()
            serializer_class = cls.generate_serializer_class(exclude=["work_order", "sku"])

        return Update


class SingleItem(AnyItem):
    """
    Represents one individual, identifiable part, such as a hotend with a barcode.

    Larger items like hotends are given some kind of identifier - this might be an engraved serial number,
    a barcode, a QR code, or some other new addition to the system. Tracking these unique IDs allows us to
    trace the progress of individual items through the production system.

    Provides the following fields:
      * uid - This item's unique ID code. It can be represented on the object itself in a variety of ways,
        but they all boil down to a basic ID code. The UID is a OneToOneField because IDs have their own table -
        we need to generate them and ensure they're unique before they're applied to an item.
      * from_bulk - When an item undergoes production stages anonymously, it's recorded as part of a BulkItem.
        If it then gains a UID and becomes a SingleItem, from_bulk can link it back to the original BulkItem.
      * contains - Items can be made up of other items. Heaters and sensors are added to nozzles; nubes
        become part of HeaterCore or V7 hotends. Note that `contains` is a ManyToMany rather than a `parent` FK
        because BulkItems can become part of a large number of SingleItems.
    """
    uid = models.OneToOneField(UniqueID, related_name="item", on_delete=NON_POLYMORPHIC_CASCADE)
    from_bulk = models.ForeignKey(
        BulkItem,
        related_name="singles_produced",
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )
    contains = models.ManyToManyField(AnyItem, related_name="part_of", blank=True)

    def __str__(self):
        return F"Single {self.sku} (UID {self.uid})"

    def is_bulk(self):
        return False


    @classmethod
    def generate_lookup_view(cls):
        """
        Return a view that accepts a POST request with at least a `uid`, and returns a SingleItem.
        Extra data supplied by the POST request is passed to get_or_create as a set of defaults.
        """
        class GetOrCreate(GetOrCreateView):
            model = cls
            identity_fields = ["uid", "sku"]
            exclude = ["contains"]

        return GetOrCreate


    @classmethod
    def generate_update_view(cls):
        """
        Return a basic PUT view that can be used to update an item's from_bulk or contains.
        This is because `contains`, as a ManyToManyField, can't be set before an item has been saved to the database,
        making it unsuitable for a GetOrCreate operation. We also expect items to mostly be created and then assembled
        together later.
        """
        class Update(UpdateAPIView):
            lookup_url_kwarg = "pk"
            queryset = cls.objects.all()
            serializer_class = cls.generate_serializer_class(exclude=["uid", "sku"])

        return Update
