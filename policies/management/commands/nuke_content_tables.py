from django.core.management.base import BaseCommand
from policies.models import Node, GreenPolicy, GoldPolicy, OaStatus

class Command(BaseCommand):
    def handle(self, *args, **options):
        if input('Are you sure you want to delete all Orpheus content tables (Nodes, Open Access stata, Gold policies'
                   'and Green Policies? (y/n)') in ['y', 'Y']:
            GreenPolicy.objects.all().delete()
            GoldPolicy.objects.all().delete()
            OaStatus.objects.all().delete()
            Node.objects.all().filter(synonym_of__isnull=False).delete()
            Node.objects.all().filter(type__exact='JOURNAL').delete()
            Node.objects.all().filter(type__exact='CONFERENCE').delete()
            Node.objects.all().delete()