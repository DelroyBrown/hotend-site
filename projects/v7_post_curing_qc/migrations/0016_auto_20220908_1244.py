# Generated by Django 3.2.12 on 2022-09-08 12:44

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('v7_post_curing_qc', '0015_remove_v7curingqcevent_result'),
    ]

    operations = [
        migrations.RenameField(
            model_name='v7curingqcconfig',
            old_name='current_open_circuit_threshold',
            new_name='heater_open_circuit_threshold',
        ),
        migrations.RenameField(
            model_name='v7curingqcconfig',
            old_name='current_short_circuit_threshold',
            new_name='heater_short_circuit_threshold',
        ),
    ]
