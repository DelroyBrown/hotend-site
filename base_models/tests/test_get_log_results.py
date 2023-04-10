from django.db import IntegrityError

from core.models import Machine, Operator, Sku, UniqueID, WorkOrder
from core.tests.api_test_case import APITestCase
from ..models import SingleItem

# We need to use an Event that has more than just the `timepoints` field.
from projects.v7_post_curing_qc.models import V7CuringQCEvent


class TestEvent(APITestCase):
    def setUp(self):
        self.machine = Machine.objects.create(hostname="123")
        self.operator = Operator.objects.create(code="123")
        self.work_order = WorkOrder.objects.create(code="E3D-WO-123")
        self.item = SingleItem.objects.create(
            sku=Sku.objects.create(code="123"),
            uid=UniqueID.objects.create(code="123456789"),
        )

    def test_get_log_results(self):
        event = V7CuringQCEvent.objects.create(
            machine=self.machine,
            operator=self.operator,
            work_order=self.work_order,
            item=self.item,
            log_timepoints=[0, 1, 2],
            log_temperatures=[100, 150, 200]
        )

        expected_data = {
            "timepoints": [0, 1, 2],
            "results": [
                {"name": "Temperatures (°C)", "data": [100, 150, 200]}
            ]
        }

        self.assertDictEqual(event.get_log_results(), expected_data)

    def test_get_log_results_wrong_length(self):
        event = V7CuringQCEvent.objects.create(
            machine=self.machine,
            operator=self.operator,
            work_order=self.work_order,
            item=self.item,
            log_timepoints=[0, 1, 2],
            log_temperatures=[100, 150]
        )

        with self.assertRaises(IntegrityError):
            event.get_log_results()
