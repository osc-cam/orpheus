# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

null = None

licence_fixture = [{"model": "policies.licence", "pk": 1, "fields": {"short_name": "CC BY", "long_name": "Creative Commons Attribution", "url": "https://creativecommons.org/licenses/by/4.0/"}}, {"model": "policies.licence", "pk": 2, "fields": {"short_name": "CC BY-NC", "long_name": "Creative Commons Attribution-NonCommercial", "url": "https://creativecommons.org/licenses/by-nc/4.0/"}}, {"model": "policies.licence", "pk": 3, "fields": {"short_name": "CC BY-NC-ND", "long_name": "Creative Commons Attribution-NonCommercial-NoDerivatives", "url": "https://creativecommons.org/licenses/by-nc-nd/4.0/"}}, {"model": "policies.licence", "pk": 4, "fields": {"short_name": "Custom", "long_name": "Publisher's own licence", "url": null}}, {"model": "policies.licence", "pk": 5, "fields": {"short_name": "Unclear", "long_name": null, "url": null}}, {"model": "policies.licence", "pk": 6, "fields": {"short_name": "CC BY-SA", "long_name": "Creative Commons Attribution-ShareAlike", "url": "https://creativecommons.org/licenses/by-sa/4.0/"}}, {"model": "policies.licence", "pk": 7, "fields": {"short_name": "CC BY-NC-SA", "long_name": "Creative Commons Attribution-NonCommercial-ShareAlike", "url": "https://creativecommons.org/licenses/by-nc-sa/4.0/"}}]
outlet_fixture = [{"model": "policies.outlet", "pk": 1, "fields": {"name": "PubMed Central", "url": "https://www.ncbi.nlm.nih.gov/pmc/"}}, {"model": "policies.outlet", "pk": 2, "fields": {"name": "Non-commercial institutional repository", "url": null}}, {"model": "policies.outlet", "pk": 3, "fields": {"name": "Personal website", "url": null}}, {"model": "policies.outlet", "pk": 4, "fields": {"name": "Commercial repository", "url": null}}, {"model": "policies.outlet", "pk": 5, "fields": {"name": "Social platforms (Research Gate, etc)", "url": null}}, {"model": "policies.outlet", "pk": 6, "fields": {"name": "Non-commercial subject repository", "url": null}}]
version_fixture = [{"model": "policies.version", "pk": 1, "fields": {"short_name": "AAM", "long_name": "Author's accepted manuscript"}}, {"model": "policies.version", "pk": 2, "fields": {"short_name": "VoR", "long_name": "Version of Record"}}, {"model": "policies.version", "pk": 3, "fields": {"short_name": "Preprint", "long_name": "Submitted version"}}, {"model": "policies.version", "pk": 4, "fields": {"short_name": "Publisher-supplied pdf", "long_name": null}}]

def initialize_data(apps, schema_editor):
    data = licence_fixture + outlet_fixture + version_fixture

    for record in data:
        app_name, model_name = record['model'].split('.')
        ModelClass = apps.get_model(app_name, model_name)
        obj = ModelClass(**record['fields'])
        # line below is required only if you have other models
        # with foreign keys referring to this object
        obj.pk = record['pk']
        obj.save()

class Migration(migrations.Migration):

    dependencies = [
        ('policies', '0021_auto_20180213_2126'),
    ]

    operations = [
        migrations.RunPython(initialize_data),
    ]
