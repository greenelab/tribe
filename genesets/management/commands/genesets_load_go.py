import logging
logger = logging.getLogger(__name__)

import sys
from datetime import date
from datetime import datetime
import urllib2
import gzip
import io

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.template.defaultfilters import slugify
from django.utils import timezone

from go import go

from organisms.models import Organism
from genes.models import Gene, CrossRefDB, CrossRef
from versions.models import Version
from genesets.models import Geneset
from publications.models import Publication
from publications.utils import load_pmids

GO_NAMES = {
    'Arabidopsis thaliana': 'tair',
    'Homo sapiens': 'goa_human',
    'Mus musculus': 'mgi',
    'Rattus norvegicus': 'rgd',
    'Danio rerio': 'zfin',
    'Drosophila melanogaster': 'fb',
    'Saccharomyces cerevisiae': 'sgd',
    'Caenorhabditis elegans': 'wb',
    'Pseudomonas aeruginosa': 'pseudocap',
}

GO_NAMESPACE_MAP = {
    'biological_process': 'BP',
    'molecular_function': 'MF',
    'cellular_component': 'CC',
}

GO_ASSOC_FTP = 'http://www.geneontology.org/gene-associations/'
GO_ASSOC_PREFIX = 'gene_association'
GO_ASSOC_SUFFIX = 'gz'

GO_OBO_URL = 'http://www.geneontology.org/ontology/obo_format_1_2/gene_ontology.1_2.obo'

DB_REMAP = {
    'FB': 'FLYBASE',
    'WB': 'WormBase',
}

class Command(BaseCommand):
    help = ('Load GO annotations. If initial load, use dates for versions. ' +
            'Otherwise use changes from latest for versions.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--organism',
            dest='organism',
            help="Organism's full name."
        )

        parser.add_argument(
            '--evidence',
            dest='evcodes',
            help=('Evidence codes that are included. All others will be ' +
                  'skipped. Comma separated (e.g. IEA,IDA).'
            )
        )

        parser.add_argument(
            '--user',
            dest='user',
            default='TribeUpdater',
            help='Username for the user to be assigned the created geneset/versions.'
        )

        parser.add_argument(
            '--obo',
            dest='obo',
            help='Location of obo file if not remote'
        )

        parser.add_argument(
            '--annot',
            dest='annot',
            help='Location of annotation file if not remote'
        )

        parser.add_argument(
            '--leading',
            dest='leading',
            action='store_true',
            help=('Is there a leading tag on the database IDs column (i.e. the ' +
                  'mouse gene ids all start with "MGI:" which must be removed).'
            )
        )

        parser.add_argument(
            '--remote',
            dest='remote',
            action="store_true",
            help='Load from remote URL. If used, this supercedes the annot and obo options.'
        )

        parser.add_argument(
            '--initial',
            dest='initial',
            action="store_true",
            help=('This is the initial load. If true, this uses dates from ' +
                  'the annotation file to construct versions. Otherwise a ' +
                  'difference from the current version is calculated to ' +
                  'determine whether or not a new version should be made.'
            )
        )

        parser.add_argument(
            '--tair',
            dest='tair',
            action='store_true',
            help=("When adding Arabidopsis GO terms, TAIR's locus IDs are " +
                  "not useful, so this command will find other gene IDs in GO file."
            )
        )

        parser.add_argument(
            '--only_wb',
            dest='only_wb',
            action='store_true',
            help="Load only GO terms that use WB identifiers."
        )

        parser.add_argument(
            '--pseudomonas',
            dest='pseudomonas',
            action='store_true',
            help=('If this option is passed, the command will search for ' +
                  'gene systematic names as well as PseudoCAP identifiers.'
            )
        )

    def handle(self, *args, **options):

        user_name = options.get('user')
        user = None
        try:
            user = User.objects.get(username=user_name)
        except User.DoesNotExist:
            logger.error(
                'The user %s did not exist.',
                user_name,
                extra={'options': options}
            )
            sys.exit()

        org = None
        try:
            org = Organism.objects.get(scientific_name=options.get('organism'))
        except Organism.DoesNotExist:
            logger.error(
                'The organism %s did not exist.',
                options.get('organism'),
                extra={'options': options}
            )
            sys.exit()

        accepted_evcodes = None
        if options.get('evcodes'):
            accepted_evcodes = set(options.get('evcodes').split(','))

        gene_ontology = go()
        remote = options.get('remote') != None
        obo_location = GO_OBO_URL if remote else options.get('obo')
        loaded_obo = gene_ontology.load_obo(
            obo_location, remote_location=remote, timeout=5
        )

        if not loaded_obo:
            logger.error(
                "Couldn't load OBO file %s with remote equal to %s.",
                obo_location, remote
            )
            sys.exit()

        annot_zip_fh = None
        annot_fh = None
        if remote:
            annot_zip_fh = urllib2.urlopen(
                GO_ASSOC_FTP + '.'.join(
                    (GO_ASSOC_PREFIX,
                     GO_NAMES[org.scientific_name],
                     GO_ASSOC_SUFFIX
                    )
                ),
                timeout=5)
        else:
            annot_zip_fh = open(options.get('annot'))
        annot_fh = gzip.GzipFile(fileobj=io.BytesIO(annot_zip_fh.read()))
        annot_zip_fh.close()

        annots = []
        load_pairs = {}
        pubs = set()

        for line in annot_fh:
            if line.startswith('!'):
                continue
            toks = line.strip().split('\t')

            (xrdb, xrid, details, goid, ref, ev, date) = (
                toks[0], toks[1], toks[3], toks[4], toks[5], toks[6], toks[13]
            )

            if options.get('tair'):
                import re
                tair_regex = re.compile('AT[0-9MC]G[0-9][0-9][0-9][0-9][0-9]')
                first_alias = toks[10].split('|')[0]
                if tair_regex.match(toks[2]):
                    xrid = toks[2]
                elif tair_regex.match(toks[9]):
                    xrid = toks[9]
                elif tair_regex.match(first_alias):
                    xrid = first_alias

            if options.get('only_wb') and (toks[0] != 'WB'):
                continue

            if details == 'NOT':
                continue
            if accepted_evcodes is not None and not (ev in accepted_evcodes):
                continue

            if options.get('leading') is not None:
                xrid = xrid.split(':')[1]

            try:
                load_pairs[xrdb].append(xrid)
            except KeyError:
                load_pairs[xrdb] = [xrid,]

            refs = ref.split('|')
            for ref_item in refs:
                if ref_item.startswith('PMID:'):
                    pubs.add(ref_item.split(':')[1])
                else:
                    logger.info("Unknown publication key %s", ref_item)
            annots.append((xrdb, xrid, goid, ref, date))

        xref_cache = {}

        if options.get('pseudomonas'):
            logger.info('Pseudomonas entered')
            for (xrdb, xrids) in load_pairs.iteritems():
                gene_objs = Gene.objects.filter(systematic_name__in=xrids)
                logger.info(
                    "Mapped %s Pseudomonas genes from the database using gene systematic name.",
                    gene_objs.count()
                )
                for gene_obj in gene_objs:
                    xref_cache[(xrdb, gene_obj.systematic_name)] = gene_obj

        else:
            for (xrdb, xrids) in load_pairs.iteritems():
                if xrdb in DB_REMAP:
                    xrdb = DB_REMAP[xrdb]
                try:
                    xrdb_obj = CrossRefDB.objects.get(name=xrdb)
                except CrossRefDB.DoesNotExist:
                    logger.warning("Couldn't find the cross reference DB %s.", xrdb)
                    continue
                xrid_objs = CrossRef.objects.filter(
                    crossrefdb=xrdb_obj).filter(xrid__in=xrids)
                logger.info(
                    "Mapped %s cross references from %s",
                    xrid_objs.count(),
                    xrdb
                )
                for xrid_obj in xrid_objs:
                    xref_cache[(xrdb, xrid_obj.xrid)] = xrid_obj.gene

        load_pmids(pubs)
        pub_cache = {}
        pub_values = Publication.objects.filter(pmid__in=pubs).only(
            'id', 'pmid').values()
        for pub in pub_values:
            pub_cache[pub['pmid']] = pub['id']

        for annot in annots:
            (xrdb, xrid, goid, ref, date) = annot
            if xrdb in DB_REMAP:
                xrdb = DB_REMAP[xrdb]
            try:
                gene = xref_cache[(xrdb, xrid)]
            except KeyError:
                logger.debug("Couldn't find xrid %s in xrdb %s.", xrid, xrdb)
                logger.info("Couldn't find xrid %s in xrdb %s.", xrid, xrdb)
                continue
            refs = ref.split('|')
            pub = None
            for ref_item in refs:
                if ref_item.startswith('PMID:'):
                    try:
                        pub = pub_cache[int(ref_item.split(':')[1])]
                    except KeyError:
                        pub = None
            gene_ontology.add_annotation(
                go_id=goid, gid=gene.pk, ref=pub, date=date, direct=True
            )

        gene_ontology.populated = True  # mark annotated
        gene_ontology.propagate()       # prop annotations

        evlist = list(accepted_evcodes)
        for (term_id, term) in gene_ontology.go_terms.iteritems():
            if term.annotations:
                slug = slugify(
                    ' '.join((term.go_id, org.scientific_name, term.full_name))
                )[:50]  # make first 50 chars into a slug


                namespace = GO_NAMESPACE_MAP[term.get_namespace()]
                go_id = term.go_id.split(':')[1]
                # construct title
                title = 'GO' + '-' + namespace + '-' + go_id + ':' + term.full_name

                # construct abstract
                # write evidence as string
                evclause = ''
                if len(evlist):
                    evclause = ' Only annotations with evidence coded as '
                    if len(evlist) == 1:
                        evclause = evclause + evlist[0]
                    else:
                        evclause = evclause + ', '.join(evlist[:-1]) + ' or ' + evlist[-1]
                    evclause = evclause + ' are included.'
                if term.description:
                    description = (
                        term.description +
                        ' Annotations are propagated through transitive ' +
                        'closure as recommended by the GO Consortium.' +
                        evclause
                    )
                else:
                    logger.info("No description on term %s", term)

                # get geneset
                changed = False
                try:
                    gs_obj = Geneset.objects.get(slug=slug, creator=user)
                    changed = False #flag to know if we need to call save

                    # all these genesets should be public
                    if not gs_obj.public:
                        gs_obj.public = True
                        changed = True

                    if gs_obj.title != title:
                        gs_obj.title = title
                        changed = True

                    if gs_obj.abstract != description:
                        gs_obj.abstract = description
                        changed = True

                except Geneset.DoesNotExist:
                    gs_obj = Geneset(
                        title=title,
                        slug=slug,
                        creator=user,
                        organism=org,
                        public=True,
                        abstract=description
                    )
                    changed = True

                # if anything changed
                if changed:
                    gs_obj.save()

                if options.get('initial'):
                    # disable commit field's auto_now_add, allows us to set a
                    # prior annotation date
                    commit_date = Version._meta.get_field_by_name('commit_date')[0]
                    commit_date.auto_now_add = False
                    logger.info(
                        'Initial load. Need to construct versions of %s from annotation date.',
                        term.go_id
                    )
                    date_annots = {}
                    for annotation in term.annotations:
                        date = timezone.make_aware(
                            datetime.strptime(annotation.date, '%Y%m%d'),
                            timezone.get_default_timezone()
                        )
                        try:
                            date_annots[date].append(annotation)
                        except KeyError:
                            date_annots[date] = [annotation, ]
                    annots_as_of_date = set()
                    prior_annots = set()
                    prior_version = None
                    for (date, annots) in sorted(date_annots.iteritems()):
                        annots_as_of_date.update(
                            [(annotation.gid, annotation.ref) for annotation in annots]
                        )

                        # if nothing changed, continue
                        if (annots_as_of_date == prior_annots):
                            continue

                        v_obj = Version(
                            geneset=gs_obj,
                            creator=user,
                            parent=prior_version,
                            commit_date=date
                        )
                        v_obj.description = (
                            "Added " + str(len(annots)) +
                            " annotations from GO based on the dates provided in the GO annotation file."
                        )
                        v_obj.annotations = annots_as_of_date
                        v_obj.save()
                        prior_version = v_obj
                        prior_annots = annots_as_of_date.copy()
                    # re-enable auto_now_add
                    commit_date.auto_now_add = True
                else:
                    # load annotations
                    most_recent_versions = Version.objects.filter(
                        geneset=gs_obj).order_by('-commit_date')[:1]
                    annots = set(
                        [(annotation.gid, annotation.ref) for annotation in term.annotations]
                    )
                    description = ''
                    most_recent_version = None
                    if most_recent_versions:
                        most_recent_version = most_recent_versions[0]
                        if (most_recent_version.commit_date > timezone.now()):
                            logger.error(
                                'Version from the future: %s.',
                                most_recent_version
                            )
                        new = annots - most_recent_version.annotations
                        removed = most_recent_version.annotations - annots
                        if (new or removed):
                            description = (
                                description + 'Added ' + str(len(new)) +
                                ' and removed ' + str(len(removed)) +
                                ' annotations from GO.'
                            )
                    else:
                        description = (
                            'Created with ' + str(len(annots)) +
                            ' annotations from GO.'
                        )
                    if description:
                        v_obj = Version(
                            geneset=gs_obj,
                            creator=user,
                            parent=most_recent_version,
                            commit_date=timezone.now()
                        )
                        v_obj.description = description
                        v_obj.annotations = annots
                        v_obj.save()
