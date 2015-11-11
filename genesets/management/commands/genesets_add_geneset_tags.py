import logging
logger = logging.getLogger(__name__)

import sys
from datetime import date
from datetime import datetime

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from organisms.models import Organism
from genesets.models import Geneset

from optparse import make_option

# This dictionary serves two purposes: To abbreviate the tag name that has to be
# entered in the command line, and to make sure users enter an accurate tag name.
TAG_NAMES = {
    't-s': 'tissue-specific'
}

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--tax_id', dest='tax_id', help='Taxonomy ID assigned by NCBI to this organism. This field is optional. If not provided, tags will be applied to genesets of all organisms.'),
        make_option('--tag_file', dest='tag_file', help='File mapping tags to genesets'),
        make_option('--geneset_id_column', dest='geneset_column', help="Geneset Identification column (Can be GO, KEGG, or DO id #s)."),
        make_option('--primary_tag_column', dest='tag_column', help='Primary tag column'),
        make_option('--secondary_tag_column', dest='second_tag_column', help='Secondary tag column. This field is optional.'),
        make_option('--gs_name_column', dest='gs_name_column', help='Geneset name column'),
        make_option('--additional_tag', dest='additional_tag', help='Code for additional tag name (such as "t-s" for "tissue-specific"). This field is optional.'),
        make_option('--header_present', dest='header', action='store_true', help='Optional flag, stating a header is present in the tag mapping file'),
    )

    help = 'Management command to add geneset tags.'

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
            gs_name = gs_name.replace('_', ' ') # Underscores may be used in files in place of spaces

            if (len(gs_id) == 1): # If Id column was not able to be split in two by ':', state this term was not found
                print('Geneset ' + str(toks[int(geneset_column)]) + '-' + str(gs_name) + ' and organism ' + str(org) + ' does not exist in our database')
                continue


            # Search for genesets with specific ID and geneset name ('icontains' makes it case-insensitive)
            gs_qset = Geneset.objects.filter(title__startswith=gs_id[0][:2]).filter(title__contains=gs_id[1]).filter(title__icontains=gs_name)

            if org:
                gs_qset = gs_qset.filter(organism=org)

            if not gs_qset.exists(): # If the queryset is empty, mark geneset(s) as not found.
                print('Geneset ' + str(toks[int(geneset_column)]) + '-' + str(gs_name) + ' and organism ' + str(org) + ' does not exist in our database')

            else:
                for gs in gs_qset:
                    gs.tags.add(str(gs_tag))
                    if additional_tag:
                        gs.tags.add(str(additional_tag))
                    if sec_gs_tag:
                        gs.tags.add(str(toks[int(sec_gs_tag)]))

        tag_file_fh.close()

