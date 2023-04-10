from django.db.models import TextChoices


class ThermistorType(TextChoices):
    THERMISTOR = ("Thermistor", "Generic Thermistor (deprecated)")
    THERMISTOR_104NT4 = ("104NT-4 Thermistor", "104NT-4 Thermistor")
    PT100 = ("PT100", "PT100")
    PT1000 = ("PT1000", "PT1000")
    BCN_THERMISTOR = ("BCN Thermistor", "100K3950 (BCN) Thermistor")
