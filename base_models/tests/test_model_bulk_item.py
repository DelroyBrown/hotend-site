from core.models import Machine, Operator, Sku, WorkOrder
from core.tests.api_test_case import APITestCase
from core.utils import reverse
from .. import models


class TestBulkItem(APITestCase):
    url = reverse("test:basic_bulk_item")

    def setUp(self):
        self.machine = Machine.objects.create(hostname="123")
        self.operator = Operator.objects.create(code="123")
        self.work_order = WorkOrder.objects.create(code="E3D-WO-123")
        self.sku = Sku.objects.create(code="123")


    def test_create_new(self):
        self.assertEqual(models.BulkItem.objects.count(), 0)

        data = {
            "work_order": "E3D-WO-123",
            "sku": "123",
        }
        response_data = self.postData(self.url, data, status_code_check=201)

        self.assertEqual(models.BulkItem.objects.count(), 1)
        self.assertEqual(response_data["work_order"], "E3D-WO-123")
        self.assertEqual(response_data["sku"], "123")


    def test_create_new_missing_dependencies(self):
        data = {
            "work_order": "E3D-WO-456",
            "sku": "456",
        }
        response = self.postData(self.url, data, status_code_check=400)
        self.assertErrorResponseContains(response, "object does not exist", expected_count=2)


    def test_get_existing(self):
        existing_item = models.BulkItem.objects.create(
            work_order=self.work_order,
            sku=self.sku,
        )

        data = {
            "work_order": "E3D-WO-123",
            "sku": "123",
        }
        response_data = self.postData(self.url, data, status_code_check=200)

        self.assertEqual(models.BulkItem.objects.count(), 1)
        self.assertEqual(response_data["id"], existing_item.pk)
        self.assertEqual(response_data["quantity_succeeded"], 0)


    def test_quantity_succeeded(self):
        existing_item = models.BulkItem.objects.create(
            work_order=self.work_order,
            sku=self.sku,
        )

        models.Event.objects.create(
            machine=self.machine,
            operator=self.operator,
            work_order=self.work_order,
            item=existing_item,
            completed=True,
        )
        models.Event.objects.create(
            machine=self.machine,
            operator=self.operator,
            work_order=self.work_order,
            item=existing_item,
            completed=False,
        )
        models.Event.objects.create(
            machine=self.machine,
            operator=self.operator,
            work_order=self.work_order,
            item=existing_item,
            completed=True,
            failed=True,
        )

        data = {
            "work_order": "E3D-WO-123",
            "sku": "123",
        }
        response_data = self.postData(self.url, data, status_code_check=200)

        self.assertEqual(models.BulkItem.objects.count(), 1)
        self.assertEqual(response_data["quantity_succeeded"], 1)
