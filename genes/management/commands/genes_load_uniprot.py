import sys
from django.core.management.base import BaseCommand
from genes.models import CrossRefDB, CrossRef, Gene
from optparse import make_option

import logging
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--uniprot_file', action='store', dest='uniprot',
                    help='Filtered uniprot file (i.e. with: zgrep -e "GeneID"'
                         ' -e "Ensembl" idmapping.dat.gz > '
                         'uniprot_entrez_ensembl.txt'),
    )
    help = 'Add UniProtKB cross references. *Note - Ensembl Cross-' + \
           'reference database must be loaded in Tribe before ' + \
           'running this command, as it will look for Ensembl IDs' + \
           ' if it finds no Entrez mappings.'

    def handle(self, *args, **options):
        uniprot_file = options.get('uniprot')
        if uniprot_file:

            uniprot = CrossRefDB.objects.get(name='UniProtKB')
            ensembl = CrossRefDB.objects.get(name='Ensembl')

            entrez_set = set(Gene.objects.all().values_list('entrezid',
                                                            flat=True))
            ensembl_set = set(CrossRef.objects.filter(
                                crossrefdb=ensembl).values_list('xrid',
                                                                flat=True))
            uniprot_file = open(uniprot_file)
            uniprot_entrez = {}
            uniprot_ensembl = {}

            for line in uniprot_file:
                (uniprot_id, id_type, identifier) = line.strip().split()

                if id_type == "GeneID":
                    # 'GeneID' is a mapping for entrez
                    entrez_id = int(identifier)
                    if entrez_id in entrez_set:
                        uniprot_entrez[uniprot_id] = entrez_id

                elif id_type == "Ensembl":
                    ensembl_id = identifier
                    if ensembl_id in ensembl_set:
                        uniprot_ensembl[uniprot_id] = ensembl_id

            for uniprot_id in uniprot_entrez.keys():
                gene = Gene.objects.get(entrezid=uniprot_entrez[uniprot_id])
                try:
                    uniprot_xr = CrossRef.objects.get(crossrefdb=uniprot,
                                                      xrid=uniprot_id)
                    uniprot_xr.gene = gene
                    uniprot_xr.save()
                except CrossRef.DoesNotExist:
                    uniprot_xr = CrossRef(crossrefdb=uniprot,
                                          xrid=uniprot_id, gene=gene)
                    uniprot_xr.save()

            uniprot_set = set(CrossRef.objects.filter(
                    crossrefdb=uniprot).values_list('xrid', flat=True))

            for uniprot_id, ensembl_id in uniprot_ensembl.iteritems():
                if uniprot_id not in uniprot_set:
                    # If there is already a UniProt xref with this id in
                    # the database it means that it was already added using
                    # Entrez. We are only interested in uniprot_ids that
                    # haven't been added
                    ensembl_xr = CrossRef.objects.filter(crossrefdb=ensembl,
                                                         xrid=ensembl_id)[0]

                    gene = ensembl_xr.gene
                    uniprot_xr = CrossRef(crossrefdb=uniprot,
                                          xrid=uniprot_id, gene=gene)
                    uniprot_xr.save()

            uniprot_file.close()
        else:
            logger.error("Couldn\'t load uniprot %s", options.get('uniprot'),
                         exc_info=sys.exc_info(), extra={'options': options})
