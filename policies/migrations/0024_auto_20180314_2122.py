# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2018-03-14 21:22
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('policies', '0023_auto_20180227_2116'),
    ]

    operations = [
        migrations.CreateModel(
            name='NodeDeal',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('applies_to', models.CharField(blank=True, choices=[('AUTHORS', 'Authors'), ('INSTITUTIONS', 'Institutions')], max_length=20, null=True)),
                ('type', models.CharField(blank=True, choices=[('MEMBER', 'Member'), ('OTHER', 'Other'), ('PREPAYMENT', 'Pre-payment account'), ('SUBSCRIBER', 'Subscriber')], max_length=20, null=True)),
                ('discount_currency', models.CharField(blank=True, choices=[('GBP', 'GBP - British Pound (£)'), ('EUR', 'EUR - Euro (€)'), ('USD', 'USD - United States Dollar ($)'), ('CHF', 'CHF - Swiss Franc (SFr.)')], max_length=10, null=True)),
                ('discount_amount', models.DecimalField(blank=True, decimal_places=2, max_digits=20, null=True)),
                ('discount_percentage', models.DecimalField(blank=True, decimal_places=2, max_digits=20, null=True)),
                ('details', models.TextField(blank=True, null=True)),
                ('start_date', models.DateField(blank=True, null=True)),
                ('vetted', models.BooleanField(default=True)),
                ('vetted_date', models.DateField(blank=True, null=True)),
                ('last_checked', models.DateField(blank=True, null=True)),
                ('superseded', models.BooleanField(default=False)),
                ('superseded_date', models.DateField(blank=True, null=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ('name',),
            },
        ),
        migrations.AddField(
            model_name='goldpolicy',
            name='problematic',
            field=models.BooleanField(default=False, help_text='Use this field to mark ambiguous/unclear policies requiring discussion/revision'),
        ),
        migrations.AddField(
            model_name='greenpolicy',
            name='deposit_allowed',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='greenpolicy',
            name='europe_pmc_deposit',
            field=models.BooleanField(default=False, help_text='Tick this box if journal/publisher automatically deposits articles in Europe PMC after the embargo period specified above'),
        ),
        migrations.AddField(
            model_name='greenpolicy',
            name='problematic',
            field=models.BooleanField(default=False, help_text='Use this field to mark ambiguous/unclear policies requiring discussion/revision'),
        ),
        migrations.AddField(
            model_name='node',
            name='romeo_id',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='nodedeal',
            name='node',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='deals', to='policies.Node'),
        ),
        migrations.AddField(
            model_name='nodedeal',
            name='source',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='policies.Source'),
        ),
    ]
