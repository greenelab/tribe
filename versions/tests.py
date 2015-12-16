"""
Version tests
"""
from django.test import TestCase
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