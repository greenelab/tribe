import logging
logger = logging.getLogger(__name__)

import sys
from django.core.management.base import BaseCommand
from genes.models import CrossRefDB, CrossRef, Gene
from optparse import make_option

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--uniprot_file', action = 'store', dest = 'uniprot', help = 'filtered uniprot file (i.e. with: zgrep "GeneID" idmapping.dat.gz > uniprot_entrez.txt'),
    )

    help = 'Add UniProtKB cross references.'
    def handle(self, *args, **options):
        uniprot_file = options.get('uniprot')
        if uniprot_file:
            uniprot_file = open(uniprot_file)
        if uniprot_file:
            entrez_set = set(Gene.objects.all().values_list('entrezid', flat = True))
            uniprot_entrez = {}
            for line in uniprot_file:
                (uniprot_id, junk, entrez_id) = line.strip().split()
                entrez_id = int(entrez_id)
                if entrez_id in entrez_set:
                    uniprot_entrez[uniprot_id] = entrez_id
            uniprot = CrossRefDB.objects.get(name = 'UniProtKB')
            for uniprot_id in uniprot_entrez.keys():
                gene = Gene.objects.get(entrezid=uniprot_entrez[uniprot_id])
                try:
                    uniprot_xr = CrossRef.objects.get(crossrefdb = uniprot, xrid = uniprot_id)
                    uniprot_xr.gene = gene
                    uniprot_xr.save()
                except CrossRef.DoesNotExist:
                    uniprot_xr = CrossRef(crossrefdb = uniprot, xrid = uniprot_id, gene = gene)
                    uniprot_xr.save()
            uniprot_file.close()
        else:
            logger.error("Couldn\'t load uniprot %s", options.get('uniprot'), exc_info = sys.exc_info(), extra = {'options': options})




