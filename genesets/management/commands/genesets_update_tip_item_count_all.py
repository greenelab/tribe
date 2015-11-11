import logging
logger = logging.getLogger(__name__)

import sys
from datetime import date, datetime

from django.core.management.base import BaseCommand
from optparse import make_option

from genesets.models import Geneset
from versions.exceptions import VersionContainsNoneGene


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--all', dest='all', action='store_true', help='Enter this flag to update the tip_item_count attribute for all genesets in the database.'),
    )

    help = 'Management command to update geneset tip item/gene count field'

    def handle(self, *args, **options):
        all_flag = options.get('all') # More than anything this flag is a security switch to make sure the users know they will update all genesets in the database
        if all_flag == None:
            logger.error('The flag "--all" is required for this management command.')
            sys.exit()

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


