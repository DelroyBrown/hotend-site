# Generated by Django 3.1.1 on 2021-05-04 10:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('v7_post_curing_qc', '0002_update_current_circuit_thresholds'),
    ]

    operations = [
        migrations.AlterField(
            model_name='v7curingqcconfig',
            name='disconnect_tolerance',
            field=models.FloatField(default=8.0),
        ),
    ]