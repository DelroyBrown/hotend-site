from rest_framework.exceptions import ValidationError

from core.models import Sku
from core.tests.api_test_case import APITestCase
from core.utils import reverse
from projects.hemera.models import HemeraGreaseConfig
from .. import models


class TestConfiguration(APITestCase):
    url = reverse("test:basic_single_config", sku="123")

    def setUp(self):
        self.sku = Sku.objects.create(code="123")


    def test_does_not_exist(self):
        self.getData(self.url, status_code_check=404)


    def test_get_existing(self):
        existing_config = HemeraGreaseConfig.objects.create(sku=self.sku)

        response_data = self.getData(self.url, status_code_check=200)
        self.assertEqual(response_data["id"], existing_config.pk)
        self.assertEqual(response_data["production_step_field"], HemeraGreaseConfig._production_step)


    def test_base_class_abstract(self):
        """Check that Configuration itself can't be instantiated."""
        with self.assertRaises(AssertionError):
            models.Configuration.objects.create(sku=self.sku)


    def test_uniqueness(self):
        HemeraGreaseConfig.objects.create(sku=self.sku)

        with self.assertRaises(ValidationError):
            HemeraGreaseConfig.objects.create(sku=self.sku)


    def test_sku_search(self):
        Sku.objects.create(code="123456")
        Sku.objects.create(code="789")

        HemeraGreaseConfig.objects.create(sku=self.sku)

        search_url = reverse("test:basic_single_config_search", search_terms="123")
        response_data = self.getData(search_url, status_code_check=200)

        self.assertCountEqual(response_data, [
            {
                "code": "123",
                "has_configuration": True,
            },
            {
                "code": "123456",
                "has_configuration": False,
            },
        ])
