# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2019-03-12 23:15
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('policies', '0039_auto_20190213_1204'),
    ]

    operations = [
        migrations.AlterField(
            model_name='epmc',
            name='deposit_status',
            field=models.CharField(blank=True, choices=[('NO_NEW', 'No new content'), ('PRE', 'Predecessor'), ('NOW_SELECT', 'Now select')], max_length=10, null=True),
        ),
    ]