"""
Version tests
"""
import string

from django.test import TestCase
from django.utils.crypto import get_random_string
from django.contrib.auth.models import User

from tastypie.test import ResourceTestCase, TestApiClient

from organisms.models import Organism
from genes.models import Gene, CrossRef, CrossRefDB
from genesets.models import Geneset
from versions.models import Version
from versions.exceptions import VersionContainsNoneGene
from publications.models import Publication
from publications.utils import load_pmids

from fixtureless import Factory
factory = Factory()


class ReturnDesiredXridsTestCase(ResourceTestCase):
    """
    Testing that version annotations are returned using requested
    gene cross-reference identifier. In turn, this checks the API methods in
    VersionResource that dehydrate annotations are working appropriately.
    """

    def setUp(self):
        # This line is important to set up the test case!
        super(ReturnDesiredXridsTestCase, self).setUp()

        # Need to specify username, otherwise will get error:
        # 'Invalid resource lookup data provided (mismatched type)'
        # when using a fixtureless username in the url (weird characters).
        self.user1 = factory.create(User, {'username': 'asdf'})

        self.org1 = factory.create(Organism)

        self.g1 = factory.create(Gene)
        self.g2 = factory.create(Gene)
        self.g3 = factory.create(Gene)
        self.g4 = factory.create(Gene)

        # Need to specify xrdb name. Otherwise, fixtureless might make the
        # name an empty string, which would raise an error.
        self.xrdb1 = factory.create(CrossRefDB, {'name': 'XRDB1'})
        self.xrdb2 = factory.create(CrossRefDB, {'name': 'XRDB2'})
        self.xrdb3 = factory.create(CrossRefDB, {'name': 'XRDB3'})

        self.xref1 = factory.create(CrossRef, {'crossrefdb': self.xrdb1,
                                               'gene': self.g1})
        self.xref1b = factory.create(CrossRef, {'crossrefdb': self.xrdb2,
                                                'gene': self.g1})
        self.xref2 = factory.create(CrossRef, {'crossrefdb': self.xrdb1,
                                               'gene': self.g2})
        self.xref2b = factory.create(CrossRef, {'crossrefdb': self.xrdb2,
                                                'gene': self.g2})
        self.xref3 = factory.create(CrossRef, {'crossrefdb': self.xrdb1,
                                               'gene': self.g3})
        self.xref3b = factory.create(CrossRef, {'crossrefdb': self.xrdb2,
                                                'gene': self.g3})
        self.xref4 = factory.create(CrossRef, {'crossrefdb': self.xrdb1,
                                               'gene': self.g4})
        self.xref4b = factory.create(CrossRef, {'crossrefdb': self.xrdb2,
                                                'gene': self.g4})

        self.geneset1 = Geneset.objects.create(
                            organism=self.org1, creator=self.user1,
                            title='Test RNA polymerase II geneset',
                            abstract='Sample abstract.', public=True)

        # This first version is the only one that is allowed to have
        # a parent version unspecified. *Note: also must fill in publications
        # as None, instead of just leaving a blank after the comma in tuple.
        self.version1 = Version.objects.create(
                            geneset=self.geneset1, creator=self.user1,
                            description='Sample description',
                            annotations=frozenset([
                                (self.g1.pk, None),
                                (self.g2.pk, None), (self.g3.pk, None),
                                (self.g4.pk, None)]))

        self.desired_version_url = '/api/v1/version/' + self.user1.username + \
                                   '/' + self.geneset1.slug + '/' + \
                                   self.version1.ver_hash

        self.client = TestApiClient()

    def get_version_annotations(self, request_params={}):
        """
        Utility function used to make the request to the TestApiClient and
        return the version's annotations. We took code that was being
        repeated in all the test functions below and refactored it into this
        function.
        """
        response = self.client.get(self.desired_version_url, format="json",
                                   data=request_params)
        self.assertValidJSONResponse(response)
        annotations = self.deserialize(response)['annotations']
        return annotations

    def testNoXridSpecified(self):
        """
        If no xrid is specified (as is the case most of the time), check that
        gene objects containing the Entrez ID AND standard name (symbol) are
        returned.
        """
        annotations = self.get_version_annotations()

        returned_gene_set = set()
        for annot in annotations:
            returned_gene_set.add((annot['gene']['entrezid'],
                                   annot['gene']['standard_name']))

        desired_gene_set = set([(gene.entrezid, gene.standard_name)
                                for gene in Gene.objects.all()])
        self.assertEqual(returned_gene_set, desired_gene_set)

    def testGetEntrezIds(self):
        """
        If the xrid specified is Entrez, check that gene objects containing
        the gene's Entrez ID are returned.
        """
        request_params = {'xrid': 'Entrez'}
        annotations = self.get_version_annotations(request_params)

        returned_gene_set = set()
        for annotation in annotations:
            returned_gene_set.add(annotation['gene']['entrezid'])

        desired_gene_set = set([gene.entrezid for gene in Gene.objects.all()])

        self.assertEqual(returned_gene_set, desired_gene_set)

    def testGetSymbols(self):
        """
        If symbols are requested, check that gene objects containing
        standard names are returned.
        """
        request_params = {'xrid': 'Symbol'}
        annotations = self.get_version_annotations(request_params)

        returned_gene_set = set()
        for annotation in annotations:
            returned_gene_set.add(annotation['gene']['standard_name'])

        desired_gene_set = set([gene.standard_name
                                for gene in Gene.objects.all()])

        self.assertEqual(returned_gene_set, desired_gene_set)

    def testGettingXrdb1(self):
        """
        Check that all genes in the annotations are returned with the type
        of xrid in xrdb1.
        """
        request_params = {'xrid': self.xrdb1.name}
        annotations = self.get_version_annotations(request_params)

        returned_gene_set = set()
        for annotation in annotations:
            returned_gene_set.add(annotation['gene']['xrid'])

        desired_gene_set = set([self.xref1.xrid, self.xref2.xrid,
                                self.xref3.xrid, self.xref4.xrid])
        self.assertEqual(returned_gene_set, desired_gene_set)

    def testGettingXrdb2(self):
        """
        Check that all genes in the annotations are returned with the type
        of xrid in xrdb2.
        """
        request_params = {'xrid': self.xrdb2.name}
        annotations = self.get_version_annotations(request_params)

        returned_gene_set = set()
        for annotation in annotations:
            returned_gene_set.add(annotation['gene']['xrid'])

        desired_gene_set = set([self.xref1b.xrid, self.xref2b.xrid,
                                self.xref3b.xrid, self.xref4b.xrid])

        self.assertEqual(returned_gene_set, desired_gene_set)

    def testGettingXrdb3(self):
        """
        When requesting a type of xrid that is inexistent for the requested
        genes, check that an empty set is returned.
        """
        request_params = {'xrid': self.xrdb3.name}
        annotations = self.get_version_annotations(request_params)

        returned_gene_set = set()
        for annotation in annotations:
            returned_gene_set.add(annotation['gene'])

        self.assertEqual(returned_gene_set, set([]))

    def testNonExistentXrdb(self):
        """
        Check that an error is returned if the user requests identifiers from
        an xrdb not loaded into our database.
        """
        request_params = {'xrid': 'qwerty'}

        response = self.client.get(self.desired_version_url, format="json",
                                   data=request_params)

        self.assertHttpBadRequest(response)
        self.assertEqual(self.deserialize(response)['error'], 'The type of '
                         'gene identifier (xrid) you requested is not in our '
                         'database.')


class DownloadVersionAsCSVTestCase(ResourceTestCase):
    """
    Testing the API endpoint that returns gene/publication list as
    tab-separated *.csv file for a specific geneset/collection version.
    For all tests below, check that the contents of the *.csv file are what
    we expect.
    """

    def setUp(self):
        # This line is important to set up the test case!
        super(DownloadVersionAsCSVTestCase, self).setUp()

        # Need to specify username, otherwise will get error:
        # 'Invalid resource lookup data provided (mismatched type)'
        # when using a fixtureless username in the url (weird characters).
        self.user1 = factory.create(User, {'username': 'asdf'})

        self.org1 = factory.create(Organism)

        self.g1 = factory.create(Gene, {'systematic_name': get_random_string(5)})
        self.g2 = factory.create(Gene, {'systematic_name': get_random_string(5)})
        self.g3 = factory.create(Gene, {'systematic_name': get_random_string(5)})
        self.g4 = factory.create(Gene, {'systematic_name': get_random_string(5)})

        self.p1 = factory.create(Publication, {
            'pmid': get_random_string(7, allowed_chars=string.digits)})
        self.p2 = factory.create(Publication, {
            'pmid': get_random_string(7, allowed_chars=string.digits)})
        self.p3 = factory.create(Publication, {
            'pmid': get_random_string(7, allowed_chars=string.digits)})

        # Need to specify xrdb name. Otherwise, fixtureless might make the
        # name an empty string, which would raise an error.
        self.xrdb1 = factory.create(CrossRefDB, {'name': 'XRDB1'})
        self.xrdb2 = factory.create(CrossRefDB, {'name': 'XRDB2'})
        self.xrdb3 = factory.create(CrossRefDB, {'name': 'XRDB3'})

        self.xref1 = factory.create(CrossRef, {'crossrefdb': self.xrdb1,
                                               'gene': self.g1,
                                               'xrid': get_random_string(5)})
        self.xref1b = factory.create(CrossRef, {'crossrefdb': self.xrdb2,
                                                'gene': self.g1,
                                                'xrid': get_random_string(5)})
        self.xref2 = factory.create(CrossRef, {'crossrefdb': self.xrdb1,
                                               'gene': self.g2,
                                               'xrid': get_random_string(5)})
        self.xref2b = factory.create(CrossRef, {'crossrefdb': self.xrdb2,
                                                'gene': self.g2,
                                                'xrid': get_random_string(5)})
        self.xref3 = factory.create(CrossRef, {'crossrefdb': self.xrdb1,
                                               'gene': self.g3,
                                               'xrid': get_random_string(5)})
        self.xref3b = factory.create(CrossRef, {'crossrefdb': self.xrdb2,
                                                'gene': self.g3,
                                                'xrid': get_random_string(5)})
        self.xref4 = factory.create(CrossRef, {'crossrefdb': self.xrdb1,
                                               'gene': self.g4,
                                               'xrid': get_random_string(5)})
        self.xref4b = factory.create(CrossRef, {'crossrefdb': self.xrdb2,
                                                'gene': self.g4,
                                                'xrid': get_random_string(5)})

        self.geneset1 = Geneset.objects.create(
                            organism=self.org1, creator=self.user1,
                            title='Test RNA polymerase II geneset',
                            abstract='Sample abstract.', public=True)

        # This first version is the only one that is allowed to have
        # a parent version unspecified. *Note: also must fill in publications
        # as None, instead of just leaving a blank after the comma in tuple.
        self.version1 = Version.objects.create(
                            geneset=self.geneset1, creator=self.user1,
                            description='Sample description',
                            annotations=frozenset([
                                (self.g1.pk, self.p1.pk),
                                (self.g2.pk, None), (self.g3.pk, self.p2.pk),
                                (self.g3.pk, self.p3.pk), (self.g4.pk, None)]))

        self.client = TestApiClient()

        self.download_version_url = '/api/v1/version/' + self.user1.username + \
                                    '/' + self.geneset1.slug + '/' + \
                                    self.version1.ver_hash + '/download'

    def get_downloaded_annotations(self, request_params={}):
        """
        Utility function (used by most of the test functions below) to make the
        request to the TestApiClient for the downloadable file. Then check that
        the contents of this file are what we expect. If the length of the file
        equal to or less than 7 lines, this means that xrids were not found, so
        check that the list of annotations is blank. Else, return a dictionary
        of the annotations downloaded.
        """
        response = self.client.get(self.download_version_url, format="json",
                                   data=request_params)

        csv_response = response.content.replace("\r", "")
        response_lines = csv_response.split("\n")
        self.assertEqual(response_lines[0],
                         'Collection: ' + self.geneset1.title)
        self.assertEqual(response_lines[1],
                         'Version: ' + self.version1.ver_hash)
        self.assertEqual(response_lines[2],
                         'Author: ' + self.geneset1.creator.username)

        if request_params == {}:
            self.assertEqual(response_lines[3], 'Gene Identifier Type: Symbol')
        else:
            self.assertEqual(response_lines[3], 'Gene Identifier Type: ' +
                             request_params['xrid'])

        self.assertEqual(response_lines[5], 'Gene\tPubmed IDs')

        if len(response_lines) > 7:
            returned_annotations_dict = {}
            for line in response_lines[6:10]:
                toks = line.split("\t")
                if toks[1]:
                    pubs = toks[1].split(", ")
                    returned_annotations_dict[toks[0]] = set(pubs)
                else:
                    returned_annotations_dict[toks[0]] = set()

            return returned_annotations_dict

        else:
            self.assertEqual(response_lines[6], '')
            self.assertEqual(len(response_lines), 7)
            return response_lines

    def testNoXridSpecified(self):
        """
        If no xrid is specified, check that genes in the *.csv file are
        returned as symbols.
        """
        returned_annotations_dict = self.get_downloaded_annotations()

        saved_annotations_dict = {}
        for annotation in self.version1.annotations:
            gene_pk, pub_pk = annotation
            symbol = Gene.objects.get(pk=gene_pk).systematic_name

            if symbol not in saved_annotations_dict:
                saved_annotations_dict[symbol] = set()

            if pub_pk is not None:
                pmid = str(Publication.objects.get(pk=pub_pk).pmid)
                saved_annotations_dict[symbol].add(pmid)

        self.assertEqual(returned_annotations_dict, saved_annotations_dict)

    def testGetEntrezIds(self):
        """
        If the xrid specified is Entrez, check that genes in the *.csv file are
        returned as Entrez IDs.
        """
        request_params = {'xrid': 'Entrez'}

        returned_annotations_dict = self.get_downloaded_annotations(
            request_params)

        saved_annotations_dict = {}
        for annotation in self.version1.annotations:
            gene_pk, pub_pk = annotation
            entrezid = str(Gene.objects.get(pk=gene_pk).entrezid)

            if entrezid not in saved_annotations_dict:
                saved_annotations_dict[entrezid] = set()

            if pub_pk is not None:
                pmid = str(Publication.objects.get(pk=pub_pk).pmid)
                saved_annotations_dict[entrezid].add(pmid)

        self.assertEqual(returned_annotations_dict, saved_annotations_dict)

    def testGetSymbols(self):
        """
        If symbols are requested, check that genes in the *.csv file are
        returned as such.
        """
        request_params = {'xrid': 'Symbol'}

        returned_annotations_dict = self.get_downloaded_annotations(
            request_params)

        saved_annotations_dict = {}
        for annotation in self.version1.annotations:
            gene_pk, pub_pk = annotation
            symbol = Gene.objects.get(pk=gene_pk).systematic_name

            if symbol not in saved_annotations_dict:
                saved_annotations_dict[symbol] = set()

            if pub_pk is not None:
                pmid = str(Publication.objects.get(pk=pub_pk).pmid)
                saved_annotations_dict[symbol].add(pmid)

        self.assertEqual(returned_annotations_dict, saved_annotations_dict)

    def testGettingXrdb1(self):
        """
        Check that all genes in the *.csv file are returned with the type
        of xrid in xrdb1.
        """
        request_params = {'xrid': self.xrdb1.name}

        returned_annotations_dict = self.get_downloaded_annotations(
            request_params)

        saved_annotations_dict = {}
        for annotation in self.version1.annotations:
            gene_pk, pub_pk = annotation
            xrid = str(CrossRef.objects
                       .filter(crossrefdb__name=self.xrdb1.name)
                       .get(gene=gene_pk).xrid)

            if xrid not in saved_annotations_dict:
                saved_annotations_dict[xrid] = set()

            if pub_pk is not None:
                pmid = str(Publication.objects.get(pk=pub_pk).pmid)
                saved_annotations_dict[xrid].add(pmid)

        self.assertEqual(returned_annotations_dict, saved_annotations_dict)

    def testGettingXrdb2(self):
        """
        Check that all genes in the *.csv file are returned with the type
        of xrid in xrdb2.
        """
        request_params = {'xrid': self.xrdb2.name}

        returned_annotations_dict = self.get_downloaded_annotations(
            request_params)

        saved_annotations_dict = {}
        for annotation in self.version1.annotations:
            gene_pk, pub_pk = annotation
            xrid = str(CrossRef.objects
                       .filter(crossrefdb__name=self.xrdb2.name)
                       .get(gene=gene_pk).xrid)

            if xrid not in saved_annotations_dict:
                saved_annotations_dict[xrid] = set()

            if pub_pk is not None:
                pmid = str(Publication.objects.get(pk=pub_pk).pmid)
                saved_annotations_dict[xrid].add(pmid)

        self.assertEqual(returned_annotations_dict, saved_annotations_dict)

    def testGettingXrdb3(self):
        """
        Check that no genes are returned in the *.csv file if the user
        requests the xrdb3 type of identifier. This is because no cross-ref
        ids with the type of identifier in xrdb3 are available for the genes
        in this geneset. The checking of the contents of the file is done
        by the get_downloaded_annotations() method.
        """
        request_params = {'xrid': self.xrdb3.name}
        response_lines = self.get_downloaded_annotations(request_params)

    def testNonExistentXrdb(self):
        """
        Check that an error is returned if the user requests identifiers from
        an xrdb not loaded into our database.
        """
        parameters = {'xrid': 'qwerty'}
        response = self.client.get(self.download_version_url, format="json",
                                   data=parameters)

        self.assertHttpBadRequest(response)
        self.assertEqual(self.deserialize(response)['error'], 'The type of '
                         'gene identifier (xrid) you requested is not in our '
                         'database.')


class CreatingRemoteVersionTestCase(ResourceTestCase):

    def setUp(self):
        super(CreatingRemoteVersionTestCase, self).setUp() # This part is important

        self.org1 = Organism.objects.create(common_name="Mouse", scientific_name="Mus musculus", taxonomy_id=10090)

        self.username = "asdf"
        self.email = "asdf@example.com"
        self.password = "1234"
        self.user1 = User.objects.create_user(self.username, self.email, self.password)

        self.username2 = "hjkl"
        self.email2 = "hjkl@example.com"
        self.password2 = "1234"
        self.user2 = User.objects.create_user(self.username2, self.email2, self.password2)

        #Create some genes, crossrefdb's and crossrefs
        xrdb1 = CrossRefDB.objects.create(name="ASDF", url="http://www.example.com")
        xrdb2 = CrossRefDB.objects.create(name="XRDB2", url="http://www.example.com/2")

        g1 = Gene.objects.create(entrezid=55982, systematic_name="g1", standard_name="Paxip1", description="asdf", organism=self.org1, aliases="gee1 GEE1")
        g2 = Gene.objects.create(entrezid=18091, systematic_name="g2", standard_name="Nkx2-5", description="asdf", organism=self.org1, aliases="gee2 GEE2")
        g3 = Gene.objects.create(entrezid=67087, systematic_name="acdc", standard_name="Ctnnbip1", description="asdf", organism=self.org1, aliases="gee3 GEE3")
        g4 = Gene.objects.create(entrezid=22410, systematic_name="acdc", standard_name="Wnt10b", description="asdf", organism=self.org1, aliases="gee4 GEE4")

        xref1 = CrossRef.objects.create(crossrefdb = xrdb1, gene=g1, xrid="XRID1")
        xref2 = CrossRef.objects.create(crossrefdb = xrdb2, gene=g2, xrid="XRID1")
        xref3 = CrossRef.objects.create(crossrefdb = xrdb1, gene=g1, xrid="XRRID1")
        xref4 = CrossRef.objects.create(crossrefdb = xrdb1, gene=g2, xrid="XRID2")

        self.geneset1 = Geneset.objects.create(organism=self.org1, creator=self.user1,
        									   title='Test RNA polymerase II geneset',
        									   abstract='Sample abstract.',
        									   public=False)

        self.geneset2 = Geneset.objects.create(organism=self.org1, creator=self.user2,
                                               title='Test RNA polymerase II geneset',
                                               abstract='Sample abstract.',
                                               public=False)

        # Create some random publications
        load_pmids([17827783, 8112735, 2556444])


    def testVersionCreationNotLoggedIn(self):
        """
        Simple test to create a new version for a geneset without being logged in.
        Should return a 401 Unauthorized Error
        """
        client = TestApiClient()

        version_data = {}
        version_data['geneset'] = '/api/v1/geneset/' + str(self.geneset1.pk)
        version_data['description'] = 'Adding genes and publications.'
        version_data['annotations'] = {55982: [20671152], 18091: [8887666], 67087: [], 22410:[]}
        version_data['xrdb'] = 'Entrez'

        resp = client.post('/api/v1/version', format="json", data=version_data)
        self.assertHttpUnauthorized(resp)


    def testVersionCreationWrongLogin(self):
        """
        Simple test to create a new version for a geneset while being logged in
        under another user. This other user does have access to another identical
        geneset. Should return a 401 Unauthorized Error.
        """
        client = TestApiClient()
        client.client.login(username=self.username2, password=self.password2)

        version_data = {}
        # Try to use pk of *geneset1*, which they have no write-access to
        version_data['geneset'] = '/api/v1/geneset/' + str(self.geneset1.pk)
        version_data['description'] = 'Adding genes and publications.'
        version_data['annotations'] = {55982: [20671152], 18091: [8887666], 67087: [], 22410:[]}
        version_data['xrdb'] = 'Entrez'

        resp = client.post('/api/v1/version', format="json", data=version_data)
        self.assertHttpUnauthorized(resp)


    def testSimpleVersionCreationNoAnnots(self):
        """
        Simple test to create a new version with no annotations - 
        This should return a 400 Bad Request Error, stating that new
        versions must have annotations
        """
        client = TestApiClient()
        client.client.login(username=self.username, password=self.password)

        version_data = {}
        version_data['geneset'] = '/api/v1/geneset/' + str(self.geneset1.pk)
        version_data['description'] = 'New version, no annotations.'
        #version_data['annotations'] = {}
        version_data['xrdb'] = 'Entrez'

        resp = client.post('/api/v1/version', format="json", data=version_data)

        # Check for 400 Bad Request response, and that the error message is:
        # 'New versions must have annotations.'
        self.assertHttpBadRequest(resp)
        self.assertEqual(self.deserialize(resp)['error'], 'New versions must have annotations.')



    def testSimpleVersionCreationWithAnnots(self):
        """
        Simple test to create a new version for a geneset
        """
        client = TestApiClient()
        client.client.login(username=self.username, password=self.password)

        version_data = {}
        version_data['geneset'] = '/api/v1/geneset/' + str(self.geneset1.pk)
        version_data['description'] = 'Adding genes and publications.'
        version_data['annotations'] = {55982: [20671152], 18091: [8887666], 67087: [], 22410:[]}
        version_data['xrdb'] = 'Entrez'

        resp = client.post('/api/v1/version', format="json", data=version_data)
        self.assertHttpCreated(resp)
        gsresp = client.get('/api/v1/geneset', format="json", data={'show_tip': 'true', 'full_annotations': 'true'})
        self.assertValidJSONResponse(gsresp)

        simplified_annotations = {}
        for annotation in self.deserialize(gsresp)['objects'][0]['tip']['annotations']:
            entrezid = annotation['gene']['entrezid']
            simplified_annotations[entrezid] = [pub['pmid'] for pub in annotation['pubs']]

        self.assertEqual(simplified_annotations, version_data['annotations'])


    def testCheckGenesetVersionURI(self):
        """
        Simple test to check the correct assignment of GenesetVersion
        resource_uri
        """
        client = TestApiClient()
        client.client.login(username=self.username, password=self.password)

        version_data = {}
        version_data['geneset'] = '/api/v1/geneset/' + str(self.geneset1.pk)
        version_data['description'] = 'Adding genes and publications.'
        version_data['annotations'] = {55982: [20671152], 18091: [8887666], 67087: [], 22410:[]}
        version_data['xrdb'] = 'Entrez'

        resp = client.post('/api/v1/version', format="json", data=version_data)
        self.assertHttpCreated(resp)
        gsresp = client.get('/api/v1/geneset', format="json", data={'show_tip': 'true', 'full_annotations': 'true'})
        self.assertValidJSONResponse(gsresp)

        vers_resp = client.get('/api/v1/version', format="json")
        self.assertValidJSONResponse(vers_resp)

        self.assertEqual(self.deserialize(gsresp)['objects'][0]['tip']['resource_uri'], self.deserialize(vers_resp)['objects'][0]['resource_uri'])



    def testCreateSecondVersionWithParent(self):
        """
        Test to create another version for a geneset, after a first one
        has been created. User *must* specify the version parent.
        """

        client = TestApiClient()
        client.client.login(username=self.username, password=self.password)

        # Create one version
        version_data = {}
        version_data['geneset'] = '/api/v1/geneset/' + str(self.geneset1.pk)
        version_data['description'] = 'Adding genes and publications.'
        version_data['annotations'] = {55982: [20671152], 18091: [8887666]}
        version_data['xrdb'] = 'Entrez'

        resp = client.post('/api/v1/version', format="json", data=version_data)
        self.assertHttpCreated(resp)

        # Get tip version of the geneset (which will be parent version)
        gsresp = client.get('/api/v1/geneset', format="json", data={'show_tip': 'true'})
        self.assertValidJSONResponse(gsresp)
        parent_version = self.deserialize(gsresp)['objects'][0]['tip']['resource_uri']

        #Create another version
        other_version_data = {}
        other_version_data['geneset'] = '/api/v1/geneset/' + str(self.geneset1.pk)
        other_version_data['description'] = 'Adding genes and publications.'
        other_version_data['annotations'] = {55982: [20671152], 18091: [8887666], 67087: [], 22410:[]}
        other_version_data['xrdb'] = 'Entrez'
        other_version_data['parent'] = parent_version

        resp = client.post('/api/v1/version', format="json", data=other_version_data)
        self.assertHttpCreated(resp)

        gsresp = client.get('/api/v1/geneset', format="json", data={'show_tip': 'true', 'full_annotations': 'true'})
        self.assertValidJSONResponse(gsresp)

        # Check that the annotations of the tip are actually the ones of the second version
        simplified_annotations = {}
        for annotation in self.deserialize(gsresp)['objects'][0]['tip']['annotations']:
            entrezid = annotation['gene']['entrezid']
            simplified_annotations[entrezid] = [pub['pmid'] for pub in annotation['pubs']]
        self.assertEqual(simplified_annotations, other_version_data['annotations'])

        # Check that the first version got correctly assigned as parent version:
        self.assertEqual(self.deserialize(gsresp)['objects'][0]['tip']['parent'], other_version_data['parent'])


    def testCreateSecondVersionRemoveOneAnnotation(self):
        """
        Very similar to previous test, but check that user can also remove
        an annotation in the new version aside from adding new annotations.
        """

        client = TestApiClient()
        client.client.login(username=self.username, password=self.password)

        # Create one version
        version_data = {}
        version_data['geneset'] = '/api/v1/geneset/' + str(self.geneset1.pk)
        version_data['description'] = 'Adding genes and publications.'
        version_data['annotations'] = {55982: [20671152], 18091: [8887666]}
        version_data['xrdb'] = 'Entrez'

        resp = client.post('/api/v1/version', format="json", data=version_data)
        self.assertHttpCreated(resp)

        # Get tip version of the geneset (which will be parent version)
        gsresp = client.get('/api/v1/geneset', format="json", data={'show_tip': 'true'})
        self.assertValidJSONResponse(gsresp)
        parent_version = self.deserialize(gsresp)['objects'][0]['tip']['resource_uri']

        #Create another version
        other_version_data = {}
        other_version_data['geneset'] = '/api/v1/geneset/' + str(self.geneset1.pk)
        other_version_data['description'] = 'Adding genes and publications.'

        # Add 2 new annotations and remove one of the old annotations
        other_version_data['annotations'] = {18091: [8887666], 67087: [], 22410:[]}
        other_version_data['xrdb'] = 'Entrez'
        other_version_data['parent'] = parent_version

        resp = client.post('/api/v1/version', format="json", data=other_version_data)
        self.assertHttpCreated(resp)

        gsresp = client.get('/api/v1/geneset', format="json", data={'show_tip': 'true', 'full_annotations': 'true'})
        self.assertValidJSONResponse(gsresp)

        # Check that the annotations of the tip are actually the ones of the second version
        simplified_annotations = {}
        for annotation in self.deserialize(gsresp)['objects'][0]['tip']['annotations']:
            entrezid = annotation['gene']['entrezid']
            simplified_annotations[entrezid] = [pub['pmid'] for pub in annotation['pubs']]
        self.assertEqual(simplified_annotations, other_version_data['annotations'])

        # Check that the first version got correctly assigned as parent version:
        self.assertEqual(self.deserialize(gsresp)['objects'][0]['tip']['parent'], other_version_data['parent'])


    def testCreateSecondVersionFail(self):
        """
        Test to create another version for a geneset, but without specifying
        a parent version. This should fail gracefully (i.e. return a 400 Bad
        Request with an interpretable error message).
        """

        client = TestApiClient()
        client.client.login(username=self.username, password=self.password)

        # Create one version
        version_data = {}
        version_data['geneset'] = '/api/v1/geneset/' + str(self.geneset1.pk)
        version_data['description'] = 'Adding genes and publications.'
        version_data['annotations'] = {55982: [20671152], 18091: [8887666]}
        version_data['xrdb'] = 'Entrez'

        resp = client.post('/api/v1/version', format="json", data=version_data)
        self.assertHttpCreated(resp)

        # Get tip version of the geneset (which will be parent version)
        gsresp = client.get('/api/v1/geneset', format="json", data={'show_tip': 'true'})
        self.assertValidJSONResponse(gsresp)
        parent_version = self.deserialize(gsresp)['objects'][0]['tip']['resource_uri']

        #Create another version, but do not specify a parent version!
        other_version_data = {}
        other_version_data['geneset'] = '/api/v1/geneset/' + str(self.geneset1.pk)
        other_version_data['description'] = 'Adding genes and publications.'
        other_version_data['annotations'] = {55982: [20671152], 18091: [8887666], 67087: [], 22410:[]}
        other_version_data['xrdb'] = 'Entrez'

        resp = client.post('/api/v1/version', format="json", data=other_version_data)

        # Check for 400 Bad Request response, and that the error message states
        # that a parent version must be specified
        self.assertHttpBadRequest(resp)
        self.assertEqual(self.deserialize(resp)['error'], "This geneset already" + \
            " has at least one version. You must specify the parent version of this new version.")


    def testVersionCreationWithFullPubObjs(self):
        """
        Test to create a version with full database publication objects, as the
        tribe web-interface does.
        """
        client = TestApiClient()
        client.client.login(username=self.username, password=self.password)

        version_data = {}
        version_data['geneset'] = '/api/v1/geneset/' + str(self.geneset1.pk)
        version_data['description'] = 'Adding genes and publications.'

        gsresp = client.get('/api/v1/publication', format="json")
        pub_objs = self.deserialize(gsresp)['objects']

        version_data['annotations'] = {55982: [pub_objs[0]], 18091: [pub_objs[1]], 67087: [pub_objs[2]], 22410:[]}
        version_data['xrdb'] = 'Entrez'
        version_data['full_pubs'] = True # The web-interface app adds this part as well

        resp = client.post('/api/v1/version', format="json", data=version_data)
        self.assertHttpCreated(resp)
        gsresp = client.get('/api/v1/geneset', format="json", data={'show_tip': 'true', 'full_annotations': 'true'})
        self.assertValidJSONResponse(gsresp)

        # We must simplify annotations - they are not the same because received_annotations
        # do not include publication resource_uris
        simplified_received_annotations = {}
        for annotation in self.deserialize(gsresp)['objects'][0]['tip']['annotations']:
            entrezid = annotation['gene']['entrezid']
            simplified_received_annotations[entrezid] = [pub['pmid'] for pub in annotation['pubs']]

        simplified_sent_annotations = {}
        for annotation in version_data['annotations']:
            simplified_sent_annotations[annotation] = [pub['pmid'] for pub in version_data['annotations'][annotation]]

        self.assertEqual(simplified_received_annotations, simplified_sent_annotations)


    def tearDown(self):
        User.objects.all().delete()
        Organism.objects.all().delete()
        Geneset.objects.all().delete()
        Version.objects.all().delete()
        Publication.objects.all().delete()


class ForkingVersionTestCase(ResourceTestCase):

    def setUp(self):
        # This line is important to set up the test case!
        super(ForkingVersionTestCase, self).setUp()

        org1 = Organism.objects.create(common_name="Mouse",
                                       scientific_name="Mus musculus",
                                       taxonomy_id=10090)

        self.username = "asdf"
        self.email = "asdf@example.com"
        self.password = "1234"
        self.user1 = User.objects.create_user(self.username, self.email,
                                              self.password)

        self.g1 = factory.create(Gene)
        self.g2 = factory.create(Gene)
        self.g3 = factory.create(Gene)
        self.g4 = factory.create(Gene)

        self.geneset1 = Geneset.objects.create(
                            organism=org1, creator=self.user1,
                            title='Test RNA polymerase II geneset',
                            abstract='Sample abstract.', public=False)

        # This first version is the only one that is allowed to have
        # a parent version unspecified
        self.version1 = Version.objects.create(
                            geneset=self.geneset1, creator=self.user1,
                            description='asdf',
                            annotations=frozenset([(self.g1.pk, 17827783),
                                (self.g1.pk, 8112735), (self.g2.pk,)]))

        self.version2 = Version.objects.create(
                            geneset=self.geneset1, creator=self.user1,
                            description='asdf', parent=self.version1,
                            annotations=frozenset([(self.g1.pk, 8112735),
                                (self.g2.pk,)]))
        self.version3 = Version.objects.create(
                            geneset=self.geneset1, creator=self.user1,
                            description='asdf', parent=self.version2,
                            annotations=frozenset([(self.g1.pk, 8112735),
                                (self.g2.pk,), (self.g3.pk,)]))
        self.version4 = Version.objects.create(
                            geneset=self.geneset1, creator=self.user1,
                            description='asdf', parent=self.version3,
                            annotations=frozenset([(self.g1.pk, 8112735),
                                (self.g2.pk,), (self.g3.pk, 2556444)]))
        self.version5 = Version.objects.create(
                            geneset=self.geneset1, creator=self.user1,
                            description='asdf', parent=self.version4,
                            annotations=frozenset([(self.g1.pk, 8112735),
                                (self.g2.pk,), (self.g3.pk, 2556444),
                                (self.g4.pk,)]))



    def testForkingGenesetAndVersions(self):
        """
        Tests that forking works normally and that it copies all versions &
        parent versions recursively.
        """

        client = TestApiClient()
        client.client.login(username=self.username, password=self.password)

        gsresp = client.get('/api/v1/geneset', format="json",
                            data={'show_tip': 'true'})
        self.assertValidJSONResponse(gsresp)

        original_geneset = self.deserialize(gsresp)['objects'][0]
        original_version = self.deserialize(gsresp)['objects'][0]['tip']

        # Create data for geneset/version fork
        forked_geneset = {}
        forked_geneset['title'] = 'Fork of' + original_geneset['title']
        forked_geneset['organism'] = original_geneset['organism']['resource_uri']
        forked_geneset['abstr'] = original_geneset['abstract']
        forked_geneset['public'] = False
        forked_geneset['fork_of'] = original_geneset['resource_uri']
        forked_geneset['fork_version'] = original_version['ver_hash']

        resp = client.post('/api/v1/geneset', format="json", data=forked_geneset)
        self.assertHttpCreated(resp)

        # These are the actual database geneset objects
        original_gs = Geneset.objects.get(title = original_geneset['title'])
        forked_gs = Geneset.objects.get(title = forked_geneset['title'])

        # This next part will make sets of the version hashes for all versions
        # in each of the genesets and make sure that they are identical (i.e.
        # all versions got copied).
        original_version_set = set()
        forked_version_set = set()

        for version in Version.objects.filter(geneset = original_gs):
            original_version_set.add(version.ver_hash)

        for version in Version.objects.filter(geneset = forked_gs):
            forked_version_set.add(version.ver_hash)

        self.assertEqual(original_version_set, forked_version_set)


    def tearDown(self):
        User.objects.all().delete()
        Organism.objects.all().delete()
        Geneset.objects.all().delete()
        Version.objects.all().delete()
        Publication.objects.all().delete()