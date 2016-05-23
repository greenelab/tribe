import re

from django.db import models
from django.core.exceptions import FieldError
from organisms.models import Organism

# Regular expressions to be matched in the methods of 'Gene'.
nonalpha = re.compile(r'[^a-zA-Z0-9]')
num = re.compile(r'[0-9]')


class Gene(models.Model):
    """
    The class 'Gene' extends the Model class in Django. For more information,
    see: https://docs.djangoproject.com/en/dev/topics/db/models/

    Genes will be added from an online database like 'Entrez', using the Django
    management commands (see management/commands/genes_load_geneinfo.py).
    """
    entrezid = models.IntegerField(null=True, db_index=True, unique=True)

    # Used for organisms like yeast.
    systematic_name = models.CharField(max_length=32, db_index=True)

    standard_name = models.CharField(max_length=32, null=True, db_index=True)

    # Description/full name of gene.
    description = models.TextField()

    # "organism" field contains the primary key of whichever organism
    # instance the gene belongs to.  For more info, see:
    # https://docs.djangoproject.com/en/dev/ref/models/fields/#django.db.models.ForeignKey
    organism = models.ForeignKey(Organism, null=False)

    # "aliases" stores a space-separated list of aliases.
    aliases = models.TextField()

    obsolete = models.BooleanField(default=False)

    # Weight used for search results, needed now that we allow genes with
    # identical symbols.
    weight = models.FloatField(default=1)

    # __unicode__ in django, explained at:
    # https://docs.djangoproject.com/en/dev/ref/models/instances/#unicode
    def __unicode__(self):
        if self.standard_name:
            return self.standard_name
        return self.systematic_name

    def wall_of_name(self):
        '''
        Appends identifiers for the different databases (such as Entrez id's)
        and returns them. Uses the CrossRef class below.
        '''
        names = [self.standard_name, self.systematic_name]
        names.extend([xref.xrid for xref in self.crossref_set.all()])
        for i in range(len(names)):
            names[i] = re.sub(nonalpha, '', names[i])
        return ' '.join(names) + ' ' + re.sub(num, '', self.standard_name)

    def save(self, *args, **kwargs):
        """
        Override save() method to make sure that standard_name and
        systematic_name won't be null or empty, or consist of only space
        characters (such as space, tab, new line, etc).
        """
        empty_std_name = False
        if not self.standard_name or self.standard_name.isspace():
            empty_std_name = True

        empty_sys_name = False
        if not self.systematic_name or self.systematic_name.isspace():
            empty_sys_name = True

        if empty_std_name and empty_sys_name:
            raise ValueError(
                "Both standard_name and systematic_name are empty")

        super(Gene, self).save(*args, **kwargs)  # Call the "real" save().


class CrossRefDB(models.Model):
    name = models.CharField(max_length=64, unique=True, db_index=True,
                            blank=False)
    url = models.URLField()

    def save(self, *args, **kwargs):
        """
        Extends save() method of Django models to check that the database name
        is not left blank.
        Note: 'blank=False' is only checked at a form-validation-stage. A test
        using Fixtureless that tries to randomly create a CrossRefDB with an
        empty string name would unintentionally break the test.
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
