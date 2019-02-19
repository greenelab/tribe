import logging
logger = logging.getLogger(__name__)

import sys
from datetime import date, datetime
from django.core.management.base import BaseCommand

from genesets.models import Geneset
from versions.exceptions import VersionContainsNoneGene


class Command(BaseCommand):
    help = 'Management command to update geneset tip item/gene count field'

    def handle(self, *args, **options):
        for geneset in Geneset.objects.all():
            tip_version = geneset.get_tip()
            if tip_version is not None:
                try:
                    tip_version.save()
                except VersionContainsNoneGene:
                    logger.error('Version %s contained None as one of its genes', tip_version)
                    sys.exit()
            else:
                continue
