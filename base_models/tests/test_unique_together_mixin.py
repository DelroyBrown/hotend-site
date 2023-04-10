from rest_framework.exceptions import ValidationError

from core.models import Sku, WorkOrder
from core.tests.api_test_case import APITestCase
from ..models import BulkItem


class TestUniqueTogetherMixin(APITestCase):
    def setUp(self):
        self.sku = Sku.objects.create(code="123")
        self.work_order = WorkOrder.objects.create(code="E3D-WO-123")

    def test_create_new(self):
        """An object can be created with no complaints."""
        BulkItem.objects.create(sku=self.sku, work_order=self.work_order)

    def test_create_duplicate(self):
        """The second object with the same fields fails validation."""
        BulkItem.objects.create(sku=self.sku, work_order=self.work_order)

        msg = "Found another model with the same unique fields: ['production_step', 'sku']"
        with self.assertRaises(ValidationError, msg=msg):
            BulkItem.objects.create(sku=self.sku, work_order=self.work_order)
