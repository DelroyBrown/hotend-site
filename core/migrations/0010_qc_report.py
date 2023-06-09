# Generated by Django 3.2.12 on 2022-09-05 10:00

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0009_rename_base_value_zeroinglog_resistance'),
    ]

    operations = [
        migrations.AddField(
            model_name='machine',
            name='idealised_cycle_time',
            field=models.PositiveIntegerField(default=3600),
        ),
        migrations.AddField(
            model_name='machine',
            name='planned_production_time',
            field=models.PositiveIntegerField(default=28800),
        ),
    ]
