import logging
logger = logging.getLogger(__name__)

import sys
import requests

from collections import defaultdict
from optparse import make_option

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.template.defaultfilters import slugify
from django.utils import timezone

from organisms.models import Organism
from genes.models import Gene
from versions.models import Version
from genesets.models import Geneset

KEGG_NAMES = {
    'Arabidopsis thaliana': 'ath',
    'Homo sapiens': 'hsa',
    'Mus musculus': 'mmu',
    'Rattus norvegicus': 'rno',
    'Danio rerio': 'dre',
    'Drosophila melanogaster': 'dme',
    'Saccharomyces cerevisiae': 'sce',
    'Caenorhabditis elegans': 'cel',
    'Pseudomonas aeruginosa': 'pae',
}

KEGG_URL_BASE = 'http://rest.kegg.jp'
KEGG_RECORD_TYPES = ('Pathway', 'Module', 'Disease')


def get_kegg_version(kegg_base):
    kegg_info = requests.get(kegg_base + '/info/kegg')
    kegg_iter = kegg_info.iter_lines()
    kegg_iter.next()
    release_line = kegg_iter.next()
    release = release_line.split('             ')[1]
    if not release.startswith('Release'):
        return None
    return release

def get_kegg_members(kegg_base, organism, record_type):
    kegg_members = requests.get(kegg_base + '/link/' + organism + '/' + record_type.lower())
    kegg_iter = kegg_members.iter_lines()
    results = defaultdict(set)
    for line in kegg_iter:
        toks = line.split()
        group = toks[0].split(':')[1]    # group listed first, has prefix
        geneid = toks[1].split(':')[1]  # gene listed second, has prefix
        results[group].add(geneid)
    return results

def get_kegg_info(kegg_base, identifier):
    kegg_record = requests.get(kegg_base + '/get/' + identifier)
    kegg_iter = kegg_record.iter_lines()
    result = {}
    for line in kegg_iter:
        if line.startswith('NAME'):
            result['title'] = ' '.join(line.split()[1:])
        if line.startswith('DESCRIPTION'):
            result['abstract'] = ' '.join(line.split()[1:])
    if 'title' in result:
        if not 'abstract' in result:
            result['abstract'] = ''
    return result

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--organism', dest='organism', help="Organism's full name."),
        make_option('--user', dest='user', default="tribeupdater", help="Username for the user to be assigned the created geneset/versions."),
        make_option('--gene_id', dest='gene_id', help="Enter a gene identifier to use (other than Entrez, which is the default) to map genes."),
        make_option('--kegg_record_types', dest='kegg_record_types', help="Desired KEGG Record Types, if something other than (Pathway, Module, Disease). Each record type should be separated by a comma from the rest."),
    )

    help = 'Load KEGG annotations for the listed organism and assign them to the passed user.'
    def handle(self, *args, **options):

        user_name = options.get('user')
        user = None
        try:
            user = User.objects.get(username = user_name)
        except User.DoesNotExist:
            logger.error('The user %s did not exist.', user_name, extra={'options': options})
            sys.exit()

        org = None
        try:
            org = Organism.objects.get(scientific_name = options.get('organism'))
        except Organism.DoesNotExist:
            logger.error('The organism %s did not exist.', options.get('organism'), extra={'options': options})
            sys.exit()

        version = get_kegg_version(KEGG_URL_BASE)
        if version is None:
            logger.error('The KEGG api may have changed. Release no longer starts with "Release".')
        else:
            logger.info('Working with KEGG version %s.', version)

        if (options.get('kegg_record_types')):
            kegg_record_types = (options.get('kegg_record_types')).replace(" ", "").split(",")
            kegg_record_types = tuple(kegg_record_types)
            logger.info('Requested KEGG Record Types are: %s', str(kegg_record_types))

        else:
            kegg_record_types = KEGG_RECORD_TYPES
            logger.info('Using pre-set KEGG Record Types')

        for record_type in kegg_record_types:
            logger.info('Starting record type %s.', record_type)
            record_members = get_kegg_members(KEGG_URL_BASE, KEGG_NAMES[org.scientific_name], record_type)
            for (record, members) in record_members.iteritems():
                if record_type == 'Module':
                    record = record.split('_').pop() #for modules, they are prefixed with species_
                slug = slugify(org.scientific_name + ' ' + record)
                gs_info = get_kegg_info(KEGG_URL_BASE, record)
                gs_info['title'] = 'KEGG-' + record_type + '-' + record + ': ' + gs_info['title'] #make title more search friendly
                try:
                    geneset = Geneset.objects.get(slug=slug)
                    changed = False
                    if geneset.title != gs_info['title']:
                        geneset.title = gs_info['title']
                        changed = True
                    if geneset.abstract != gs_info['abstract']:
                        geneset.abstract = gs_info['abstract']
                        changed = True
                    if changed:
                        geneset.save()

                except Geneset.DoesNotExist:
                    geneset = Geneset(creator=user, title=gs_info['title'], organism=org, abstract=gs_info['abstract'], slug=slug, public=True)
                    geneset.save()

                if (options.get('gene_id')):
                    gene_id = options.get('gene_id')
                    if (gene_id == 'systematic_name'):
                        annots = frozenset([(gene.pk, None) for gene in Gene.objects.filter(systematic_name__in=members)])
                    elif (gene_id == 'standard_name'):
                        annots = frozenset([(gene.pk, None) for gene in Gene.objects.filter(standard_name__in=members)])
                    else:
                        logger.error('gene_id entered is not supported (yet)')
                        return False
                else:
                    annots = frozenset([(gene.pk, None) for gene in Gene.objects.filter(entrezid__in=members)])

                most_recent_versions = Version.objects.filter(geneset=geneset).order_by('-commit_date')[:1]
                description = ''
                most_recent_version = None
                if most_recent_versions:
                    most_recent_version = most_recent_versions[0]
                    if (most_recent_version.commit_date > timezone.now()):
                        logger.error('Version from the future: %s.', most_recent_version)
                    new = annots - most_recent_version.annotations
                    removed = most_recent_version.annotations - annots
                    if (new or removed):
                        description = description + 'Added ' + str(len(new)) + ' and removed ' + str(len(removed)) + ' annotations from KEGG version ' + version + '.'
                else:
                    description = 'Created with ' + str(len(annots)) + ' annotations from KEGG version ' + version + '.'
                if description:
                    v_obj = Version(geneset=geneset, creator=user, parent=most_recent_version, commit_date=timezone.now())
                    v_obj.description = description
                    v_obj.annotations = annots
                    v_obj.save()


