# Generated by Django 3.2.12 on 2022-09-09 10:05

import base_models.generate_serializer_mixin
import datetime
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0010_qc_report'),
    ]

    operations = [
        migrations.AddField(
            model_name='machine',
            name='required_ping_interval',
            field=models.PositiveIntegerField(default=600),
        ),
        migrations.CreateModel(
            name='MachineUsage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('logged_in_at', models.DateTimeField(default=datetime.datetime.today)),
                ('logged_out_at', models.DateTimeField(null=True)),
                ('last_ping', models.DateTimeField(auto_now_add=True)),
                ('machine', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.machine')),
                ('operator', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.operator')),
            ],
            bases=(base_models.generate_serializer_mixin.GenerateSerializerMixin, models.Model),
        ),
    ]
