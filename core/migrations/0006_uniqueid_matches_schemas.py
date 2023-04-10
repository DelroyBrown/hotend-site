# Generated by Django 3.1.1 on 2022-01-17 12:25

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_uniqueid_date_created'),
    ]

    operations = [
        migrations.AddField(
            model_name='uniqueid',
            name='matches_schemas',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(choices=[('V6_BARCODE', 'V6 Barcode'), ('V7_SERIAL', 'V7 Serial Number'), ('HEMERA_QR', 'Hemera QR Code')], max_length=255), default=list, size=None),
        ),
    ]