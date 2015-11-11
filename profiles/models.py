from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    user = models.OneToOneField(User)
    temporary_acct = models.BooleanField(default=False)
    institution    = models.CharField(max_length=200)

    # __unicode__ in django explained: https://docs.djangoproject.com/en/dev/ref/models/instances/#unicode
    def __unicode__(self):
        profile_name = "Profile for user: " + str(self.user.username) 
        return profile_name

