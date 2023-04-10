from django import forms
from django.contrib.postgres.fields import ArrayField
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

from base_models.models import Configuration, Event
from core.production_steps import PRODUCTION_STEPS
from core.thermistor_types import ThermistorType


class V7CuringQCConfig(Configuration):
    _production_step = PRODUCTION_STEPS.ASSEMBLY_QC

    voltage = models.SmallIntegerField(choices=((12, "12V"), (24, "24V")))
    thermistor_type = models.CharField(
        max_length=255,
        choices=ThermistorType.choices,
    )
    wattage = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(99)], default=40)

    # Pre-thermal-cycling test thresholds
    temperature_open_circuit_threshold = models.FloatField(validators=[MinValueValidator(0)], default=10.0)
    temperature_short_circuit_threshold = models.FloatField(validators=[MinValueValidator(0)], default=350.0)
    current_test_pwm = models.FloatField(validators=[MinValueValidator(0)], default=0.1)
    heater_open_circuit_threshold = models.FloatField(validators=[MinValueValidator(0)], default=0.015)
    heater_short_circuit_threshold = models.FloatField(validators=[MinValueValidator(0)], default=0.225)

    # Thermal cycling settings
    thermal_target_temp = models.FloatField(validators=[MinValueValidator(0)], default=250.0)
    thermal_min_hot_temp = models.FloatField(validators=[MinValueValidator(0)], default=220.0)
    thermal_max_hot_temp = models.FloatField(validators=[MinValueValidator(0)], default=270.0)
    current_min = models.FloatField(validators=[MinValueValidator(0)], default=0.001)
    current_max = models.FloatField(validators=[MinValueValidator(0)], default=4.7)
    heat_rate_min_offset = models.FloatField(default=0.0)
    heat_rate_min_gradient = models.FloatField(default=0.0)
    heat_rate_max_offset = models.FloatField(default=1000.0)
    heat_rate_max_gradient = models.FloatField(default=0.0)

    # Safety check settings
    overheat_temp = models.FloatField(validators=[MinValueValidator(0)], default=300.0)
    heatup_timeout = models.FloatField(validators=[MinValueValidator(0)], default=180.0)
    cooling_timeout = models.FloatField(validators=[MinValueValidator(0)], default=180.0)
    mosfet_max_current_after_disable = models.FloatField(validators=[MinValueValidator(0)], default=0.0)
    disconnect_tolerance = models.FloatField(default=8.0)
    safe_handling_temperature = models.FloatField(validators=[MinValueValidator(0)], default=50.0)

    # PID settings
    pid_kp = models.FloatField(default=0.01)
    pid_ki = models.FloatField(default=0.01)
    pid_kd = models.FloatField(default=0.0)

    def __str__(self):
        return F"Post-curing QC config for V7 SKU {self.sku}"


class V7CuringQCEvent(Event):
    # Since the individual components of the test can be skipped, track whether they were run
    # to help catch any accidental skips and better represent early failures.
    tested_leakage = models.BooleanField(default=False)
    tested_circuit = models.BooleanField(default=False)
    tested_thermal_cycling = models.BooleanField(default=False)

    # Track how many successful thermal cycles were run, so we know at which point a failure occurred.
    successful_thermal_cycles = models.PositiveIntegerField(default=0)

    log_temperatures = ArrayField(models.FloatField(), default=list, verbose_name="Temperatures (°C)")

    _log_fields = ["log_temperatures"]

    def __str__(self):
        return F"V7 post-curing QC result from {self.date_created}"
