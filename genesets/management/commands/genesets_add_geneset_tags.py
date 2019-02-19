import logging
logger = logging.getLogger(__name__)

import sys
from datetime import date
from datetime import datetime

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from organisms.models import Organism
from genesets.models import Geneset

# This dictionary serves two purposes: To abbreviate the tag name that has to be
# entered in the command line, and to make sure users enter an accurate tag name.
TAG_NAMES = {
    't-s': 'tissue-specific'
}


class Command(BaseCommand):
    help = 'Management command to add geneset tags.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--tax_id',
            dest='tax_id',
            required=True,
            help=('Taxonomy ID assigned by NCBI to this organism. ' +
                  'This field is optional. If not provided, tags will be ' +
                  'applied to genesets of all organisms.')
        )

        parser.add_argument(
            '--tag_file',
            dest='tag_file',
            required=True,
            help='File mapping tags to genesets'
        )

        parser.add_argument(
            '--geneset_id_column',
            dest='geneset_column',
            required=True,
            help="Geneset Identification column (Can be GO, KEGG, or DO id #s)."
        )

        parser.add_argument(
            '--primary_tag_column',
            dest='tag_column',
            required=True,
            help='Primary tag column'
        )

        parser.add_argument(
            '--secondary_tag_column',
            dest='second_tag_column',
            required=True,
            help='Secondary tag column. This field is optional.'
        )

        parser.add_argument(
            '--gs_name_column',
            dest='gs_name_column',
            required=True,
            help='Geneset name column'
        )

        parser.add_argument(
            '--additional_tag',
            dest='additional_tag',
            help=('Code for additional tag name (such as "t-s" for ' +
                  '"tissue-specific"). This field is optional.')
        )

        parser.add_argument(
            '--header_present',
            dest='header',
            action='store_true',
            help='Optional flag, stating a header is present in the tag mapping file'
        )

    def handle(self, *args, **options):

        # Load the organism
        tax_id = options.get('tax_id')
        if tax_id:
            org = Organism.objects.get(taxonomy_id = tax_id)
        else:
            org = None

        # Mapping file information
        tag_file       = options.get('tag_file')
        geneset_column = options.get('geneset_column')
        tag_column     = options.get('tag_column')
        sec_gs_tag     = options.get('second_tag_column')
        gs_name_column = options.get('gs_name_column')
        header         = options.get('header')

        tag_abbrev = options.get('additional_tag')
        if tag_abbrev:
            additional_tag = TAG_NAMES[tag_abbrev]

        tag_file_fh = open(tag_file, 'r')
        if header:
            tag_file_fh.next()

        for line in tag_file_fh:
            toks = line.strip().split('\t')
            gs_id = toks[int(geneset_column)].split(':')
            gs_tag = toks[int(tag_column)]
            gs_name = toks[int(gs_name_column)]
            # Underscores may be used in files in place of spaces
            gs_name = gs_name.replace('_', ' ')

            # If Id column was not able to be split in two by ':', state this
            # term was not found
            if (len(gs_id) == 1):
                print('Geneset ' + str(toks[int(geneset_column)]) + '-' +
                      str(gs_name) + ' and organism ' + str(org) +
                      ' does not exist in our database'
                )
                continue

            # Search for genesets with specific ID and geneset name
            # ('icontains' makes it case-insensitive)
            gs_qset = Geneset.objects.filter(
                title__startswith=gs_id[0][:2]
            ).filter(title__contains=gs_id[1]).filter(title__icontains=gs_name)

            if org:
                gs_qset = gs_qset.filter(organism=org)

            # If the queryset is empty, mark geneset(s) as not found.
            if not gs_qset.exists():
                print('Geneset ' + str(toks[int(geneset_column)]) + '-' +
                      str(gs_name) + ' and organism ' + str(org) +
                      ' does not exist in our database'
                )
            else:
                for gs in gs_qset:
                    gs.tags.add(str(gs_tag))
                    if additional_tag:
                        gs.tags.add(str(additional_tag))
                    if sec_gs_tag:
                        gs.tags.add(str(toks[int(sec_gs_tag)]))

        tag_file_fh.close()
