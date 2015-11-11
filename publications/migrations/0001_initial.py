# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Publication'
        db.create_table(u'publications_publication', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('pmid', self.gf('django.db.models.fields.IntegerField')(unique=True, null=True)),
            ('title', self.gf('django.db.models.fields.TextField')()),
            ('authors', self.gf('django.db.models.fields.TextField')()),
            ('date', self.gf('django.db.models.fields.DateField')()),
            ('journal', self.gf('django.db.models.fields.TextField')()),
            ('volume', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('pages', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('issue', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'publications', ['Publication'])


    def backwards(self, orm):
        # Deleting model 'Publication'
        db.delete_table(u'publications_publication')


    models = {
        u'publications.publication': {
            'Meta': {'object_name': 'Publication'},
            'authors': ('django.db.models.fields.TextField', [], {}),
            'date': ('django.db.models.fields.DateField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'issue': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'journal': ('django.db.models.fields.TextField', [], {}),
            'pages': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'pmid': ('django.db.models.fields.IntegerField', [], {'unique': 'True', 'null': 'True'}),
            'title': ('django.db.models.fields.TextField', [], {}),
            'volume': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['publications']