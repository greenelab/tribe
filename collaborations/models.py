
from django.db import models
from django.contrib.auth.models import User
from genesets.models import Geneset


class Share(models.Model):

    """
    Model to allow users to work together on a single geneset.

    The class 'Share' extends the Model class in Django (see organisms/models.py), and serves
    as a Django model constructor, which will create a table for shares in the database.
    For more information, see: https://docs.djangoproject.com/en/1.5/topics/db/models/
    Shares allow users to work together on a specific geneset.
    """

    from_user = models.ForeignKey(User, related_name="share_from_user")  # User that invited
    to_user = models.ForeignKey(User, related_name="share_to_user")  # User that was invited
    geneset = models.ForeignKey(Geneset)

    class Meta:
        unique_together = ('from_user', 'to_user', 'geneset')

    def __unicode__(self):
        # __unicode__ in django explained: https://docs.djangoproject.com/en/dev/ref/models/instances/#unicode
        return 'Invite from ' + self.from_user.username + ' to ' + self.to_user.username + ' to share ' + self.geneset.title + '.'


class Collaboration(models.Model):

    """
    Class to allow users to collaborate.

    The class 'Collaboration' extends the Model class in Django (see organisms/models.py), and
    serves as a Django model constructor, which will create a table for Collaborations in the
    database. For more information, see: https://docs.djangoproject.com/en/1.5/topics/db/models/
    As opposed to share, which is specific to a geneset, Collaboration is broader and indicates
    which users can be asked to share a specific geneset. Only users with a pre-existing
    collaboration can be asked to share a geneset. Breaking an overall collaboration removes the
    ability to invite that user to share, but does not remove existing shares.

    Collaboration and associated managers are heavily based on django-relationships:
        https://github.com/coleifer/django-relationships
    """

    from_user = models.ForeignKey(User, related_name="from_users")
    to_user = models.ForeignKey(User, related_name="to_users")
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('from_user', 'to_user')
