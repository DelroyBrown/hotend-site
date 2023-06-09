# Generated by Django 3.1.1 on 2020-11-11 08:38

import base_models.generate_serializer_mixin
import datetime
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ZeroingLog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateTimeField(default=datetime.datetime.now)),
                ('base_value', models.FloatField()),
                ('machine', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.machine')),
                ('operator', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.operator')),
            ],
            bases=(base_models.generate_serializer_mixin.GenerateSerializerMixin, models.Model),
        ),
    ]
