
from django.db import models

class Publication(models.Model):
    pmid = models.IntegerField(null=True, unique=True, db_index=True)
    title = models.TextField()
    authors = models.TextField()
    date = models.DateField()
    journal = models.TextField()
    volume = models.TextField(blank=True, null=True)
    pages = models.TextField(blank=True, null=True)
    issue = models.TextField(blank=True, null=True)
