from django.db import models
from django.utils import timezone
from uuidfield import UUIDField
from django.template.defaultfilters import slugify

from django.contrib.auth.models import User
from organisms.models import Organism
from genes.models import Gene
from taggit.managers import TaggableManager

"""
The class 'Geneset' is a Django model constructor, which is the blueprint for the information that will be stored
in the database for each 'geneset' instance. Users create and save sets of genes that are linked in certain
processes or pathways.  Through versioning (see versions/models.py) users can add or subtract genes in their set
and save the updated versions of their sets.  Users can build many different gene sets.
For more information on Djando models, see: https://docs.djangoproject.com/en/dev/topics/db/models/
For more information on Django model fields, see: https://docs.djangoproject.com/en/dev/ref/models/fields/
"""

class Geneset(models.Model):
    creator     = models.ForeignKey(User, help_text="Creator of the gene set.")
    title       = models.TextField(help_text="Title of gene set assigned by gene set author.")
    organism    = models.ForeignKey(Organism, help_text="The organism the genes in this set belong to.")
    abstract    = models.TextField(null=True)
    slug        = models.SlugField(help_text="Slugified title field", max_length=75)
                                # A 'slug' is a label for an object in django, which only
                                  # contains letters, numbers, underscores, and hyphens, thus making it URL-usable. For more
                                  # information, see: http://stackoverflow.com/questions/427102/what-is-a-slug-in-django
    public   = models.BooleanField(default=False, help_text="Do you want other users to have read-access to this gene set?")
                                  # If true, gene set will be read-accessible to other users.  No gene sets are write-accessible by
                                  # other than the author. Other users can fork a new gene set off of gene sets that are public.
    deleted  = models.BooleanField(default=False, help_text="Do you want to mark this gene set as 'deleted'?")
    fork_of  = models.ForeignKey('self', editable=False, null=True, help_text="Stores what gene set this set is a fork of, if any.")
    tags     = TaggableManager()
    tip_item_count = models.IntegerField(null=True, help_text="Holds how many items (e.g. genes) are saved in the tip version of this Geneset.")

    def _get_tags(self):
        return self.tags.all()
    tag_prop = property(_get_tags)

    def get_tip(self):
        vers = self.version_set.order_by('-commit_date')[:1]
        if not vers.count():
            return None
        else:
            return vers[0]

    def save(self, *args, **kwargs):
    # Extends save method of Django models to automatically create a slug for each new
    # gene set as it is saved in the database for the first time. For more information on overriding methods,
    # see: https://docs.djangoproject.com/en/dev/db/models/#overriding-model-methods
        if not self.id:
            slug = self.slug
            if not slug:
                self.slug = slugify(self.title)[:75]
        return super(Geneset, self).save(*args, **kwargs)

    # __unicode__ in django explained: https://docs.djangoproject.com/en/dev/ref/models/instances/#unicode
    def __unicode__(self):
        return self.title

    class Meta:
       ordering = ['pk']
       unique_together = ('slug', 'creator') # This will make unique URLs for gene sets and their creators possible.