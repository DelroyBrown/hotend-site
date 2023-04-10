# Generated by Django 3.1.1 on 2022-02-14 09:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('v7_post_curing_qc', '0012_v7curingqcconfig_wattage'),
    ]

    operations = [
        migrations.AlterField(
            model_name='v7curingqcconfig',
            name='thermistor_type',
            field=models.CharField(choices=[('Thermistor', 'Generic Thermistor (deprecated)'), ('104NT-4 Thermistor', '104NT-4 Thermistor'), ('PT100', 'PT100'), ('PT1000', 'PT1000'), ('BCN Thermistor', '100K3950 (BCN) Thermistor')], max_length=255),
        ),
    ]
