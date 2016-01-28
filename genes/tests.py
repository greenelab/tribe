from datetime import date

from django.test import TestCase
from django.core.exceptions import FieldError
from django.db import IntegrityError

from fixtureless import Factory

from organisms.models import Organism
from genes.models import Gene, CrossRef, CrossRefDB
from genes.utils import translate_genes

factory = Factory()

class TranslateTestCase(TestCase):
    def setUp(self):
        org = factory.create(Organism)
        xrdb1 = CrossRefDB(name="ASDF", url="http://www.example.com")
        xrdb1.save()
        xrdb2 = CrossRefDB(name="XRDB2", url="http://www.example.com/2")
        xrdb2.save()
        g1 = Gene(entrezid=1, systematic_name="g1", standard_name="G1", description="asdf", organism=org, aliases="gee1 GEE1")
        g1.save()
        g2 = Gene(entrezid=2, systematic_name="g2", standard_name="G2", description="asdf", organism=org, aliases="gee2 GEE2")
        g2.save()
        xref1 = CrossRef(crossrefdb = xrdb1, gene=g1, xrid="XRID1")
        xref1.save()
        xref2 = CrossRef(crossrefdb = xrdb2, gene=g2, xrid="XRID1")
        xref2.save()
        xref3 = CrossRef(crossrefdb = xrdb1, gene=g1, xrid="XRRID1")
        xref3.save()
        xref4 = CrossRef(crossrefdb = xrdb1, gene=g2, xrid="XRID2")
        xref4.save()

        org2 = Organism(taxonomy_id=1234, common_name="Computer mouse", scientific_name="Mus computurus", slug="mus-computurus")
        org2.save()
        org3 = Organism(taxonomy_id=4321, common_name="Computer screen", scientific_name="Monitorus computurus", slug="monitorus-computurus")
        org3.save()

        #Make systematic and standard name the same for the following genes. but make organisms different. Skip entrezid 3 since that is used by other tests.
        g4  = Gene(entrezid=4, systematic_name="acdc", standard_name="ACDC", description="asdf", organism=org2, aliases="gee4 GEE4")
        g4.save()
        g5  = Gene(entrezid=5, systematic_name="acdc", standard_name="ACDC", description="asdf", organism=org3, aliases="gee5 GEE5")
        g5.save()

    def test_translate_symbol_entrez_diff_organisms(self):
        """
        translate should be able to differentiate between different organism genes when passed identical symbols
        """
        translation = translate_genes(id_list=['ACDC'], from_id="Symbol", to_id="Entrez", organism="Mus computurus")
        self.assertEqual(translation, {'ACDC':[4], 'not_found':[]})

    def test_translate_symbol_entrez_diff_organisms2(self):
        """
        Same as previous test, but uses the other organism as input
        """
        translation = translate_genes(id_list=['ACDC'], from_id="Symbol", to_id="Entrez", organism="Monitorus computurus")
        self.assertEqual(translation, {'ACDC':[5], 'not_found':[]})

    def test_translate_entrez_entrez(self):
        """
        translate should be able to translate from entrez to entrez.
        """
        translation = translate_genes(id_list=[1, 2], from_id="Entrez", to_id="Entrez")
        self.assertEqual(translation, {1:[1,], 2:[2,], 'not_found':[]})

    def test_translate_entrez_standard_name(self):
        """
        translate should be able to translate from entrez to standard names.
        """
        translation = translate_genes(id_list=[1, 2], from_id="Entrez", to_id="Standard name")
        self.assertEqual(translation, {1:['G1',], 2:['G2',], 'not_found':[]})

    def test_translate_entrez_systematic_name(self):
        """
        translate should be able to translate from entrez to standard names.
        """
        translation = translate_genes(id_list=[1, 2], from_id="Entrez", to_id="Systematic name")
        self.assertEqual(translation, {1:['g1',], 2:['g2',], 'not_found':[]})

    def test_translate_entrez_xrdb(self):
        """
        translate should be able to translate from entrez to standard names.
        """
        translation = translate_genes(id_list=[1, 2], from_id="Entrez", to_id="ASDF")
        self.assertEqual(translation, {1:['XRID1','XRRID1',], 2:['XRID2',], 'not_found':[]})

    def test_translate_xrdb_entrez(self):
        """
        translate should be able to translate from entrez to standard names.
        """
        translation = translate_genes(id_list=['XRID1', 'XRRID1', 'XRID2'], from_id="ASDF", to_id="Entrez")
        self.assertEqual(translation, {'XRID1': [1,], 'XRRID1': [1,], 'XRID2': [2,], 'not_found':[]})

    def test_translate_entrez_entrez_missing(self):
        """
        translate should be able to translate from entrez to entrez with a missing value.
        """
        translation = translate_genes(id_list=[1, 2, 3], from_id="Entrez", to_id="Entrez")
        self.assertEqual(translation, {1:[1,], 2:[2,], 'not_found':[3]})

    def test_translate_entrez_standard_name(self):
        """
        translate should be able to translate from entrez to standard names.
        """
        translation = translate_genes(id_list=[1, 2, 3], from_id="Entrez", to_id="Standard name")
        self.assertEqual(translation, {1:['G1',], 2:['G2',], 'not_found':[3]})

    def tearDown(self):
        Organism.objects.all().delete() #remove any created publications
        Gene.objects.all().delete() #remove any created publications
        CrossRef.objects.all().delete() #remove any created publications
        CrossRefDB.objects.all().delete() #remove any created publications


class CrossRefDBTestCase(TestCase):

    def test_saving_xrdb(self):
        """
        Test that this simple CrossRefDB creation raises no errors
        """
        xrdb1 = factory.create(CrossRefDB, {"name": "XRDB1"})

    def test_saving_xrdb_no_name(self):
        """
        Check that CrossRefDBs in database are required to have a non-null
        name - if they do, raise IntegrityError.
        """
        with self.assertRaises(IntegrityError):
            xrdb1 = factory.create(CrossRefDB, {"name": None})

    def test_saving_xrdb_blank_name(self):
        """
        Check that CrossRefDBs in database are required to have a name that
        is not an empty string - if they do, raise FieldError.
        """
        with self.assertRaises(FieldError):
            xrdb1 = factory.create(CrossRefDB, {"name": ""})
