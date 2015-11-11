import logging
logger = logging.getLogger(__name__)

import sys

from django.core.management.base import BaseCommand
from django.db import IntegrityError, transaction
from django.db.utils import DatabaseError
from genes.models import Gene, CrossRefDB, CrossRef
from organisms.models import Organism
from optparse import make_option

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--geneinfo_file', action = 'store', dest = 'geneinfo', help = "gene_info file available for download from NCBI entrez"),
        make_option('--taxonomy_id', action = 'store', dest = 'taxonomy_id', help = "taxonomy_id assigned by NCBI to this organism"),
        make_option('--gi_tax_id', action = 'store', dest = 'gi_tax_id', help = "To work with cerivisiae's tax id change, use, this, otherwise we will just use tax_id"),
        make_option('--symbol_col', action = 'store', dest = 'symbol_col', help = "The column containing the symbol id.", default = 2),
        make_option('--systematic_col', action = 'store', dest = 'systematic_col', help = "The column containing the systematic id.  If this is '-' or blank, the symbol will be used", default = 3),
        make_option('--alias_col', action = 'store', dest = 'alias_col', help = "The column containing gene aliases.  If this is '-' or blank, the symbol will be used", default = 4),
        make_option('--put_systematic_in_xrdb', action = 'store', dest = 'systematic_xrdb', help = 'Optional: Name of Cross-Reference Database for which you want to use organism systematic IDs as CrossReference IDs (Used for Pseudomonas)'),
    )

    help = 'Add standards from stds_file with the associations from assoc_file.'
    def handle(self, *args, **options):
        #load the organism
        tax_id = options.get('taxonomy_id')
        org = Organism.objects.get(taxonomy_id = tax_id)

        #geneinfo file information
        geneinfo_filename = options.get('geneinfo')
        symb_col = int(options.get('symbol_col'))
        syst_col = int(options.get('systematic_col'))
        alias_col = int(options.get('alias_col'))
        systematic_xrdb = options.get('systematic_xrdb')

        #open the geneinfo file
        if geneinfo_filename:
            geneinfo_fh = open(geneinfo_filename)

        gi_tax_id = tax_id #yeast has a taxonomy_id that changed, in this case when we look at the id from NCBI we have to use the new one
        if options.get('gi_tax_id'):
            gi_tax_id = options.get('gi_tax_id')

        #get all genes for this organism from the database
        entrez_in_db = set(Gene.objects.filter(organism=org).values_list('entrezid', flat=True))
        #get all cross reference pairs that refer to a gene from this organism
        xr_in_db = set()
        for x in CrossRef.objects.filter(gene__entrezid__in=entrez_in_db).prefetch_related('crossrefdb', 'gene'):
            xr_in_db.add((x.crossrefdb.name, x.xrid, x.gene.entrezid))

        if tax_id and geneinfo_fh:
            #store all the genes seen thus far so we can remove obsolete entries
            entrez_seen = set()
            #store all the crossref pairs seen thus far to avoid duplicates
            xrdb_cache = {} #cache of cross reference databases, saves hits to DB
            org_matches = 0 #check to make sure the organism matched so that we don't mass-delete for no reason
            entrez_found = 0 #found from before
            entrez_updated = 0 #found from before and updated
            entrez_created = 0 #didn't exist, added
            for line in geneinfo_fh:
                toks = line.strip().split('\t')
                if not (toks[0] == gi_tax_id): #from the wrong organism, skip
                    continue

                org_matches += 1 #count lines that came from this organism
                #grab requested fields from tab delimited file
                (entrezid, standard_name, systematic_name, aliases, crossrefs, description, status, chromosome) = (int(toks[1]), toks[symb_col], toks[syst_col], toks[alias_col], toks[5], toks[8], toks[9], toks[6])

                #this column only gets filled in for certain organisms
                if (not systematic_name) or (systematic_name == '-'):
                    systematic_name = standard_name
                if chromosome == "MT": #gene is actually mitochondrial, change symbol to avoid dupes (analogous to what GeneCards does)
                    if not systematic_name.startswith('MT'):
                        logger.debug("Renaming %s to %s, mitochondrial version", systematic_name, "MT-" + systematic_name)
                        systematic_name = "MT-" + systematic_name

                alias_str = ""
                alias_num = 0
                if aliases and (aliases != '-'):
                    alias_list = [unicode(x) for x in aliases.split('|')]
                    alias_num = len(alias_list)
                    alias_str = ' '.join(alias_list)

                #handle cross references
                xref_tuples = []
                if crossrefs and (crossrefs != '-'):
                    xref_tuples = set()
                    if (systematic_xrdb):
                        xref_tuples.add( (unicode(systematic_xrdb), unicode(systematic_name)) ) 

                    xrefs = [unicode(x) for x in crossrefs.split('|')]
                    for x in xrefs:
                        xref_tuples.add( tuple(x.split(':')) )

                xref_num = len(xref_tuples)

                weight = 2*xref_num + alias_num #arbitrary weight for search results
                #principle of weighting is that we think people are more likely to want
                #a gene that occurs in more databases or has more aliases b/c its more
                #well known. This helps break ordering ties where gene names are identical.

                #we also assume that people are much more likely to want protein coding genes
                #in the long term we could measure actual selections and estimate weight per gene
                if status == 'protein-coding':
                    weight = weight * 2

                gene_object = None
                entrez_seen.add(entrezid)
                if entrezid in entrez_in_db: #this existed already
                    logger.debug("Entrez %s existed already.", entrezid)
                    entrez_found += 1
                    gene_object = Gene.objects.get(entrezid=entrezid, organism=org)
                    changed = False #following lines update characteristics that may have changed
                    if gene_object.systematic_name != systematic_name:
                        gene_object.systematic_name = systematic_name
                        changed = True
                    if gene_object.standard_name != standard_name:
                        gene_object.standard_name = standard_name
                        changed = True
                    if gene_object.description != description:
                        gene_object.description = description
                        changed = True
                    if gene_object.aliases != alias_str:
                        gene_object.aliases = alias_str
                        changed=True
                    if gene_object.weight != weight:
                        gene_object.weight = weight
                        changed=True
                    if gene_object.obsolete: #if the gene was marked obsolete
                        gene_object.obsolete = False #it's not if it occurs in the gene_info file
                        changed = True
                    if changed:
                        entrez_updated += 1
                        gene_object.save() #only call save if something changed to save time

                else: #new entrezid observed
                    logger.debug("Entrez %s did not exist and will be created.", entrezid)
                    gene_object = Gene(entrezid=entrezid, organism=org, systematic_name=systematic_name, standard_name=standard_name, description=description, obsolete=False, weight=weight)
                    gene_object.save()
                    entrez_created += 1

                #add crossreferences
                for xref_tuple in xref_tuples:
                    try:
                        xrdb = xrdb_cache[xref_tuple[0]]
                    except KeyError:
                        try:
                            xrdb = CrossRefDB.objects.get(name=xref_tuple[0])
                        except CrossRefDB.DoesNotExist:
                            xrdb = None
                        xrdb_cache[xref_tuple[0]] = xrdb
                    if xrdb is None: #don't understand crossrefdb, skip
                        logger.warning("We encountered an xrdb (%s) not in our database for pair %s.", xref_tuple[0], xref_tuple)
                        continue
                    logger.debug('Found crossreference pair %s.', xref_tuple)
                    if not (xref_tuple[0], xref_tuple[1], entrezid) in xr_in_db: #doesn't exist, create
                        xr_obj = CrossRef(crossrefdb=xrdb, xrid=xref_tuple[1], gene=gene_object)
                        xr_obj.save()


            logger.info("%s entrez identifiers existed in the database and were found in the new gene_info file", entrez_found)
            logger.info("%s entrez identifiers existed in the database and were changed in the new gene_info file", entrez_updated)
            logger.info("%s entrez identifiers did not exist and were created in the new gene_info file", entrez_created)
            if org_matches < 10:
                sys.stderr.write('Less than ten matches were encountered for this organism.  Check the organism ID.')
                sys.exit(1)
        else:
            logger.error('Couldn\'t load geneinfo %s for org %s.', options.get('geneinfo'), tax_id , exc_info = sys.exc_info(), extra = {'options': options})
