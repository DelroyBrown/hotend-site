from base_models.project import Project
from base_models.models import SingleItem

from . import models


v7_post_curing_qc_project = Project(
    name="v7_post_curing_qc",
    verbose_name="V7 (Revo) QC rig",
    item_class=SingleItem,
    configuration_class=models.V7CuringQCConfig,
    event_class=models.V7CuringQCEvent,
)
