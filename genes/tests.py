from django.test import TestCase
from django.core.exceptions import FieldError
from django.db import IntegrityError
from django.core.management import call_command
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

        # g1 and g2 have both standard and systematic names.
        g1 = Gene(entrezid=1, systematic_name="g1", standard_name="G1",
                  description="asdf", organism=org, aliases="gee1 GEE1")
        g1.save()
        g2 = Gene(entrezid=2, systematic_name="g2", standard_name="G2",
                  description="asdf", organism=org, aliases="gee2 GEE2")
        g2.save()

        xref1 = CrossRef(crossrefdb=xrdb1, gene=g1, xrid="XRID1")
        xref1.save()
        xref2 = CrossRef(crossrefdb=xrdb2, gene=g2, xrid="XRID1")
        xref2.save()
        xref3 = CrossRef(crossrefdb=xrdb1, gene=g1, xrid="XRRID1")
        xref3.save()
        xref4 = CrossRef(crossrefdb=xrdb1, gene=g2, xrid="XRID2")
        xref4.save()

        org2 = Organism(taxonomy_id=1234, common_name="Computer mouse",
                        scientific_name="Mus computurus",
                        slug="mus-computurus")
        org2.save()
        org3 = Organism(taxonomy_id=4321, common_name="Computer screen",
                        scientific_name="Monitorus computurus",
                        slug="monitorus-computurus")
        org3.save()

        # Make systematic and standard name the same for the following genes,
        # but make organisms different. Skip entrezid 3 since that is used by
        # other tests.
        g4 = Gene(entrezid=4, systematic_name="acdc", standard_name="ACDC",
                  description="asdf", organism=org2, aliases="gee4 GEE4")
        g4.save()
        g5 = Gene(entrezid=5, systematic_name="acdc", standard_name="ACDC",
                  description="asdf", organism=org3, aliases="gee5 GEE5")
        g5.save()

        # g101 has standard name, but no systematic name.
        g101 = Gene(entrezid=101, standard_name="std_101", organism=org2)
        g101.save()

        # g102 has systematic name, but no standard name.
        g102 = Gene(entrezid=102, systematic_name="sys_102", organism=org2)
        g102.save()

    def test_translate_symbol_entrez_diff_organisms(self):
        """
        translate_genes() should be able to differentiate between different
        organism genes when passed identical symbols.
        """
        # This test also confirmed that when both standard name and systematic
        # name are available, the sysmbol will be standard name.
        translation = translate_genes(id_list=['ACDC'],
                                      from_id="Symbol", to_id="Entrez",
                                      organism="Mus computurus")
        self.assertEqual(translation, {'ACDC': [4], 'not_found': []})

    def test_translate_symbol_entrez_diff_organisms2(self):
        """
        Same as previous test, but uses the other organism as input.
        """
        translation = translate_genes(id_list=['ACDC'],
                                      from_id="Symbol", to_id="Entrez",
                                      organism="Monitorus computurus")
        self.assertEqual(translation, {'ACDC': [5], 'not_found': []})

    def test_translate_entrez_entrez(self):
        """
        Test translation from entrez to entrez.
        """
        translation = translate_genes(id_list=[1, 2],
                                      from_id="Entrez", to_id="Entrez")
        self.assertEqual(translation, {1: [1, ], 2: [2, ], 'not_found': []})

    def test_translate_entrez_standard_name(self):
        """
        Test translation from entrez to standard names.
        """
        translation = translate_genes(id_list=[1, 2],
                                      from_id="Entrez",
                                      to_id="Standard name")
        self.assertEqual(translation,
                         {1: ['G1', ], 2: ['G2', ], 'not_found': []})

    def test_translate_entrez_systematic_name(self):
        """
        Test translation from entrez to systematic names.
        """
        translation = translate_genes(id_list=[1, 2],
                                      from_id="Entrez",
                                      to_id="Systematic name")
        self.assertEqual(translation,
                         {1: ['g1', ], 2: ['g2', ], 'not_found': []})

    def test_translate_entrez_xrdb(self):
        """
        Test translation from entrez to ASDF.
        """
        translation = translate_genes(id_list=[1, 2],
                                      from_id="Entrez", to_id="ASDF")
        self.assertEqual(translation, {1: ['XRID1', 'XRRID1', ],
                                       2: ['XRID2', ], 'not_found': []})

    def test_translate_xrdb_entrez(self):
        """
        Test translation from ASDF to entrez.
        """
        translation = translate_genes(id_list=['XRID1', 'XRRID1', 'XRID2'],
                                      from_id="ASDF", to_id="Entrez")
        self.assertEqual(translation, {'XRID1': [1, ], 'XRRID1': [1, ],
                                       'XRID2': [2, ], 'not_found': []})

    def test_translate_entrez_entrez_missing(self):
        """
        Test translation from entrez to entrez with a missing value.
        """
        translation = translate_genes(id_list=[1, 2, 3],
                                      from_id="Entrez", to_id="Entrez")
        self.assertEqual(translation, {1: [1, ], 2: [2, ], 'not_found': [3]})

    def test_translate_entrez_standard_name_missing(self):
        """
        Test translation from entrez to standard names with a missing value.
        """
        translation = translate_genes(id_list=[1, 2, 3],
                                      from_id="Entrez", to_id="Standard name")
        self.assertEqual(translation,
                         {1: ['G1', ], 2: ['G2', ], 'not_found': [3]})

    def test_translate_symbol_entrez(self):
        """
        Test translation from symbol to entrez when either standard name or
        systematic name is null.
        """
        # Test the gene that has standard name.
        translation = translate_genes(id_list=['std_101'],
                                      from_id="Symbol", to_id="Entrez",
                                      organism="Mus computurus")
        self.assertEqual(translation, {'std_101': [101], 'not_found': []})
        # Test the gene that does NOT have standard name.
        translation = translate_genes(id_list=['sys_102'],
                                      from_id="Symbol", to_id="Entrez",
                                      organism="Mus computurus")
        self.assertEqual(translation, {'sys_102': [102], 'not_found': []})

    def test_translate_entrez_symbol(self):
        """
        Test translation from entrez to symbol when either standard name or
        systematic name is null.
        """
        # Test the gene that has standard name.
        translation = translate_genes(id_list=[101],
                                      from_id="Entrez", to_id="Symbol",
                                      organism="Mus computurus")
        self.assertEqual(translation, {101: ['std_101'], 'not_found': []})
        # Test the gene that does NOT have standard name.
        translation = translate_genes(id_list=[102],
                                      from_id="Entrez", to_id="Symbol",
                                      organism="Mus computurus")
        self.assertEqual(translation, {102: ['sys_102'], 'not_found': []})

    def test_empty_standard_and_systematic_names(self):
        """
        Test that a ValueError exception will be raised when we try to create a
        gene whose standard and systematic names are both empty or null, or
        ONLY consist of space characters (such as space, tab, new line, etc).
        """
        org = factory.create(Organism)

        # Neither standard_name nor systematic_name is set explicitly.
        unnamed_gene = Gene(entrezid=999, organism=org)
        self.assertRaises(ValueError, unnamed_gene.save)

        # standard_name consists of only space characters.
        # systematic_name is u'' here, because it is not set explicitly, and
        # by default "null=False" for this field in the model.
        unnamed_gene = Gene(entrezid=999, standard_name="\t  \n", organism=org)
        self.assertRaises(ValueError, unnamed_gene.save)

        # Both standard_name and systematic_name are empty strings.
        unnamed_gene = Gene(entrezid=999, standard_name="", systematic_name="",
                            organism=org)
        self.assertRaises(ValueError, unnamed_gene.save)

        # Both standard_name and systematic_name consist of space characters
        # only.
        unnamed_gene = Gene(entrezid=999, standard_name="  ",
                            systematic_name="\t  \n ", organism=org)
        self.assertRaises(ValueError, unnamed_gene.save)

    def tearDown(self):
        Organism.objects.all().delete()    # Remove Organism objects.
        Gene.objects.all().delete()        # Remove Gene objects.
        CrossRef.objects.all().delete()    # Remove CrossRef objects.
        CrossRefDB.objects.all().delete()  # Remove CrossRefDB objects.


class CrossRefDBTestCase(TestCase):
    def test_saving_xrdb(self):
        """
        Test that this simple CrossRefDB creation raises no errors.
        """
        factory.create(CrossRefDB, {"name": "XRDB1"})

    def test_saving_xrdb_no_name(self):
        """
        Check that CrossRefDBs in database are required to have a non-null
        name - if they do, raise IntegrityError.
        """
        with self.assertRaises(IntegrityError):
            factory.create(CrossRefDB, {"name": None})

    def test_saving_xrdb_blank_name(self):
        """
        Check that CrossRefDBs in database are required to have a name that
        is not an empty string - if they do, raise FieldError.
        """
        with self.assertRaises(FieldError):
            factory.create(CrossRefDB, {"name": ""})


class LoadCrossRefsTestCase(TestCase):

    def setUp(self):
        xrdb1 = CrossRefDB.objects.create(
            name="Ensembl", url="http://www.ensembl.org/Gene/Summary?g=_REPL_")

        CrossRefDB.objects.create(
            name="UniProtKB", url="http://www.uniprot.org/uniprot/_REPL_")

        g1 = factory.create(Gene, {'entrezid': 50810})
        g2 = factory.create(Gene)
        g3 = factory.create(Gene)
        g4 = factory.create(Gene)

        factory.create(CrossRef, {'crossrefdb': xrdb1, 'gene': g1,
                                  'xrid': 'ENSG00000166503'})
        factory.create(CrossRef, {'crossrefdb': xrdb1, 'gene': g2,
                                  'xrid': 'ENSG00000214575'})
        factory.create(CrossRef, {'crossrefdb': xrdb1, 'gene': g3,
                                  'xrid': 'ENSG00000170312'})
        factory.create(CrossRef, {'crossrefdb': xrdb1, 'gene': g4,
                                  'xrid': 'ENSG00000172053'})

    def test_load_uniprot_mgmt_command(self):
        """
        Check that genes_load_uniprot management command loads UniProtKB
        identifiers (using Entrez and Ensembl) and that it also saves those
        relationships in the database.
        """
        call_command('genes_load_uniprot',
                     uniprot='genes/test_files/test_uniprot_entrez_ensembl.txt')

        uniprot1 = CrossRef.objects.get(xrid='A0A024R216')
        self.assertEqual(uniprot1.gene.entrezid, 50810)
        e1 = CrossRef.objects.filter(
            crossrefdb__name='Ensembl').get(gene=uniprot1.gene)
        self.assertEqual(e1.xrid, 'ENSG00000166503')

        uniprot2 = CrossRef.objects.get(xrid='A0A024R214')
        e2 = CrossRef.objects.filter(
            crossrefdb__name='Ensembl').get(gene=uniprot2.gene)
        self.assertEqual(e2.xrid, 'ENSG00000214575')

        uniprot3 = CrossRef.objects.get(xrid='A0A024QZP7')
        e3 = CrossRef.objects.filter(
            crossrefdb__name='Ensembl').get(gene=uniprot3.gene)
        self.assertEqual(e3.xrid, 'ENSG00000170312')

        uniprot4 = CrossRef.objects.get(xrid='A0A0U1RQX9')
        e4 = CrossRef.objects.filter(
            crossrefdb__name='Ensembl').get(gene=uniprot4.gene)
        self.assertEqual(e4.xrid, 'ENSG00000172053')
