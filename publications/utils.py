import logging
logger = logging.getLogger(__name__)

from datetime import datetime
from xml.etree import ElementTree as ET

from django.conf import settings
import requests

from publications.models import Publication

def load_pmids(pmids, force_update=False):
    """
    Loads PMIDS passed as integers into the database when they do not already exist.
    """
    pmids = list(set([int(x) for x in pmids]))
    if not force_update:
        logger.info('Checking %s PMIDS', len(pmids))
        existing_pubs = set(Publication.objects.filter(pmid__in=pmids).values_list('pmid', flat=True))
        pmids = set(pmids)
        pmids.difference_update(existing_pubs)
    logger.info('About to fetch %s new PMIDs.', len(pmids), extra={'data':{'pmids': pmids}})
    if not pmids:
        return None
    pmids_mia = [str(x) for x in pmids]
    for i in xrange(len(pmids_mia) / 5000 + 1): #Efetch Maximum, Batch 5000 per request
        query_list = pmids_mia[i * 5000:(i + 1) * 5000]
        query_str = ','.join(query_list)
        qdict = settings.ETOOLS_CONFIG['query_params']
        qdict['id'] = query_str
        r = requests.post(settings.ETOOLS_CONFIG['base_url'], data=qdict) #have to use post if > 200
        pub_page = r.text
        if pub_page:
            xmltree = ET.fromstring(pub_page.encode('utf-8'))
            pubs = xmltree.findall('.//DocumentSummary')
            pub_dicts = map(parse_pub, pubs)
            for pub in pub_dicts:
                if pub is not None:
                    new_pub = None
                    if force_update:
                        try:
                            new_pub = Publication.objects.get(pmid=pub['pmid'])
                        except Publication.DoesNotExist:
                            new_pub = Publication()
                        new_pub.pmid = pub['pmid']
                        new_pub.title = pub['title']
                        new_pub.authors = pub['authors']
                        new_pub.date = pub['date']
                        new_pub.journal = pub['journal']
                        new_pub.volume = pub['volume']
                        new_pub.pages = pub['pages']
                        new_pub.issue = pub['issue']
                    else:
                        new_pub = Publication(**pub)
                    if not new_pub.issue:
                        logger.info('no issue for %s', new_pub.pmid)
                    if not new_pub.volume:
                        logger.info('no volume for %s', new_pub.pmid)
                    if not new_pub.pages:
                        logger.info('no pages for %s', new_pub.pmid)
                    new_pub.save()

#takes an Element from the esummary etree and parses it to a python dict
#appropriate for insertion as a publication
KEEP_NAMES = frozenset(('Source', 'Title', 'Volume', 'Issue', 'Pages', 'SortPubDate'))
PARSE_NAMES = frozenset(('Authors',))
def parse_pub(pub):
    logger.debug("Parsing PMID %s", pub.get('uid'))
    if pub.find('error') is not None:
        logger.warning("Error in request for PMID %s from pubmed server.", pub.get('uid'))
        return None
    rel_fields = reduce(dict_merge, map(extract_fields, pub))
    result = {}
    result['pmid'] = pub.get('uid')
    result['title'] = rel_fields['Title']
    result['authors'] = rel_fields['Authors']
    result['date'] = rel_fields['SortPubDate'].split(' ')[0]
    result['volume'] = rel_fields['Volume']
    result['issue'] = rel_fields['Issue']
    result['pages'] = rel_fields['Pages']

    result['date'] = datetime.strptime(result['date'], '%Y/%m/%d')
    result['journal'] = rel_fields['Source']
    return result

def extract_fields(field):
    field_name = field.tag
    if field_name in KEEP_NAMES:
        return {field_name: field.text}
    elif field_name in PARSE_NAMES:
        if field_name == 'Authors':
            names = [item.text for item in field.findall('.//Name')]
            author_str = ', '.join(names)
            return {'Authors': author_str}

def dict_merge(a, b):
    if a or b:
        if not a:
            return b
        if not b:
            return a
        return dict(a, **b)
    return None

