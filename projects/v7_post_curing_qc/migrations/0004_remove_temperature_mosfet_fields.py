# Generated by Django 3.1.1 on 2021-06-15 14:34

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('v7_post_curing_qc', '0003_set_disconnect_tolerance_default'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='v7curingqcconfig',
            name='mosfet_check_min_temp_drop',
        ),
        migrations.RemoveField(
            model_name='v7curingqcconfig',
            name='mosfet_check_time',
        ),
    ]
