from django.core.management.base import BaseCommand
from policies.models import Node, GreenPolicy, GoldPolicy, OaStatus

class Command(BaseCommand):
    def handle(self, *args, **options):
        if input('Are you sure you want to delete all Orpheus journal nodes? (y/n)') in ['y', 'Y']:
            Node.objects.all().filter(type__exact='JOURNAL').delete()