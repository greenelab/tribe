# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding index on 'Publication', fields ['pmid']
        db.create_index(u'publications_publication', ['pmid'])


    def backwards(self, orm):
        # Removing index on 'Publication', fields ['pmid']
        db.delete_index(u'publications_publication', ['pmid'])


    models = {
        u'publications.publication': {
            'Meta': {'object_name': 'Publication'},
            'authors': ('django.db.models.fields.TextField', [], {}),
            'date': ('django.db.models.fields.DateField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'issue': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'journal': ('django.db.models.fields.TextField', [], {}),
            'pages': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'pmid': ('django.db.models.fields.IntegerField', [], {'unique': 'True', 'null': 'True', 'db_index': 'True'}),
            'title': ('django.db.models.fields.TextField', [], {}),
            'volume': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['publications']