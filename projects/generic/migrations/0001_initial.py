# Generated by Django 3.2.12 on 2022-05-27 09:52

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('base_models', '0008_alter_event_log_timepoints'),
    ]

    operations = [
        migrations.CreateModel(
            name='GenericEvent',
            fields=[
                ('event_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='base_models.event')),
                ('fail_state', models.CharField(default='None', max_length=255)),
            ],
            options={
                'abstract': False,
                'base_manager_name': 'objects',
            },
            bases=('base_models.event',),
        ),
    ]