import django
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "orpheus.settings")
django.setup()

from policies import models

source1 = models.Source.objects.get(pk=1)
node9997 = models.Node.objects.get(pk=9997)
goldpolicy = models.GoldPolicy(node=node9997, source=source1)
goldpolicy.save()
