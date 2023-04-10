from django.db import models


class SearchResults(models.Model):
    uid = models.CharField(max_length=255)
    sku = models.CharField(max_length=255)
    date_created = models.DateTimeField()
    completed = models.BooleanField()
    tested_leakage = models.BooleanField()
    tested_circuit = models.BooleanField()
    tested_thermal_cycling = models.BooleanField()
    successful_thermal_cycles = models.BooleanField()
