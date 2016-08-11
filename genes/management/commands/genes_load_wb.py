import logging
logger = logging.getLogger(__name__)

import sys
import urllib2
import gzip
from StringIO import StringIO

from django.core.management.base import BaseCommand
from django.db import IntegrityError, transaction
from django.db.utils import DatabaseError
from genes.models import Gene, CrossRefDB, CrossRef
from organisms.models import Organism
from optparse import make_option

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--wb_url', action = 'store', dest = 'wburl', help = "URL of wormbase xrefs file."),
        make_option('--db_name', action = 'store', dest = 'dbname', help = "Name of the database- defaults to 'WormBase'.", default="WormBase"),
        make_option('--taxonomy_id', action = 'store', dest = 'taxonomy_id', help = "taxonomy_id assigned by NCBI to this organism"),
    )

    help = 'Add wormbase identifiers to database.'
    def handle(self, *args, **options):
        #load the organism
        tax_id = options.get('taxonomy_id')
        org = Organism.objects.get(taxonomy_id = tax_id)

        database = CrossRefDB.objects.get(name=options.get('dbname'))
        wb_url = options.get('wburl')

        xrefs_gzip_fh = gzip.GzipFile(fileobj = StringIO(urllib2.urlopen(wb_url, timeout=5).read()))

        for line in xrefs_gzip_fh:
            toks = line.strip().split('\t')
            systematic = 'CELE_' + toks[0]
            wbid = toks[1]
            try:
                gene = Gene.objects.get(systematic_name=systematic)
            except Gene.DoesNotExist:
                logger.info("Unable to find gene %s.", systematic)
                continue
            wb = None
            try:
                wb = CrossRef.objects.get(xrid=wbid, crossrefdb=database)
            except CrossRef.DoesNotExist:
                wb = CrossRef(xrid=wbid, crossrefdb=database)
            wb.gene = gene
            wb.save()
        xrefs_gzip_fh.close()
