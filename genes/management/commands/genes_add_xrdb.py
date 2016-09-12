import logging
logger = logging.getLogger(__name__)
from django.core.management.base import BaseCommand
from optparse import make_option
from genes.models import CrossRefDB

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--name', action = 'store', dest = 'name'),
        make_option('--URL', action = 'store', dest = 'url'),
    )

    help = 'Add a cross reference database if one with the provided name does not exist, or update the URL if it does.'
    def handle(self, *args, **options):
        name = options.get('name', None)
        url = options.get('url', None)
        try:
            xrdb = CrossRefDB.objects.get(name=name)
            if xrdb.url != url:
               xrdb.url = url
               xrdb.save()
        except CrossRefDB.DoesNotExist:
            xrdb = CrossRefDB(name=name, url=url)
            xrdb.save()


