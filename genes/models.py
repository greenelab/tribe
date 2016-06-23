import logging
logger = logging.getLogger(__name__)

from django.db import models
from django.template.defaultfilters import slugify
from django.core.exceptions import FieldError
from organisms.models import Organism
import re

"""
The class 'Gene' extends the Model class in Django (see organisms/models.py), and serves
as a Django model constructor, which will create a table for Genes in the database.
For more information, see: https://docs.djangoproject.com/en/dev/topics/db/models/
Genes will be added from an online database like 'Entrez', using the Django management
commands (see genes/management/commands/genes_load_geneinfo.py).
"""

# Regular expressions to be matched in the methods of 'Gene'
nonalpha = re.compile(r'[^a-zA-Z0-9]')
nonalpha_space = re.compile(r'[^a-zA-Z0-9\ ]')
num = re.compile(r'[0-9]')

class Gene(models.Model):
    entrezid        = models.IntegerField(null=True, db_index=True, unique=True)
    systematic_name = models.CharField(max_length=32, db_index=True) # Used for organisms like yeast
    standard_name   = models.CharField(max_length=32, null=True, db_index=True) # Gene symbol will be standard_name or
                                                                                # systematic_name if there is no standard_name
    description     = models.TextField() # Description/full name of gene
    organism        = models.ForeignKey(Organism, null=False)
    # The organism field contains the primary key of whichever organism instance the gene belongs to. For more info,
    # see: https://docs.djangoproject.com/en/1.5/ref/models/fields/#django.db.models.ForeignKey
    aliases = models.TextField() #store a space separated list of aliases, helps whoosh search
                                #before this change, aliases were stored as separate database table.
    obsolete = models.BooleanField(default=False)
    weight = models.FloatField(default=1)#Weight used for search results, needed now that we allow genes with identical symbols

    #__unicode__ in django explained: https://docs.djangoproject.com/en/dev/ref/models/instances/#unicode
    def __unicode__(self):
        return self.symbol

    def _get_symbol(self):
        if self.standard_name:
            return self.standard_name
        else:
            return self.systematic_name
    symbol = property(_get_symbol)

    def wall_of_name(self):
	# Appends identifiers for the different databases (such as Entrez id's) and returns them.
	# Uses the CrossRef class below.
        names = [self.standard_name, self.systematic_name]
        names.extend([xref.xrid for xref in self.crossref_set.all()])
        for i in range(len(names)):
            names[i] = re.sub(nonalpha,'',names[i])
        return ' '.join(names) + ' ' + re.sub(num, '', self.standard_name)


class CrossRefDB(models.Model):
    name = models.CharField(max_length=64, unique=True, db_index=True,
                            blank=False)
    url = models.URLField()

    def save(self, *args, **kwargs):
        """
        Extends save method of Django models to check that the database name
        is not left blank. Note: 'blank=False' is only checked at a
        form-validation-stage. A test using Fixtureless, that tried to
        randomly create a CrossRefDB with an empty string name would
        unintentionally break the test.
        """
        if self.name == '':
            raise FieldError
        else:
            return super(CrossRefDB, self).save(*args, **kwargs)

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = "Cross Reference Database"


class CrossRef(models.Model):
    crossrefdb = models.ForeignKey(CrossRefDB, null=False)
    gene = models.ForeignKey(Gene, null=False)
    xrid = models.CharField(max_length=32, null=False, db_index=True)

    def __unicode__(self):
        return self.xrid

    # Return the url for this entry
    def _get_url(self):
        url = self.crossrefdb.url
        if "_SPEC_" in url:
            species_name = self.gene.organism.scientific_name
            url = url.replace("_SPEC_", species_name.replace(" ", "+"))
        url = url.replace("_REPL_", self.xrid)
        return url

    specific_url = property(_get_url)
