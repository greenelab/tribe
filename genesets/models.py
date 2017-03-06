from django.db import models
from django.template.defaultfilters import slugify

from django.contrib.auth.models import User
from organisms.models import Organism
from taggit.managers import TaggableManager

# Import and set logger
import logging
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class Geneset(models.Model):
    """
    The class 'Geneset' extends Model class in Django.
    Genesets are created by users to save sets of genes that are
    linked in certain processes or pathways. Through versioning
    (see versions/models.py), users can add or subtract genes to
    their gene set and save the updated versions of their sets.
    Users can create as many genesets as they desire.

    For more information on Djando models, see:
    https://docs.djangoproject.com/en/dev/topics/db/models/

    For more information on Django model fields, see:
    https://docs.djangoproject.com/en/dev/ref/models/fields/
    """
    creator = models.ForeignKey(User)
    title = models.TextField()
    organism = models.ForeignKey(Organism)
    abstract = models.TextField(null=True)

    # A 'slug' is a url-friendly label for an object in django (meaning it only
    # contains letters, numbers, underscores, and hyphens.
    # For more information, see:
    # http://stackoverflow.com/questions/427102/what-is-a-slug-in-django
    slug = models.SlugField(help_text="Slugified title field", max_length=75)

    # If true, gene set will be read-accessible to all other users.
    # Other users can fork a new gene set off of gene sets that are public.
    public = models.BooleanField(default=False)

    deleted = models.BooleanField(default=False)
    fork_of = models.ForeignKey('self', editable=False, null=True)
    tags = TaggableManager()

    # Number of genes in the geneset's tip version
    tip_item_count = models.IntegerField(null=True)

    def _get_tags(self):
        logger.debug("Calling _get_tags() function for geneset %s", self)
        return self.tags.all()
    tag_prop = property(_get_tags)

    def get_tip(self):
        logger.debug("Calling get_tip() function for geneset %s", self)
        vers = self.version_set.order_by('-commit_date')[:1]
        if not vers.count():
            return None
        else:
            return vers[0]

    def save(self, *args, **kwargs):
        """
        Extends save method of Django models to automatically create a
        slug for each new gene set as it is saved in the database for
        the first time. For more information on overriding methods, see:
        https://docs.djangoproject.com/en/dev/db/models/#overriding-model-methods
        """
        logger.debug("Calling save() function for geneset %s", self)
        if not self.id:
            slug = self.slug
            if not slug:
                self.slug = slugify(self.title)[:75]
        return super(Geneset, self).save(*args, **kwargs)

    def __unicode__(self):
        """
        __unicode__ in django explained:
        https://docs.djangoproject.com/en/dev/ref/models/instances/#unicode
        """
        return self.title

    class Meta:
        ordering = ['pk']

        # This will make unique URLs for gene sets and their creators possible.
        unique_together = ('slug', 'creator')
