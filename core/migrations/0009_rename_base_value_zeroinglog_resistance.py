# Generated by Django 3.2.12 on 2022-04-11 12:18

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0008_remove_deathrig'),
    ]

    operations = [
        migrations.RenameField(
            model_name='zeroinglog',
            old_name='base_value',
            new_name='resistance',
        ),
    ]
