# Generated by Django 3.1.1 on 2021-08-23 15:48

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        # ('prusa_nube_press', '0002_auto_20210823_1548'),
        # ('v6_hot_tightening', '0003_auto_20210823_1548'),
        ('v7_post_curing_qc', '0006_auto_20210823_1548'),
        ('base_models', '0005_event_log_timepoints'),
    ]

    operations = [
        migrations.DeleteModel(
            name='LogEntry',
        ),
    ]
