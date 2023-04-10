from core.models import Sku, UniqueID, WorkOrder
from core.tests.api_test_case import APITestCase
from core.utils import reverse
from .. import models


class TestSingleItem(APITestCase):
    url = reverse("test:basic_single_item")

    def test_create_new(self):
        self.assertEqual(models.SingleItem.objects.count(), 0)
        Sku.objects.create(code="123")
        UniqueID.objects.create(code="123456789")

        data = {
            "uid": "123456789",
            "sku": "123",
        }
        response_data = self.postData(self.url, data, status_code_check=201)

        self.assertEqual(models.SingleItem.objects.count(), 1)
        self.assertEqual(response_data["uid"], "123456789")
        self.assertEqual(response_data["sku"], "123")

    def test_create_new_ignores_contains(self):
        """
        The `contains` field is a ManyToManyField, which can't be set during object creation.
        To avoid any failures, it gets excluded from the input serializers, so even if we supply it as part of the
        data, no errors are thrown.
        """
        sku = Sku.objects.create(code="123")
        UniqueID.objects.create(code="123456789")

        child_item = models.SingleItem.objects.create(
            uid=UniqueID.objects.create(code="456789123"),
            sku=sku,
        )

        data = {
            "uid": "123456789",
            "sku": "123",
            "contains": [child_item.pk],
        }

        response_data = self.postData(self.url, data, status_code_check=201)
        self.assertEqual(response_data["uid"], "123456789")
        self.assertEqual(response_data["contains"], [])


    def test_create_new_missing_dependencies(self):
        data = {
            "uid": "123456789",
            "sku": "123",
        }
        response = self.postData(self.url, data, status_code_check=400)
        self.assertErrorResponseContains(response, "object does not exist", expected_count=2)


    def test_get_existing(self):
        existing_config = models.SingleItem.objects.create(
            uid=UniqueID.objects.create(code="123456789"),
            sku=Sku.objects.create(code="123"),
        )

        data = {
            "uid": "123456789",
            "sku": "123",
        }
        response_data = self.postData(self.url, data, status_code_check=200)

        self.assertEqual(models.SingleItem.objects.count(), 1)
        self.assertEqual(response_data["id"], existing_config.pk)


    def test_update(self):
        sku = Sku.objects.create(code="123")

        parent_item = models.SingleItem.objects.create(
            uid=UniqueID.objects.create(code="123456789"),
            sku=sku,
        )
        child_item = models.SingleItem.objects.create(
            uid=UniqueID.objects.create(code="456789123"),
            sku=sku,
        )
        bulk_item = models.BulkItem.objects.create(
            work_order=WorkOrder.objects.create(code="E3D-WO-123"),
            sku=sku,
        )

        data = {
            "from_bulk": bulk_item.pk,
            "contains": [child_item.pk],
        }

        url = reverse("test:basic_single_item_update", pk=parent_item.pk)
        self.putData(url, data, status_code_check=200)

        parent_item.refresh_from_db()
        self.assertEqual(parent_item.from_bulk, bulk_item)
        self.assertEqual(parent_item.contains.first(), child_item)
