import logging
logger = logging.getLogger(__name__)

import sys
from datetime import date
from datetime import datetime
from collections import defaultdict
import re
from StringIO import StringIO

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.template.defaultfilters import slugify
from django.utils import timezone

import requests
import requests_ftp
requests_ftp.monkeypatch_session()

from go import go

from organisms.models import Organism
from genes.models import Gene
from versions.models import Version
from genesets.models import Geneset

from optparse import make_option

OMIM_FTP = 'ftp://ftp.omim.org/OMIM/'
DO_URL = 'http://sourceforge.net/p/diseaseontology/code/HEAD/tree/trunk/HumanDO.obo?format=raw'
class mim_disease:
    def __init__(self):
        self.mimid = ''
        self.is_susceptibility = 0 #Whether it has {}
        self.phe_mm = ''  #Phenotype mapping method
        self.genetuples = [] #(Gene ID, Gene Status)

LIMIT_TYPE = set(['gene','gene/phenotype'])
LIMIT_PHENO = '(3)'
LIMIT_STATUS = ['C','P']

#This should be standardized, but you never know
#Most disorders that have omimphenotypes fit this expression
FIND_MIMID = re.compile('\, [0-9]* \([1-4]\)')

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--user', dest='user', default="TribeUpdater", help="Username for the user to be assigned the created geneset/versions."),
    )

    help = 'Load DOID annotations using genes from OMIM.'
    def handle(self, *args, **options):

        user_name = options.get('user')
        user = None
        try:
            user = User.objects.get(username=user_name)
        except User.DoesNotExist:
            logger.error('The user %s did not exist.', user_name, extra={'options': options})
            sys.exit()

        org = None
        try:
            org = Organism.objects.get(scientific_name='Homo sapiens') #Only exists for human
        except Organism.DoesNotExist:
            logger.error('The organism %s did not exist.', 'Homo sapiens', extra={'options': options})
            sys.exit()


        obo_r = requests.get(DO_URL)

        obo_strio = StringIO(obo_r.text)
        disease_ontology = go()
        loaded_obo = disease_ontology.parse(obo_strio)

        doid_omim = {}
        obo_reversed_str_array = obo_r.text.splitlines()[::-1]
        while obo_reversed_str_array: #Loop from Dima @ Princeton
            line = obo_reversed_str_array.pop()
            if line == '[Term]':
                while line != '':
                     line = obo_reversed_str_array.pop()
                     if line.startswith('id:'):
                         doid = re.search('DOID:[0-9]+',line).group(0)
                     if line.startswith('xref: OMIM:'):
                         omim = re.search('[0-9]+',line).group(0)
                         if not doid_omim.has_key(doid):
                             doid_omim[doid] = set()
                         if omim not in doid_omim[doid]:
                             doid_omim[doid].add(omim)

        mim_gene = {}
        s = requests.Session()
        mim2gene_list = s.retr(OMIM_FTP + 'mim2gene.txt', auth=("anonymous", "casey.s.greene@dartmouth.edu")).text.splitlines()
        for line in mim2gene_list: #Loop from Dima @ Princeton
            toks = line.split('\t')
            mim = toks[0]
            gtype = toks[1]
            gid = toks[2]
            if gtype in LIMIT_TYPE:
                if mim in mim_gene:
                    logger.warning("MIM already exists: %s", mim)
                mim_gene[mim] = gid

        mimdiseases = {}
        genemap_list = s.retr(OMIM_FTP + "genemap", auth=("anonymous", "casey.s.greene@dartmouth.edu")).text.splitlines()
        for l in genemap_list: #Loop from Dima @ Princeton
            #The choice of fields relies on info from the genemap.key file from omim
            l_split = l.split('|')
            status = l_split[6].strip()
            mim_geneid = l_split[9].strip()
            disorders = l_split[13].strip()

            #continuation of disorder field
            d2 = l_split[14].strip()
            d3 = l_split[15].strip()
            if d2 != '': disorders= disorders + ' ' + d2
            if d3 != '': disorders= disorders + ' ' + d3

            if disorders != '' and status in LIMIT_STATUS and mim_gene.has_key(mim_geneid):
                #print 'Status ok, not blank and genemap has key'

                geneid = mim_gene[mim_geneid]
                tuple_gid_status = (geneid, status)

                disorders_list = disorders.split(';')
                for d in disorders_list:
                    if '[' not in d and '?' not in d:
                        mim_info = re.search(FIND_MIMID,d)
                        if mim_info:
                            #print 'Has necessary info'
                            #TODO: Make sure to include ? and [
                            info_split = mim_info.group(0).split(' ')
                            mim_disease_id = info_split[1].strip()
                            mim_phetype = info_split[2].strip()
                            if mim_phetype == LIMIT_PHENO:
                                #print 'Correct phenotype'
                                if not mimdiseases.has_key(mim_disease_id):
                                    mimdiseases[mim_disease_id] = mim_disease()
                                    mimdiseases[mim_disease_id].mimid = mim_disease_id
                                    mimdiseases[mim_disease_id].phe_mm = mim_phetype
                                if '{' in d:
                                    mimdiseases[mim_disease_id].is_susceptibility = 1
                                if tuple_gid_status not in mimdiseases[mim_disease_id].genetuples:
                                    mimdiseases[mim_disease_id].genetuples.append(tuple_gid_status)

        logger.debug(disease_ontology.go_terms)
        entrez_gid = {}
        for doid in doid_omim.keys():
            term = disease_ontology.get_term(doid)
            if term is None:
                continue
            logger.info("Processing %s", term)
            omim_list = doid_omim[doid]
            for o in omim_list:
                omim_id = o
                if mimdiseases.has_key(omim_id):
                    mim_entry = mimdiseases[omim_id]
                    if mim_entry.is_susceptibility:
                        d_or_s = 'S'
                    else:
                        d_or_s = 'D'
                    for g in mim_entry.genetuples:
                        entrez = int(g[0])
                        if entrez in entrez_gid:
                            term.add_annotation(gid=entrez_gid[entrez], ref=None)
                        else:
                            gene = Gene.objects.get(entrezid=entrez)
                            entrez_gid[entrez] = gene.id
                            term.add_annotation(gid=gene.id, ref=None)

        disease_ontology.populated = True #mark annotated
        disease_ontology.propagate() #prop annotations

        for (term_id, term) in disease_ontology.go_terms.iteritems():
            if term.annotations:
                logger.info("Creating %s", term)
                slug = slugify(' '.join((term.go_id, org.scientific_name, term.full_name)))[:50] #make first 50 chars into a slug

                doid = term.go_id
                do_num = doid.split(':')[1]
                #construct title
                title = 'DO' + '-' + do_num + ':' + term.full_name

                #construct abstract
                #write evidence as string
                omim_clause = ''
                if doid in doid_omim:
                    omim_list = list(doid_omim[doid])
                    if len(omim_list):
                        omim_clause = ' Annotations directly to this term are provided by the OMIM disease ID'
                        if len(omim_list) == 1:
                            omim_clause = omim_clause + ' ' + omim_list[0]
                        else:
                            omim_clause = omim_clause + 's ' + ', '.join(omim_list[:-1]) + ' and ' + omim_list[-1]
                        omim_clause = omim_clause + '.'

                description = ''
                if term.description:
                    description += term.description
                description += ' Annotations from child terms in the disease ontology are propagated through transitive closure.' + omim_clause
                logger.info(description)

                #get geneset
                changed = False
                try:
                    gs_obj = Geneset.objects.get(slug=slug, creator=user)
                    changed = False #flag to know if we need to call save

                    #all these genesets should be public
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
                    gs_obj = Geneset(title=title, slug=slug, creator=user, organism=org, public=True, abstract=description)
                    changed = True

                #if anything changed
                if changed:
                    gs_obj.save()

                #load annotations
                most_recent_versions = Version.objects.filter(geneset=gs_obj).order_by('-commit_date')[:1]
                annots = set([(annotation.gid, annotation.ref) for annotation in term.annotations])
                description = ''
                most_recent_version = None
                if most_recent_versions:
                    most_recent_version = most_recent_versions[0]
                    if (most_recent_version.commit_date > timezone.now()):
                        logger.error('Version from the future: %s.', most_recent_version)
                    new = annots - most_recent_version.annotations
                    removed = most_recent_version.annotations - annots
                    if (new or removed):
                        description = description + 'Added ' + str(len(new)) + ' and removed ' + str(len(removed)) + ' annotations from OMIM and the disease ontology.'
                else:
                    description = 'Created with ' + str(len(annots)) + ' annotations from OMIM and the disease ontology.'
                if description:
                    v_obj = Version(geneset=gs_obj, creator=user, parent=most_recent_version, commit_date=timezone.now())
                    v_obj.description = description
                    v_obj.annotations = annots
                    v_obj.save()


