# Generated by Django 3.1.1 on 2021-08-20 15:55

import django.contrib.postgres.fields
import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base_models', '0004_related_name_on_event_fks'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='log_timepoints',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.FloatField(validators=[django.core.validators.MinValueValidator(0)]), default=list, size=None),
        ),
    ]