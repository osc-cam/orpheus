# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2018-08-17 09:55
from __future__ import unicode_literals

from django.db import migrations, models
import policies.models


class Migration(migrations.Migration):

    dependencies = [
        ('policies', '0029_auto_20180803_1027'),
    ]

    operations = [
        migrations.AlterField(
            model_name='node',
            name='name',
            field=models.CharField(max_length=200, unique=True, validators=[policies.models.node_name_validator]),
        ),
    ]
