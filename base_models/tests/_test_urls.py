from projects.hemera.models import HemeraGreaseConfig
from .. import models
from ..project import Project


basic_single = Project(
    name="basic_single",
    item_class=models.SingleItem,
    configuration_class=HemeraGreaseConfig,
    event_class=models.Event,
)

basic_bulk = Project(
    name="basic_bulk",
    item_class=models.BulkItem,
    configuration_class=HemeraGreaseConfig,
    event_class=models.Event,
)


urlpatterns = [
    basic_single.generate_basic_api(),
    basic_bulk.generate_basic_api(),
]
