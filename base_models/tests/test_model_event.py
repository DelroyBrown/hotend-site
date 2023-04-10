from core.models import Machine, Operator, Sku, UniqueID, WorkOrder
from core.tests.api_test_case import APITestCase
from core.utils import reverse
from .. import models


class TestEvent(APITestCase):
    def setUp(self):
        self.machine = Machine.objects.create(hostname="123", name="machine")
        self.operator = Operator.objects.create(code="123", name="operator")
        self.work_order = WorkOrder.objects.create(code="E3D-WO-123")
        self.item = models.SingleItem.objects.create(
            sku=Sku.objects.create(code="123"),
            uid=UniqueID.objects.create(code="123456789"),
        )


    def test_start(self):
        url = reverse("test:basic_single_start")
        self.assertEqual(models.Event.objects.count(), 0)

        data = {
            "machine": self.machine.hostname,
            "operator": self.operator.code,
            "work_order": self.work_order.code,
            "item": self.item.pk,
        }
        response_data = self.postData(url, data, status_code_check=201)

        self.assertEqual(models.Event.objects.count(), 1)
        event = models.Event.objects.first()

        self.assertEqual(response_data["pk"], event.pk)
        self.assertEqual(event.machine, self.machine)
        self.assertEqual(event.operator, self.operator)
        self.assertEqual(event.work_order, self.work_order)
        self.assertEqual(event.item, self.item)


    def test_start_required_fields(self):
        url = reverse("test:basic_single_start")
        response = self.postData(url, {}, status_code_check=400)
        self.assertErrorResponseContains(response, "is required", expected_count=4)


    def test_finish(self):
        event = models.Event.objects.create(
            machine=self.machine,
            operator=self.operator,
            work_order=self.work_order,
            item=self.item,
        )
        url = reverse("test:basic_single_finish", pk=event.pk)

        data = {
            "failed": True,
            "completed": True,
            "log_timepoints": [0, 1, 2.5]
        }
        response_data = self.putData(url, data, status_code_check=200)
        self.assertEqual(models.Event.objects.count(), 1)

        event.refresh_from_db()
        self.assertEqual(response_data["id"], event.pk)
        self.assertTrue(event.failed)
        self.assertTrue(event.completed)
        self.assertGreater(event.date_updated, event.date_created)
        self.assertEqual(len(event.log_timepoints), 3)


    def test_finish_invalid_pk(self):
        url = reverse("test:basic_single_finish", pk=0)
        self.putData(url, {}, status_code_check=404)


    def test_to_dict(self):
        event = models.Event.objects.create(
            machine=self.machine,
            operator=self.operator,
            work_order=self.work_order,
            item=self.item,
        )

        data = event.to_dict()

        # Check that the converted time fields are included.
        self.assertIn("date_and_time", data)
        self.assertIn("duration", data)

        # Check that the data of the ForeignKey models is nested (aside from WorkOrder).
        self.assertEqual(data["item"]["sku"], self.item.sku.code)
        self.assertEqual(data["machine"]["hostname"], self.machine.hostname)
        self.assertEqual(data["operator"]["code"], self.operator.code)


    def test_to_readable_dict(self):
        event = models.Event.objects.create(
            machine=self.machine,
            operator=self.operator,
            work_order=self.work_order,
            item=self.item,
        )

        data = event.to_readable_dict()

        # Check that the converted time fields are included.
        self.assertIn("Started at", data)
        self.assertIn("Duration", data)

        # The ForeignKey models are no longer nested, and Item is split into two fields.
        self.assertEqual(data["Item SKU"], self.item.sku.code)
        self.assertEqual(data["Item UID"], self.item.uid.code)
        self.assertEqual(data["Machine"], self.machine.name)
        self.assertEqual(data["Operator"], self.operator.name)

        # The id field has a nice name.
        self.assertNotIn("id", data)
        self.assertEqual(data["Database primary key"], event.pk)
