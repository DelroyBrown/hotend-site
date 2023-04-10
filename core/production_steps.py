from django.db.models import TextChoices


class PRODUCTION_STEPS(TextChoices):
    """
    A list of all the operations that can be performed on a component as part of our production system.

    This is used to distinguish Event and Configuration "types" from one another without necessarily needing
    a legion of subclasses, and validate that a production pipeline has occurred in the correct order.

    Note that the precision and exhaustiveness of these steps isn't complete. Different components can undergo
    the same production step in slightly different ways. The intention is that different rigs on the *same* product
    pipeline have different production steps, but (say) Goods-In QC for heaters and sensors can both be recorded under
    "Goods-In QC".
    """
    ASSEMBLY_QC = "Mid-assembly QC"
    CURING = "Curing"
    CUTTING = "Cutting"
    DRY_ASSEMBLY = "Dry assembly"
    EOL_QC = "End-of-line QC"
    GOODS_IN_QC = "Goods-In QC"
    GREASING = "Greasing"
    HEATER_ASSEMBLY = "Heater assembly"
    HOT_TIGHTENING = "Hot tightening"
    INSPECTION = "Inspection"
    PACKING = "Packing"
    POTTING = "Potting"
    PRESSING = "Pressing"
    UID_SETTING = "Unique ID setting"
