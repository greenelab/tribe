"""
Geneset tests
"""
from datetime import datetime
import random
import string
import mock

from django.test import TestCase
from django.test.utils import override_settings
from django.core.management import call_command
from django.contrib.auth.models import User
from django.conf import settings
from django.utils import timezone

from fixtureless import Factory

from tastypie.test import (
    ResourceTestCase, ResourceTestCaseMixin, TestApiClient)
import haystack

from organisms.models import Organism
from genes.models import Gene, CrossRef, CrossRefDB
from genesets.models import Geneset
from versions.models import Version
from versions.exceptions import (
    VersionContainsNoneGene, NoParentVersionSpecified
)

factory = Factory()

# REQUIRES ELASTICSEARCH TO BE SETUP AS THE HAYSTACK PROVIDER.
TEST_INDEX = {
    'default': {
        'ENGINE': 'haystack.backends.elasticsearch_backend.'
                  'ElasticsearchSearchEngine',
        'URL': 'http://127.0.0.1:9200/',
        'TIMEOUT': 60 * 10,
        'INDEX_NAME': 'test_index',
    },
}


def ver_hash_generator():
    return ''.join(random.choice(string.ascii_lowercase + string.digits)
                   for i in range(40))


class GenesetTipTestCase(TestCase):

    def setUp(self):
        org1 = factory.create(Organism)
        user1 = factory.create(User)
        geneset1 = Geneset.objects.create(
            creator=user1, title='TestGeneset1', organism=org1, abstract='Testing genes.', public=False)
        geneset2 = Geneset.objects.create(
            creator=user1, title='TestGeneset2', organism=org1, abstract='Testing no versions.', public=False)

        # Try all combinations I can think of with genes and publications
        gene_frozenset1 = frozenset([(5860, 1)])
        gene_frozenset2 = frozenset(
            [(5860, 1), (11672, 2), (11672, 3), (7489, None), (5576, None), (5576, 3), (5576, 3), (5576, 4)])
        version1 = Version.objects.create(
            geneset=geneset1, creator=user1, description="First version.", annotations=gene_frozenset1)
        version2 = Version.objects.create(
            geneset=geneset1, creator=user1, description="Tip version.", 
            annotations=gene_frozenset2, parent=version1)

    def testGetTip(self):
        """
        Tests the Geneset model's get_tip method. This should return 'version2' (not 'version1'),
        which was created above
        """
        geneset1 = Geneset.objects.get(title='TestGeneset1')
        tip_version = geneset1.get_tip()
        self.assertEqual(tip_version.description, "Tip version.")

    def testGetTipIsNone(self):
        """
        Tests that the Geneset model's get_tip method returns None for geneset2 created above (which has no versions).
        """
        geneset2 = Geneset.objects.get(title='TestGeneset2')
        tip_version = geneset2.get_tip()
        self.assertEqual(tip_version, None)

    def testTipItemCount(self):
        """
        For the geneset1 object, the tip_item_count attribute should return 4 - the total number of different
        genes (regardless of publications associated with them) present in the tip version (version1).
        """
        geneset1 = Geneset.objects.get(title='TestGeneset1')
        self.assertEqual(geneset1.tip_item_count, 4)


    def testNoParentVersionSpecified(self):
        """
        Testing that the Version save() method correctly raises a
        'NoParentVersionSpecified' exception if the user tries to create
        a version of a geneset that already has versions, but without
        specifying a parent version.
        """

        geneset1 = Geneset.objects.get(title='TestGeneset1')
        none_gene_frozenset = frozenset([(5576, 2), (5860, 1)])

        # This is the correct way to test for exceptions. See:
        # https://docs.djangoproject.com/en/dev/topics/testing/tools/#exceptions
        with self.assertRaises(NoParentVersionSpecified):
            Version.objects.create(geneset=geneset1, creator=geneset1.creator,
                                   description="Testing None gene.", 
                                   annotations=none_gene_frozenset)


    def testNoneGenes(self):
        """
        Testing that the Version save() method correctly returns a
        'VersionContainsNoneGene' exception when trying to pass 'None'
        instead of a gene ID.
        """
        # Try to save 'None' as a gene in a version.
        geneset1 = Geneset.objects.get(title='TestGeneset1')
        none_gene_frozenset = frozenset([(None, 1), (None, 2), (5860, 1)])

        with self.assertRaises(VersionContainsNoneGene):
            Version.objects.create(geneset=geneset1, creator=geneset1.creator,
                                   description="Testing None gene.", 
                                   annotations=none_gene_frozenset,
                                   parent=geneset1.get_tip())


    def testNoneGenesPublications(self):
        """
        Testing that the Version save() method correctly returns a
        'VersionContainsNoneGene' exception when passing both
        'None' for both a gene and a publication.
        """
        # Try to save 'None' as both gene AND publication:
        geneset1 = Geneset.objects.get(title='TestGeneset1')
        none_gene_publication = frozenset([(None, None)])

        with self.assertRaises(VersionContainsNoneGene):
            Version.objects.create(geneset=geneset1, creator=geneset1.creator,
                                   description="Testing None gene AND publication.",
                                   annotations=none_gene_publication,
                                   parent=geneset1.get_tip())



class TestKEGGLoaderMethods(TestCase):
    KEGG_URL_BASE = 'http://rest.kegg.jp'

    def test_version_loads_something(self):
        """
        Test that get_kegg_version at least gets a string starting with Release.
        """
        from genesets.management.commands import genesets_load_kegg
        version = genesets_load_kegg.get_kegg_version(self.KEGG_URL_BASE)
        self.assertIsNotNone(version)
        self.assertTrue(version.startswith('Release'))

    def test_pathway_gene_loads_hsa00010_gene_10327(self):
        """
        Test that get_kegg_members creates a dictionary where the key hsa00010 contains 10327.
        This is the first line from link/hsa/pathway.
        """
        from genesets.management.commands import genesets_load_kegg
        result = genesets_load_kegg.get_kegg_members(
            self.KEGG_URL_BASE, 'hsa', 'Pathway')
        self.assertTrue('hsa00010' in result)
        self.assertTrue('10327' in result['hsa00010'])

    def test_pathway_info_loads_hsa00010(self):
        """
        Test that get_kegg_info creates a dictionary with the title, abstract, etc..
        """
        from genesets.management.commands import genesets_load_kegg
        result = genesets_load_kegg.get_kegg_info(
            self.KEGG_URL_BASE, 'hsa00010')
        self.assertTrue('title' in result)
        self.assertEqual(
            result['title'], 'Glycolysis / Gluconeogenesis - Homo sapiens (human)')
        self.assertTrue('abstract' in result)

    def test_info_loads_no_description(self):
        """
        Test that get_kegg_info works when there is no description. This occurs sometimes
        (e.g. http://rest.kegg.jp/get/hsa03010). The returned abstract should be empty in this case.
        """
        from genesets.management.commands import genesets_load_kegg
        result = genesets_load_kegg.get_kegg_info(
            self.KEGG_URL_BASE, 'hsa03010')
        self.assertTrue('title' in result)
        self.assertEqual(result['title'], 'Ribosome - Homo sapiens (human)')
        self.assertTrue('abstract' in result)
        self.assertEqual(result['abstract'], '')

    def test_module_info_loads_M00001(self):
        """
        Test that get_kegg_info creates a dictionary with the title, abstract, etc..
        """
        from genesets.management.commands import genesets_load_kegg
        result = genesets_load_kegg.get_kegg_info(self.KEGG_URL_BASE, 'M00001')
        self.assertTrue('title' in result)
        self.assertEqual(
            result['title'], 'Glycolysis (Embden-Meyerhof pathway), glucose => pyruvate')
        self.assertTrue('abstract' in result)

    def test_disease_info_loads_M00001(self):
        """
        Test that get_kegg_info creates a dictionary with the title, abstract, etc..
        """
        from genesets.management.commands import genesets_load_kegg
        result = genesets_load_kegg.get_kegg_info(self.KEGG_URL_BASE, 'H00001')
        self.assertTrue('title' in result)

        # Note: The name of this KEGG term has changed:
        # http://www.genome.jp/dbget-bin/www_bget?ds:H00001
        self.assertEqual(
            result['title'], 'B lymphoblastic leukemia/lymphoma')

        self.assertTrue('abstract' in result)


# The Celery settings are needed for updating the Geneset search indexes
# with Celery in tests. These should be included in every TestCase class
# where Celery is run.
@override_settings(HAYSTACK_CONNECTIONS=TEST_INDEX, CELERY_ALWAYS_EAGER=True,
                   CELERY_EAGER_PROPAGATES_EXCEPTIONS=True)
class GenesetUnregisteredTestCase(ResourceTestCase):

    def setUp(self):
        haystack.connections.reload('default')
        super(GenesetUnregisteredTestCase, self).setUp()
        self.org1 = factory.create(Organism)
        self.user1 = factory.create(User)
        self.user2 = factory.create(User)
        self.geneset1 = Geneset.objects.create(creator=self.user1, title='Test Geneset 1',
                                               organism=self.org1, deleted=False,
                                               abstract='Testing for BRCA AURKB.', public=False)
        self.geneset2 = Geneset.objects.create(creator=self.user2, title='GO-BP:Test Geneset 2',
                                               organism=self.org1, deleted=False,
                                               abstract='Testing BRCA AURKA.', public=False)
        self.geneset3 = Geneset.objects.create(creator=self.user2, title='GO-BP:Test Geneset 3',
                                               organism=self.org1, deleted=False,
                                               abstract='Testing BRCA AURKA.', public=True)

        # This will update the search indexes for the genesets that were just
        # created, but new genesets will need to have their search indexes
        # created through the Celery queue.
        call_command('update_index', interactive=False, verbosity=0)

    def testEmptyQuery(self):
        """
        Test public genesets w/o search.

        Tests that an empty query from a non-registered user returns only public results.
        """
        resp = self.api_client.get('/api/v1/geneset', format="json")
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)['objects']), 1)
        self.assertEqual(self.deserialize(resp)['objects'][0]['title'], "GO-BP:Test Geneset 3")

    def testGOBPQuery(self):
        """
        Tests string query.

        Uses "GO-BP:" as a query. Should return the public object.
        """
        resp = self.api_client.get('/api/v1/geneset', format="json", data={'query': 'GO-BP'})
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)['objects']), 1)
        titles = set([x['title'] for x in self.deserialize(resp)['objects']])
        exp_set = set(["GO-BP:Test Geneset 3", ])
        self.assertEqual(titles, exp_set)

    def testAbstractQuery(self):
        """
        Tests query for item in abstract.

        Uses "AURKB" as a query. Should return nothing.
        """
        resp = self.api_client.get('/api/v1/geneset', format="json", data={'query': 'AURKB'})
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)['objects']), 0)

    def testSearchIndexUpdate(self):
        """
        Tests that search indexes get updated when a new object is created.

        Creating a new Gene Ontology Biological Process term, and making
        it public. This term should get returned when using "GO-BP" as a
        query.
        """

        self.geneset4 = Geneset.objects.create(
            creator=self.user2, title='GO-BP:Test Geneset 4', deleted=False,
            organism=self.org1, abstract='Testing index.', public=True
        )

        resp = self.api_client.get('/api/v1/geneset',
                                   format="json",
                                   data={'query': 'GO-BP'})
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)['objects']), 2)

        titles = set([x['title'] for x in self.deserialize(resp)['objects']])
        exp_set = set(["GO-BP:Test Geneset 3", "GO-BP:Test Geneset 4"])
        self.assertEqual(titles, exp_set)

    def tearDown(self):
        User.objects.all().delete()
        Organism.objects.all().delete()
        Geneset.objects.all().delete()
        call_command('clear_index', interactive=False, verbosity=0)


# The Celery settings are needed for updating the Geneset search indexes
# with Celery in tests. These should be included in every TestCase class
# where Celery is run.
@override_settings(HAYSTACK_CONNECTIONS=TEST_INDEX, CELERY_ALWAYS_EAGER=True,
                   CELERY_EAGER_PROPAGATES_EXCEPTIONS=True)
class GenesetRegisteredTestCase(ResourceTestCase):

    def setUp(self):
        haystack.connections.reload('default')
        super(GenesetRegisteredTestCase, self).setUp()
        self.org1 = factory.create(Organism)
        self.username = "asdf"
        self.email = "asdf@example.com"
        self.password = "qwerty"
        self.user1 = User.objects.create_user(self.username, self.email, self.password)

        # log in user 1
        self.api_client.client.login(username=self.username, password=self.password)

        # create other objects.
        self.user2 = factory.create(User)
        self.geneset1 = Geneset.objects.create(creator=self.user1, title='Test Geneset 1',
                                               organism=self.org1, deleted=False,
                                               abstract='Testing for BRCA AURKB.', public=False)
        self.geneset2 = Geneset.objects.create(creator=self.user2, title='GO-BP:Test Geneset 2',
                                               organism=self.org1, deleted=False,
                                               abstract='Testing BRCA AURKA.', public=False)
        self.geneset3 = Geneset.objects.create(creator=self.user2, title='GO-BP:Test Geneset 3',
                                               organism=self.org1, deleted=False,
                                               abstract='Testing BRCA AURKA.', public=True)

        # Make Tags For Testing
        self.geneset1.tags.add("asdf")
        self.geneset2.tags.add("asdf")
        self.geneset1.tags.add("qwerty")
        self.geneset3.tags.add("qwerty")

        # This will update the search indexes for the genesets that were just
        # created, but new genesets will need to have their search indexes
        # created through the Celery queue.
        call_command('update_index', interactive=False, verbosity=0)

    def testEmptyQuery(self):
        """
        Test private genesets w/o search.

        Tests that an empty query from a registered user returns public and private results.
        """
        resp = self.api_client.get('/api/v1/geneset', format="json")
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)['objects']), 2)
        titles = set([x['title'] for x in self.deserialize(resp)['objects']])
        exp_set = set([self.geneset1.title, self.geneset3.title])
        self.assertEqual(titles, exp_set)

    def testGOBPQuery(self):
        """
        Test string query.

        Uses "GO-BP:" as a query. Should return the public object.
        """
        resp = self.api_client.get('/api/v1/geneset', format="json", data={'query': 'GO-BP'})
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)['objects']), 1)
        titles = set([x['title'] for x in self.deserialize(resp)['objects']])
        exp_set = set([self.geneset3.title, ])
        self.assertEqual(titles, exp_set)

    def testAbstractQuery(self):
        """
        Test query for item in abstract.

        Uses "AURKB" as a query. Should return the private object that has AURKB in the abstract.
        """
        resp = self.api_client.get('/api/v1/geneset', format="json", data={'query': 'AURKB'})
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)['objects']), 1)
        titles = set([x['title'] for x in self.deserialize(resp)['objects']])
        exp_set = set([self.geneset1.title, ])
        self.assertEqual(titles, exp_set)

    def testTagWithoutSearchRestricted(self):
        """
        Test tag filtering; no search; no matching public result.

        Uses "asdf" to check that only geneset1 is returned.
        """
        resp = self.api_client.get('/api/v1/geneset', format="json", data={'filter_tags': 'asdf'})
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)['objects']), 1)
        titles = set([x['title'] for x in self.deserialize(resp)['objects']])
        exp_set = set([self.geneset1.title, ])
        self.assertEqual(titles, exp_set)

    def testTagWithoutSearchRestrictedPublic(self):
        """
        Test tag filtering; no search; also matching public result.

        Uses "qwerty" to check that genesets 1 and 3 are returned.
        """
        resp = self.api_client.get('/api/v1/geneset', format="json", data={'filter_tags': 'qwerty'})
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)['objects']), 2)
        titles = set([x['title'] for x in self.deserialize(resp)['objects']])
        exp_set = set([self.geneset1.title, self.geneset3.title])
        self.assertEqual(titles, exp_set)

    def testTagWithSearchRestricted(self):
        """
        Test tag filtering; search matching all genesets; no matching public result.

        Uses "asdf" to check that only geneset1 is returned.
        """
        resp = self.api_client.get('/api/v1/geneset', format="json", data={'query': 'BRCA', 'filter_tags': 'asdf'})
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)['objects']), 1)
        titles = set([x['title'] for x in self.deserialize(resp)['objects']])
        exp_set = set([self.geneset1.title, ])
        self.assertEqual(titles, exp_set)

    def testTagWithSearchRestrictedPublic(self):
        """
        Test tag filtering; search matching all genesets; also matching public result.

        Uses "qwerty" to check that genesets 1 and 3 are returned.
        """
        resp = self.api_client.get('/api/v1/geneset', format="json", data={'query': 'BRCA', 'filter_tags': 'qwerty'})
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)['objects']), 2)
        titles = set([x['title'] for x in self.deserialize(resp)['objects']])
        exp_set = set([self.geneset1.title, self.geneset3.title])
        self.assertEqual(titles, exp_set)

    def testSearchIndexUpdate(self):
        """
        Tests that search indexes get updated when a new object is created.

        Creating a new Gene Ontology Biological Process term, making
        it private, and checking that user1 (who is logged in), can
        access it. This term should get returned when using "GO-BP" as a
        query.
        """

        self.geneset4 = Geneset.objects.create(
            creator=self.user1, title='GO-BP:Test Geneset 4', deleted=False,
            organism=self.org1, abstract='Testing index.', public=False
        )

        resp = self.api_client.get('/api/v1/geneset',
                                   format="json",
                                   data={'query': 'GO-BP'})
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)['objects']), 2)

        titles = set([x['title'] for x in self.deserialize(resp)['objects']])
        exp_set = set(["GO-BP:Test Geneset 3", "GO-BP:Test Geneset 4"])
        self.assertEqual(titles, exp_set)

    def tearDown(self):
        User.objects.all().delete()
        Organism.objects.all().delete()
        Geneset.objects.all().delete()
        call_command('clear_index', interactive=False, verbosity=0)


class CreatingRemoteGenesetTestCase(ResourceTestCase):

    def setUp(self):
        # This following 'super' call is important to initialize TestCase
        super(CreatingRemoteGenesetTestCase, self).setUp()

        self.org1 = Organism.objects.create(common_name="Mouse",
                                            scientific_name="Mus musculus",
                                            taxonomy_id=10090,
                                            slug="mus-musculus")
        self.org2 = Organism.objects.create(common_name="Human",
                                            scientific_name="Homo sapiens",
                                            taxonomy_id=9606,
                                            slug="homo-sapiens")
        self.org3 = Organism.objects.create(common_name="Yeast",
                                            scientific_name="Saccharomyces "
                                                            "cerevisiae",
                                            taxonomy_id=4932,
                                            slug="saccharomyces-cerevisiae")

        self.username = "hjkl"
        self.email = "hjkl@example.com"
        self.password = "1234"
        self.user1 = User.objects.create_user(
            self.username, self.email, self.password)

        # Create some genes, crossrefdb's and crossrefs
        xrdb1 = CrossRefDB.objects.create(name="ASDF",
                                          url="http://www.example.com")
        xrdb2 = CrossRefDB.objects.create(name="XRDB2",
                                          url="http://www.example.com/2")

        self.g1 = Gene.objects.create(entrezid=55982, systematic_name="g1",
                                      standard_name="Paxip1",
                                      description="asdf",
                                      organism=self.org1, aliases="gee1 GEE1")
        self.g2 = Gene.objects.create(entrezid=18091, systematic_name="g2",
                                      standard_name="Nkx2-5",
                                      description="asdf",
                                      organism=self.org1, aliases="gee2 GEE2")
        self.g3 = Gene.objects.create(entrezid=67087, systematic_name="acdc",
                                      standard_name="Ctnnbip1",
                                      description="asdf",
                                      organism=self.org1, aliases="gee3 GEE3")
        self.g4 = Gene.objects.create(entrezid=22410, systematic_name="acdc",
                                      standard_name="Wnt10b",
                                      description="asdf",
                                      organism=self.org1, aliases="gee4 GEE4")
        self.g5 = Gene.objects.create(entrezid=3388, systematic_name="ICR1",
                                      standard_name="ICR1",
                                      organism=self.org2)
        self.g6 = Gene.objects.create(entrezid=9164906, systematic_name="ICR1",
                                      standard_name="ICR1",
                                      organism=self.org3)
        self.gene_entrezid_set = set([55982, 18091, 67087, 22410])

        CrossRef.objects.create(crossrefdb=xrdb1, gene=self.g1, xrid="XRID1")
        CrossRef.objects.create(crossrefdb=xrdb2, gene=self.g2, xrid="XRID1")
        CrossRef.objects.create(crossrefdb=xrdb1, gene=self.g1, xrid="XRRID1")
        CrossRef.objects.create(crossrefdb=xrdb1, gene=self.g2, xrid="XRID2")

    def testSimpleGenesetCreationNoGenes(self):
        """
        Simple test to create a new geneset with some genes, using an organism queried in the API
        """
        client = TestApiClient()
        client.client.login(username=self.username, password=self.password)

        # Get the organism uri just as the user would, doing a query to the API
        org_scientific_name = self.org1.scientific_name
        org_resp = self.api_client.get('/api/v1/organism', format="json", data={'scientific_name': org_scientific_name})
        org_object = self.deserialize(org_resp)['objects'][0]
        org_uri = org_object['resource_uri']

        geneset_data = {}
        geneset_data['organism'] = org_uri
        geneset_data['title'] = 'Sample RNA polymerase II geneset - created remotely'
        geneset_data['abstract'] = 'Any process that modulates the rate, frequency or extent of a process involved in starting transcription from an RNA polymerase II promoter.'
        geneset_data['public'] = True

        resp = client.post('/api/v1/geneset', format="json", data=geneset_data)
        self.assertHttpCreated(resp)

    def testGenesetCreationWithGenePKs(self):
        """
        Test to create a new geneset, with passed genes AND publications
        """
        client = TestApiClient()
        client.client.login(username=self.username, password=self.password)

        # Get the organism uri just as the user would, doing a query to the API
        org_scientific_name = self.org1.scientific_name
        org_resp = self.api_client.get('/api/v1/organism', format="json", data={'scientific_name': org_scientific_name})
        org_object = self.deserialize(org_resp)['objects'][0]
        org_uri = org_object['resource_uri']

        geneset_data = {}
        geneset_data['organism'] = org_uri
        geneset_data['title'] = 'Sample RNA polymerase II geneset - created remotely'
        geneset_data['abstract'] = 'Any process that modulates the rate, frequency or extent of a process involved in starting transcription from an RNA polymerase II promoter.'
        geneset_data['public'] = True
        geneset_data['annotations'] = {self.g1.pk: [20671152, 19583951], self.g2.pk: [8887666], self.g3.pk: [], self.g4.pk:[]}
        # Do not pass a 'xrdb' gene identifier

        resp = client.post('/api/v1/geneset', format="json", data=geneset_data)
        self.assertHttpCreated(resp)
        gsresp = self.api_client.get('/api/v1/geneset', format="json", data={'show_tip': 'true', 'full_annotations': 'true'})
        self.assertValidJSONResponse(gsresp)

        # Check some of the data that has been hydrated/dehydrated for this geneset
        self.assertEqual(self.deserialize(gsresp)['objects'][0]['title'], geneset_data['title'])
        self.assertEqual(len(self.deserialize(gsresp)['objects'][0]['tip']['annotations']), len(geneset_data['annotations']))
        self.assertEqual(set(self.deserialize(gsresp)['objects'][0]['tip']['genes']), self.gene_entrezid_set)


    def testGenesetCreationWithGenesAndPublications(self):
        """
        Test to create a new geneset, with passed genes AND publications
        """
        client = TestApiClient()
        client.client.login(username=self.username, password=self.password)

        # Get the organism uri just as the user would, doing a query to the API
        org_scientific_name = self.org1.scientific_name
        org_resp = self.api_client.get('/api/v1/organism', format="json", data={'scientific_name': org_scientific_name})
        org_object = self.deserialize(org_resp)['objects'][0]
        org_uri = org_object['resource_uri']

        geneset_data = {}
        geneset_data['organism'] = org_uri
        geneset_data['title'] = 'Sample RNA polymerase II geneset - created remotely'
        geneset_data['abstract'] = 'Any process that modulates the rate, frequency or extent of a process involved in starting transcription from an RNA polymerase II promoter.'
        geneset_data['public'] = True
        geneset_data['annotations'] = {55982: [20671152, 19583951], 18091: [8887666], 67087: [], 22410:[]}
        geneset_data['xrdb'] = 'Entrez'

        resp = client.post('/api/v1/geneset', format="json", data=geneset_data)
        self.assertHttpCreated(resp)
        gsresp = self.api_client.get('/api/v1/geneset', format="json", data={'show_tip': 'true', 'full_annotations': 'true'})
        self.assertValidJSONResponse(gsresp)

        # Check some of the data that has been hydrated/dehydrated for this geneset
        self.assertEqual(self.deserialize(gsresp)['objects'][0]['title'], geneset_data['title'])
        self.assertEqual(len(self.deserialize(gsresp)['objects'][0]['tip']['annotations']), len(geneset_data['annotations']))

    def testGenesetCreateGenesNotFound(self):
        """
        Test to create a new geneset where some of the genes passed are not found
        in the database. Check for response with warning stating those genes where
        not found.
        """
        client = TestApiClient()
        client.client.login(username=self.username, password=self.password)

        # Get the organism uri just as the user would, doing a query to the API
        org_scientific_name = self.org1.scientific_name
        org_resp = self.api_client.get('/api/v1/organism', format="json", data={'scientific_name': org_scientific_name})
        org_object = self.deserialize(org_resp)['objects'][0]
        org_uri = org_object['resource_uri']

        geneset_data = {}
        geneset_data['organism'] = org_uri
        geneset_data['title'] = 'Sample RNA polymerase II geneset - created remotely'
        geneset_data['abstract'] = 'Any process that modulates the rate, frequency or extent of a process involved in starting transcription from an RNA polymerase II promoter.'
        geneset_data['public'] = True
        geneset_data['xrdb'] = 'Entrez'

        geneset_data['annotations'] = {55982: [20671152, 19583951], 
                                       18091: [8887666], 67087: [], 22410:[]}

        not_in_db_genes = set([7915, 57494, 64902])  # These three do not exist in the database

        for geneid in not_in_db_genes:  # Add these to the 'annotations' in geneset_data
            geneset_data['annotations'][geneid] = []

        resp = client.post('/api/v1/geneset', format="json", data=geneset_data)
        self.assertHttpCreated(resp)

        warning_response = self.deserialize(resp)["Warning - The following genes were not found in our database"]
        genes_not_found = set()
        for not_found in warning_response:
            genes_not_found.add(int(not_found))
        self.assertEqual(genes_not_found, not_in_db_genes)

        gsresp = self.api_client.get('/api/v1/geneset', format="json", data={'show_tip': 'true', 'full_annotations': 'true'})
        self.assertValidJSONResponse(gsresp)

        # Check some of the data that has been hydrated/dehydrated for this geneset, 
        # check the length of the annotations that were actually found and got saved
        self.assertEqual(self.deserialize(gsresp)['objects'][0]['title'], geneset_data['title'])
        self.assertEqual(len(self.deserialize(gsresp)['objects'][0]['tip']['annotations']), len(geneset_data['annotations']) - len(not_in_db_genes))

    def testCreateGenesetAmbiguousSymbol(self):
        """
        Checking that the GenesetResource's obj_create() method correctly
        passes the scientific_name of the new geneset's organism to the
        Version.format_annotations() method, and that this filters out
        genes for the passed organism (in case there are genes with the
        same symbol for different organisms). This test is analogous to the
        CreatingRemoteVersionTestCase.testCreateVersionAmbiguousSymbol()
        test for the VersionResource in versions/tests.py.
        """
        client = TestApiClient()
        client.client.login(username=self.username, password=self.password)

        # Get the organism uri just as the user would, doing a query to the API
        org_scientific_name = self.org3.scientific_name
        org_resp = self.api_client.get('/api/v1/organism', format="json",
                                       data={'scientific_name': org_scientific_name})
        org_object = self.deserialize(org_resp)['objects'][0]
        org_uri = org_object['resource_uri']

        geneset_data = {}
        geneset_data['organism'] = org_uri
        geneset_data['title'] = 'Test yeast geneset'
        geneset_data['abstract'] = 'Adding yeast gene that has the same ' \
                                   'symbol as a human gene'
        geneset_data['annotations'] = {'ICR1': [20671152]}
        geneset_data['xrdb'] = 'Symbol'

        resp = client.post('/api/v1/geneset', format="json", data=geneset_data)

        new_geneset_uri = self.deserialize(resp)['resource_uri']

        gsresp = client.get(
            new_geneset_uri, format="json",
            data={'show_tip': 'true', 'full_annotations': 'true'}
        )
        self.assertValidJSONResponse(gsresp)

        simplified_annotations = []
        for annotation in self.deserialize(gsresp)['tip']['annotations']:
            simple_annot = {}
            simple_annot['gene'] = annotation['gene']['entrezid']
            simple_annot['pubs'] = [pub['pmid'] for pub in annotation['pubs']]
            simplified_annotations.append(simple_annot)

        entrez_annots = [{'gene': 9164906, 'pubs': [20671152]}]
        self.assertEqual(simplified_annotations, entrez_annots)

    def testCreateGenesetWithTags(self):
        """
        Test to create a new geneset with some annotations AND tags
        """
        client = TestApiClient()
        client.client.login(username=self.username, password=self.password)

        # Get the organism uri just as the user would, doing a query to the API
        org_scientific_name = self.org1.scientific_name
        org_resp = self.api_client.get(
            '/api/v1/organism', format="json",
            data={'scientific_name': org_scientific_name}
        )
        org_object = self.deserialize(org_resp)['objects'][0]
        org_uri = org_object['resource_uri']

        geneset_data = {}
        geneset_data['organism'] = org_uri
        geneset_data['title'] = 'RNA polymerase II geneset with tags'
        geneset_data['abstract'] = ('Any process that modulates the rate, '
                                    'frequency or extent of a process involved'
                                    ' in starting transcription from an RNA '
                                    'polymerase II promoter.')
        geneset_data['public'] = True
        geneset_data['annotations'] = {55982: [20671152, 19583951],
                                       18091: [8887666], 67087: []}
        geneset_data['xrdb'] = 'Entrez'
        geneset_data['tags'] = ['alpha', 'beta', 'omega']

        resp = client.post('/api/v1/geneset', format="json", data=geneset_data)
        self.assertHttpCreated(resp)

        gsresp = self.api_client.get(
            '/api/v1/geneset', format="json", data={'show_tip': 'true'})
        self.assertValidJSONResponse(gsresp)

        # Check that all tags have been saved successfully. We need to
        # convert the lists to set, because they might have been saved
        # in a different order:
        self.assertEqual(set(self.deserialize(gsresp)['objects'][0]['tags']),
                         set(geneset_data['tags']))


class GenesetSlugAndCreatorTestCase(ResourceTestCase):

    def setUp(self):
        super(GenesetSlugAndCreatorTestCase, self).setUp()

        self.org1 = Organism.objects.create(
            common_name="Mouse", scientific_name="Mus musculus",
            taxonomy_id=10090
        )

        self.username = "hjkl"
        self.email = "hjkl@example.com"
        self.password = "1234"
        self.user1 = User.objects.create_user(self.username, self.email,
                                              self.password)
        self.user2 = factory.create(User)

        self.g1 = Gene.objects.create(
            entrezid=18128, systematic_name="g1", standard_name="Notch1",
            description="notch 1", organism=self.org1, aliases="Mis6 N1 Tan1")
        self.g2 = Gene.objects.create(
            entrezid=13819, systematic_name="g2", standard_name="Epas1",
            description="endothelial PAS domain protein 1",
            organism=self.org1, aliases="HIF-2alpha HIF2A")
        self.g3 = Gene.objects.create(
            entrezid=15251, systematic_name="g3",
            standard_name="Hif1a",
            description="hypoxia inducible factor 1, alpha subunit",
            organism=self.org1, aliases="HIF1alpha MOP1")

        # Create two genesets with the same title, which will create the same
        # slug. However, they will have different creators, so this will
        # satisfy the unique_together database requirement of 'slug' and
        # 'creator'.
        self.geneset1 = Geneset.objects.create(
            creator=self.user1, title='TestGenesetABCDEFG', organism=self.org1,
            abstract='', public=True)
        self.geneset2 = Geneset.objects.create(
            creator=self.user2, title='TestGenesetABCDEFG', organism=self.org1,
            abstract='', public=True)

    def testRemoteCreationSameSlug(self):
        """
        Test to check that users are given a helpful error message (that
        also points to the Tribe docs) if they create a geneset with the same
        slug as one of their already existing genesets.
        """
        client = TestApiClient()
        client.client.login(username=self.username, password=self.password)

        geneset1_data = {}
        geneset1_data['organism'] = '/api/v1/organism/' + self.org1.slug
        geneset1_data['title'] = 'SampleSameSlug'
        geneset1_data['abstract'] = 'SampleAbstract1'
        geneset1_data['annotations'] = {self.g1.entrezid: [18299578]}

        resp = client.post('/api/v1/geneset', format="json",
                           data=geneset1_data)
        self.assertHttpCreated(resp)

        geneset2_data = {}
        geneset2_data['organism'] = '/api/v1/organism/' + self.org1.slug
        geneset2_data['title'] = 'SampleSameSlug'
        geneset2_data['abstract'] = 'SampleAbstract2'
        geneset2_data['annotations'] = {self.g2.entrezid: [14608355, 17284606],
                                        self.g3.entrezid: [12832481]}

        resp = client.post('/api/v1/geneset', format="json",
                           data=geneset2_data)
        self.assertHttpBadRequest(resp)
        self.assertEqual(resp.content, (
            'There is already one collection with this url created by this '
            'account. Please choose a different collection title. For more '
            'information, see our documentation here: ' + settings.DOCS_URL +
            'using_tribe.html#collection-urls'))

    def testRemoteCreationVeryLongTitles(self):
        """
        Test to check very long geneset titles. Since slugs are automatically
        generated from the first 75 characters of geneset titles (if no 'slug'
        is explicitly sent with the geneset data), very long titles that only
        differ from each other after 75 characters produce identical slugs.
        This test checks that users are given a helpful error message (that
        also points to the Tribe docs) if this happens.
        """
        client = TestApiClient()
        client.client.login(username=self.username, password=self.password)

        geneset1_data = {}
        geneset1_data['organism'] = '/api/v1/organism/' + self.org1.slug
        geneset1_data['title'] = 'GO-regulation of transcription from RNA '\
            'polymerase II promoter in response to stress'
        geneset1_data['abstract'] = 'Any process that increases the '\
            'frequency, rate or extent of transcription from an RNA '\
            'polymerase II promoter as a result of a stimulus indicating'\
            ' the organism is under stress...'
        geneset1_data['public'] = True
        geneset1_data['annotations'] = {self.g1.entrezid: [18299578]}

        resp = client.post('/api/v1/geneset', format="json",
                           data=geneset1_data)
        self.assertHttpCreated(resp)

        geneset2_data = {}
        geneset2_data['organism'] = '/api/v1/organism/' + self.org1.slug

        # This title is 94 characters long and differs from the geneset1_data
        # title in the 78th character (beyond truncation point).
        geneset2_data['title'] = 'GO-regulation of transcription from RNA '\
            'polymerase II promoter in response to oxidative stress'

        geneset2_data['abstract'] = 'Modulation of the frequency, rate or '\
            'extent of transcription from an RNA polymerase II promoter as'\
            ' a result of a stimulus indicating the organism is under '\
            'oxidative stress, a state often resulting from exposure...'
        geneset2_data['public'] = True
        geneset2_data['annotations'] = {self.g2.entrezid: [14608355, 17284606],
                                        self.g3.entrezid: [12832481]}

        resp = client.post('/api/v1/geneset', format="json",
                           data=geneset2_data)
        self.assertHttpBadRequest(resp)
        self.assertEqual(resp.content, (
            'There is already one collection with this url created by this '
            'account. Please choose a different collection title. For more '
            'information, see our documentation here: ' + settings.DOCS_URL +
            'using_tribe.html#collection-urls'))

    def testGettingSameSlugGeneset(self):
        """
        Test to check that users successfully get the only one, desired
        geneset when they fetch it by creator username and slug (even if
        another geneset exists in the database with the same slug).
        """
        client = TestApiClient()
        client.client.login(username=self.username, password=self.password)

        geneset1_url = ('/api/v1/geneset/' + self.username +
                        '/testgenesetabcdefg/')

        resp = client.get(geneset1_url, format="json")

        # Check that we get a 200 HTTP response instead of a
        # 300 response (Multiple Objects Returned)
        self.assertValidJSONResponse(resp)
        creator = self.deserialize(resp)['creator']
        self.assertEqual(creator['username'], self.username)

    def testFilteringByCreatorUsername(self):
        """
        Test to check that users successfully get the only one, desired
        geneset when they make a request to the geneset list API url but
        filter by creator username.
        """

        client = TestApiClient()

        parameters = {'creator__username': self.username}

        resp = client.get('/api/v1/geneset/', format="json", data=parameters)

        # Check that we get a 200 HTTP response, containing only one geneset.
        self.assertValidJSONResponse(resp)
        resp_dict = self.deserialize(resp)

        self.assertEqual(resp_dict['meta']['total_count'], 1)
        self.assertEqual(len(resp_dict['objects']), 1)
        self.assertEqual(resp_dict['objects'][0]['creator']['username'],
                         self.username)

        # Check that if we do not pass any parameters (and therefore do
        # not filter by creator__username), we get a 200 HTTP response,
        # containing two genesets.
        resp2 = client.get('/api/v1/geneset/', format="json")
        resp2_dict = self.deserialize(resp2)

        self.assertEqual(resp2_dict['meta']['total_count'], 2)
        self.assertEqual(len(resp2_dict['objects']), 2)


class FilterGenesetByDateTestCase(ResourceTestCaseMixin, TestCase):

    def setUp(self):
        super(FilterGenesetByDateTestCase, self).setUp()

        self.geneset1 = factory.create(Geneset, {'public': True,
                                                 'fork_of': None})
        self.geneset2 = factory.create(Geneset, {'public': True,
                                                 'fork_of': None})

        # This method of making django believe it is a different date and
        # time than it really is now was taken from here:
        # https://devblog.kogan.com/blog/testing-auto-now-datetime-fields-in-django
        # This is necessary to save the date we want in the commit_date field,
        # since it has the 'auto_now_add' argument set to True.
        with mock.patch('django.utils.timezone.now') as mock_now:
            mock_now.return_value = timezone.make_aware(
                datetime(2005, 1, 1), timezone.get_current_timezone())

            self.version1a = factory.create(
                Version, {'geneset': self.geneset1,
                          'parent': None,
                          'annotations': frozenset([(1, 1)]),
                          'ver_hash': ver_hash_generator()})

            mock_now.return_value = timezone.make_aware(
                datetime(2007, 1, 1), timezone.get_current_timezone())

            self.version1b = factory.create(
                Version, {'geneset': self.geneset1,
                          'parent': self.version1a,
                          'annotations': frozenset([(1, 1), (1, 2)]),
                          'ver_hash': ver_hash_generator()})

            mock_now.return_value = timezone.make_aware(
                datetime(2011, 1, 1), timezone.get_current_timezone())

            self.version1c = factory.create(
                Version, {'geneset': self.geneset1,
                          'parent': self.version1b,
                          'annotations': frozenset([(1, 1), (1, 3)]),
                          'ver_hash': ver_hash_generator()})

        # Go back to using the current time for all of the following versions
        # being created.
        self.version2a = factory.create(
            Version, {'geneset': self.geneset2,
                      'parent': None,
                      'annotations': frozenset([(1, 1)]),
                      'ver_hash': ver_hash_generator()})
        self.version2b = factory.create(
            Version, {'geneset': self.geneset2,
                      'parent': self.version2a,
                      'annotations': frozenset([(1, 1), (1, 2)]),
                      'ver_hash': ver_hash_generator()})
        self.version2c = factory.create(
            Version, {'geneset': self.geneset2,
                      'parent': self.version2b,
                      'annotations': frozenset([(1, 1), (1, 3)]),
                      'ver_hash': ver_hash_generator()})

    def testGetGenesetVersionsByDate(self):
        """
        Test to check that only the genesets and versions created and
        modified before the date passed in the parameters (as
        'modified_before') get returned.
        """

        client = TestApiClient()

        parameters = {'modified_before': '12/31/10', 'show_versions': 'true'}

        resp = client.get('/api/v1/geneset/', format='json', data=parameters)

        # Check that we get a 200 HTTP response.
        self.assertValidJSONResponse(resp)
        resp_dict = self.deserialize(resp)

        # Check that we only get one geneset back.
        self.assertEqual(resp_dict['meta']['total_count'], 1)
        self.assertEqual(len(resp_dict['objects']), 1)

        # Check that only 2 of the 3 geneset versions get returned.
        self.assertEqual(len(resp_dict['objects'][0]['versions']), 2)
