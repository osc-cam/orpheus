# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2017-11-07 21:03
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('policies', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='node',
            name='name',
            field=models.CharField(help_text='Please enter the name of the publisher, journal or conference.', max_length=200, unique=True),
        ),
    ]
