from base_models.models import Configuration, Event
from core.production_steps import PRODUCTION_STEPS


class HemeraGreaseConfig(Configuration):
    _production_step = PRODUCTION_STEPS.GREASING

    def __str__(self):
        return F"Hemera grease dispensing config for SKU {self.sku}"


class HemeraGreaseEvent(Event):
    def __str__(self):
        return F"Hemera grease event from {self.date_created}"
