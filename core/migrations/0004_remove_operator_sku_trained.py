# Generated by Django 3.1.1 on 2020-12-02 10:17

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_add_grease_op'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='operator',
            name='sku_trained',
        ),
    ]
