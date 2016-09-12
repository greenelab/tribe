from datetime import date

from django.test import TestCase

from fixtureless import Factory

from publications.models import Publication
from publications.utils import load_pmids

factory = Factory()

class PublicationTestCase(TestCase):
    def test_get_single_pmid(self):
        """
        load_pmids should be able to get a single publication's information successfully from pubmed's efetch
        """
        load_pmids(['1', ])
        pub = Publication.objects.get(pmid=1)
        self.assertEqual(pub.title, 'Formate assay in body fluids: application in methanol poisoning.')
        self.assertEqual(pub.date, date(1975, 6, 1))
        self.assertEqual(pub.authors, 'Makar AB, McMartin KE, Palese M, Tephly TR')
        self.assertEqual(pub.journal, 'Biochem Med')
        self.assertEqual(pub.volume, '13')
        self.assertEqual(pub.issue, '2')
        self.assertEqual(pub.pages, '117-26')

    def test_get_multiple_pmid(self):
        """
        load_pmids should be able to get multiple publications' information successfully from pubmed's efetch
        """
        load_pmids(['1', '2'])
        #First Pub
        pub1 = Publication.objects.get(pmid=1)
        self.assertEqual(pub1.title, 'Formate assay in body fluids: application in methanol poisoning.')
        self.assertEqual(pub1.date, date(1975, 6, 1))
        self.assertEqual(pub1.authors, 'Makar AB, McMartin KE, Palese M, Tephly TR')
        self.assertEqual(pub1.journal, 'Biochem Med')
        self.assertEqual(pub1.volume, '13')
        self.assertEqual(pub1.issue, '2')
        self.assertEqual(pub1.pages, '117-26')
        #Second Pub
        pub2 = Publication.objects.get(pmid=2)
        self.assertEqual(pub2.title, 'Delineation of the intimate details of the backbone conformation of pyridine nucleotide coenzymes in aqueous solution.')
        self.assertEqual(pub2.date, date(1975, 10, 27))
        self.assertEqual(pub2.authors, 'Bose KS, Sarma RH')
        self.assertEqual(pub2.journal, 'Biochem Biophys Res Commun')
        self.assertEqual(pub2.volume, '66')
        self.assertEqual(pub2.issue, '4')
        self.assertEqual(pub2.pages, '1173-9')

    def test_force_update_pmid_exists(self):
        """
        force_update should cause existing data to be overwritten.
        """
        initial = {
            'pmid': 1,
            'title': 'ASDF',
        }
        pub = factory.create(Publication, initial)
        pub.save()
        self.assertEqual(pub.title, initial['title'])
        load_pmids(['1', ], force_update=True)
        #First Pub
        pub1 = Publication.objects.get(pmid=1)
        self.assertEqual(pub1.title, 'Formate assay in body fluids: application in methanol poisoning.')
        self.assertEqual(pub1.date, date(1975, 6, 1))
        self.assertEqual(pub1.authors, 'Makar AB, McMartin KE, Palese M, Tephly TR')
        self.assertEqual(pub1.journal, 'Biochem Med')
        self.assertEqual(pub1.volume, '13')
        self.assertEqual(pub1.issue, '2')
        self.assertEqual(pub1.pages, '117-26')
        self.assertEqual(pub1.id, pub.id) # make sure primary key doesn't change

    def test_force_update_pmid_doesnt_exist(self):
        """
        force_update should cause existing data to be overwritten.
        """
        load_pmids(['1', ], force_update=True)
        #First Pub
        pub1 = Publication.objects.get(pmid=1)
        self.assertEqual(pub1.title, 'Formate assay in body fluids: application in methanol poisoning.')
        self.assertEqual(pub1.date, date(1975, 6, 1))
        self.assertEqual(pub1.authors, 'Makar AB, McMartin KE, Palese M, Tephly TR')
        self.assertEqual(pub1.journal, 'Biochem Med')
        self.assertEqual(pub1.volume, '13')
        self.assertEqual(pub1.issue, '2')
        self.assertEqual(pub1.pages, '117-26')

    def test_error_pub_id(self):
        """
        A publication that does not exist should emit a warning and nothing should be created.
        """
        load_pmids(['2764472319', ])
        with self.assertRaises(Publication.DoesNotExist):
            Publication.objects.get(pmid=2764472319)

    def test_load_pub_already_exists(self):
        """
        Loading a publication that already exists should do nothing when force_update is not passed.
        """
        initial = {
            'pmid': 1,
            'title': 'ASDF',
        }
        pub = factory.create(Publication, initial)
        pub.save()
        self.assertEqual(pub.title, initial['title'])
        load_pmids(['1', ])
        self.assertEqual(pub.title, initial['title'])

    def test_can_load_when_issue_volume_pages_are_null(self):
        """
        Some PMIDs lack an issue (e.g. 9371713), volume, or pages. This test makes sure that these can still be loaded.
        """
        load_pmids(['9371713', ])
        pub = Publication.objects.get(pmid=9371713)
        self.assertIsNone(pub.issue)
        #load_pmids(['24117850', ]) //Need to figure out a better way to test this, this only occurs for pubs that are in process.
        #pub = Publication.objects.get(pmid=24117850)
        #self.assertIsNone(pub.volume)
        #self.assertIsNone(pub.pages)

    def tearDown(self):
        Publication.objects.all().delete() #remove any created publications
