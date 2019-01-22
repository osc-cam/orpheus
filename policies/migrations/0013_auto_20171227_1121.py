# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2017-12-27 11:21
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('policies', '0012_node_eissn'),
    ]

    operations = [
        migrations.AlterField(
            model_name='node',
            name='type',
            field=models.CharField(choices=[('CONFERENCE', 'Conference'), ('JOURNAL', 'Journal'), ('PUBLISHER', 'Publisher')], max_length=20),
        ),
    ]
