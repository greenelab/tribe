from datetime import datetime
import time
from xml.etree import ElementTree as ET

from django.conf import settings
import requests

from publications.models import Publication

import logging
logger = logging.getLogger(__name__)


NUM_PUBMED_RETRIES = settings.ETOOLS_CONFIG['num_of_retries']


def load_pmids(pmids, force_update=False):
    """
    Loads publications into the database from a list of PubMed IDs passed
    as integers into the database when they do not already exist.
    """
    pmids = list(set([int(x) for x in pmids]))
    logger.debug('Starting to load PMID(S) %s', pmids)
    if not force_update:
        logger.info('Checking %s PMIDS', len(pmids))
        existing_pubs = set(Publication.objects.filter(pmid__in=pmids).values_list('pmid', flat=True))
        pmids = set(pmids)
        pmids.difference_update(existing_pubs)
    logger.info('About to fetch %s new PMIDs.', len(pmids), extra={'data':{'pmids': pmids}})
    if not pmids:
        logger.debug('pmids are none')
        return None
    pmids_mia = [str(x) for x in pmids]
    for i in xrange(len(pmids_mia) / 5000 + 1): #Efetch Maximum, Batch 5000 per request
        query_list = pmids_mia[i * 5000:(i + 1) * 5000]
        query_str = ','.join(query_list)
        qdict = settings.ETOOLS_CONFIG['query_params']
        qdict['id'] = query_str

        # Have to use post if data being sent is > 200
        r = requests.post(settings.ETOOLS_CONFIG['base_url'], data=qdict)

        error_cnt = 0
        while r.status_code != 200 and error_cnt < NUM_PUBMED_RETRIES:
            error_cnt += 1
            time.sleep(0.5)
            r = requests.post(settings.ETOOLS_CONFIG['base_url'],
                              data=qdict)

        if r.status_code != 200:
            logger.warning('Requests to the PubMed server with data %s failed '
                           'after %s attempts.', qdict, NUM_PUBMED_RETRIES + 1)

        pub_page = r.text
        if pub_page:
            logger.debug('Request to pubmed server returned pub_page')
            xmltree = ET.fromstring(pub_page.encode('utf-8'))
            pubs = xmltree.findall('.//DocumentSummary')

            # pub_dicts will be a list of publications, where each
            # of them is a dictionary
            pub_dicts = map(parse_pub, pubs)
            for index, pub in enumerate(pub_dicts):
                logger.debug('Making new pub %s', pub)
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
                    logger.debug('Finished saving pub %s', new_pub)

                else:
                    bad_pmid = pubs[index].get('uid')
                    logger.warning('PMID %s has no publication in pub_page %s',
                                   bad_pmid, pub_page)

        else:
            logger.warning('There was no page returned from pubmed server!!')


#takes an Element from the esummary etree and parses it to a python dict
#appropriate for insertion as a publication
KEEP_NAMES = frozenset(('Source', 'Title', 'Volume', 'Issue', 'Pages', 'SortPubDate'))
PARSE_NAMES = frozenset(('Authors',))
def parse_pub(pub):
    logger.debug("Parsing PMID %s", pub.get('uid'))
    if pub.find('error') is not None:
        logger.warning("Error in request for PMID %s from PubMed server.", pub.get('uid'))
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
    logger.debug("Finished parsing PMID %s", pub.get('uid'))
    logger.debug("Result for PMID %s is %s", pub.get('uid'), result)
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
