from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import MultipleObjectsReturned
from genes.models import Gene, CrossRef
from genesets.models import Geneset
from versions.exceptions import VersionContainsNoneGene, NoParentVersionSpecified
from publications.models import Publication
from publications.utils import load_pmids

from django.utils import timezone
from django.db import connection
import cPickle as pickle # For more information on pickling, see: http://docs.python.org/2/library/pickle.html
import hashlib # See: http://docs.python.org/2/library/hashlib.html

# Import and set logger
import logging
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

"""
The class 'Version' is a Django model constructor, which is the blueprint for the information that will be stored
in the database for each 'version' instance. Users create and save sets of genes that are linked in certain
processes or pathways (see genesets/models.py). Through versioning, users can add or subtract genes in their set
and save the updated versions of their sets. The genes in each version of the set are stored as a FrozenSetField
(which pickles a python frozenset([])) of gene Primary Keys (see genes/models.py).
For more information on Djando models, see: https://docs.djangoproject.com/en/dev/topics/db/models/
For more information on Django model fields, see: https://docs.djangoproject.com/en/dev/ref/models/fields/
"""

class FrozenSetField(models.TextField):
# For more information on writing custom model fields, see: https://docs.djangoproject.com/en/1.5/howto/custom-model-fields/

    description = "Extends TextField (from Django model fields) to store the genes in the set as a pickled set of primary keys."

    __metaclass__ = models.SubfieldBase
    # see: https://docs.djangoproject.com/en/1.5/howto/custom-model-fields/#the-subfieldbase-metaclass

    def to_python(self, value):
    # This method converts the data stored in the database into a python object. In this case, it is a pickled data stream.
    # See: https://docs.djangoproject.com/en/1.5/howto/custom-model-fields/#django.db.models.Field.to_python
        if isinstance(value, basestring) and value:
            value = pickle.loads(str(value))
        elif not value:
            return frozenset()
        return value

    def get_prep_value(self, value):
    # The reverse of to_python. This 'pickles' the frozenset.
    # See: https://docs.djangoproject.com/en/1.5/howto/custom-model-fields/#django.db.models.Field.get_prep_value
        if value is None:
            return None
        value = frozenset(value)
        return pickle.dumps(value)

    def value_to_string(self, obj):
    # Used by serializers to output the data in this field as a string.  See:
    # https://docs.djangoproject.com/en/1.5/howto/custom-model-fields/#converting-field-data-for-serialization
        value = self._get_val_from_obj(obj)
        return self.get_db_prep_value(value, connection)

    def south_field_triple(self):  # Returns a suitable description of this field for South (which handles DB migrations).
        from south.modelsinspector import introspector
        field_class = "django.db.models.fields.TextField"
        args, kwargs = introspector(self)
        return (field_class, args, kwargs)


class Version(models.Model):
    geneset     = models.ForeignKey(Geneset, help_text="The gene set this will be a new version of.")
    creator     = models.ForeignKey(User, help_text="Must be the same as the author of the gene set.")
    ver_hash    = models.CharField(db_index=True, max_length=40, help_text="A 40-character sha1 hash that identifies this version.")
    description = models.TextField(null=True)
    commit_date = models.DateTimeField(auto_now_add=True, editable=False)
    parent      = models.ForeignKey('self', editable=False, null=True, help_text="Previous version in gene set line. Is null if it is the first version.")
    annotations = FrozenSetField(editable = False, help_text="Holds gene PK's.")
    # FrozenSetField defined in the class above.

    def save(self, *args, **kwargs):
        """
        Extends save method of Django models to automatically do some checks
        (checks to see if the user should have passed a parent version and if
        publications are sent without genes), and creates a sha1 ver_hash for
        each new version as it is saved in the database for the first time.
        For more information on overriding methods, see:
        https://docs.djangoproject.com/en/dev/topics/db/models/#overriding-model-methods
        """

        existing_versions_num = self.geneset.version_set.count()

        if (existing_versions_num != 0) and (self.parent is None):
            raise NoParentVersionSpecified

        if not self.ver_hash:
            a = None
            if not self.parent:
                a = hashlib.sha1("")
            else:
                a = hashlib.sha1(self.parent.ver_hash)
            a.update(str(self.annotations))
            self.ver_hash = a.hexdigest()

        different_genes = set()
        for annotation in self.annotations:
            if annotation[0] is None:
                raise VersionContainsNoneGene
            else:
                different_genes.add(annotation[0])
        self.geneset.tip_item_count = len(different_genes)
        self.geneset.save()

        return super(Version, self).save(*args, **kwargs)

    def format_annotations(self, annots, xrdb, full_pubs, organism=None):
        """
        xrdb is the type of gene identifier that the annotations are sent as
        """
        formatted_for_db_annotations = set()
        genes_not_found = set()
        multiple_genes_found = set()
        pubs_not_loaded = set()
        annotation_dict = {}

        if organism is not None:
            gene_objects_manager = Gene.objects.filter(
                organism__scientific_name=organism)
        else:
            gene_objects_manager = Gene.objects

        for key in annots:
            # This loop validates the annotations and gets the actual
            # gene/publication objects
            try:
                if (xrdb is None):
                    gene_obj = gene_objects_manager.get(id=key)
                elif (xrdb == 'Entrez'):
                    gene_obj = gene_objects_manager.get(entrezid=key)
                elif (xrdb == 'Symbol'):
                    try:
                        gene_obj = gene_objects_manager.get(
                            standard_name=key)
                    except Gene.DoesNotExist:
                        gene_obj = gene_objects_manager.get(
                            systematic_name=key)
                else:
                    xref_obj = CrossRef.objects.filter(
                            crossrefdb__name=xrdb).get(xrid=key)
                    gene_obj = xref_obj.gene

                pubs = set()
                for publication in annots[key]:

                    if full_pubs:
                        # The full publication database objects were sent
                        pubs.add(publication['id'])
                    else:
                        # Only the pubmed IDs were sent
                        pubmed_id = publication
                        try:
                            # Check to see if publication is in the database
                            pub_obj = Publication.objects.get(pmid=pubmed_id)
                        except Publication.DoesNotExist:
                            # If it doesn't exist in the database, load it
                            logger.info("Pubmed ID %s did not exist in the "
                                        "database. Loading it now.", pubmed_id)
                            load_pmids([pubmed_id, ])
                            try:
                                # Try again to see if publication is now in
                                # the database
                                pub_obj = Publication.objects.get(pmid=pubmed_id)
                            except Publication.DoesNotExist:
                                # Pubmed id that was passed probably does not
                                # exist
                                logger.warning("Pubmed ID %s could not be "
                                               "loaded from Pubmed server. "
                                               "Saving it in version as None.",
                                               pubmed_id)
                                pubs_not_loaded.add(pubmed_id)
                                pub_obj = None
                        if pub_obj:
                            pubs.add(pub_obj.id)

                annotation_dict[gene_obj.pk] = pubs

            except (Gene.DoesNotExist, CrossRef.DoesNotExist):
                genes_not_found.add(key)

            except (MultipleObjectsReturned):
                multiple_genes_found.add(key)

        if annotation_dict:
            # if annotations (genes and publications) exist in the database:
            for key in annotation_dict:
                # The following statement is the pythonic way to check if the
                # set is not empty (i.e. there are publications for this gene)
                if annotation_dict[key]:
                    # There are publications for this gene - add them as tuples
                    # to formatted_for_db_annotations set.
                    for pub in annotation_dict[key]:
                        formatted_for_db_annotations.add((key, pub))
                else:
                    # There are no pubs for this gene
                    formatted_for_db_annotations.add((key, None))

            formatted_for_db_annotations = frozenset(formatted_for_db_annotations)

        return (formatted_for_db_annotations, genes_not_found, pubs_not_loaded,
                multiple_genes_found)

    # __unicode__ in django explained: https://docs.djangoproject.com/en/dev/ref/models/instances/#unicode
    def __unicode__(self):
        gs = str(self.geneset)
        verhash = str(self.ver_hash)
        v_hash  = verhash[:7]
        version_name = gs + "-" + v_hash
        return version_name # Returns the gene set this version is a part of and the first seven characters of hash.

    class Meta:
        # Order the versions of a gene set in chronological order.
        ordering = ['geneset', 'commit_date']

        # Each gene set must have different hashes for each version
        # to differentiate them.
        unique_together = ('geneset', 'ver_hash')
