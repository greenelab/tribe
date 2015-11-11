# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding index on 'CrossRef', fields ['xrid']
        db.create_index(u'genes_crossref', ['xrid'])


    def backwards(self, orm):
        # Removing index on 'CrossRef', fields ['xrid']
        db.delete_index(u'genes_crossref', ['xrid'])


    models = {
        u'genes.crossref': {
            'Meta': {'object_name': 'CrossRef'},
            'crossrefdb': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['genes.CrossRefDB']"}),
            'gene': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['genes.Gene']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'xrid': ('django.db.models.fields.CharField', [], {'max_length': '32', 'db_index': 'True'})
        },
        u'genes.crossrefdb': {
            'Meta': {'object_name': 'CrossRefDB'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '64', 'db_index': 'True'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200'})
        },
        u'genes.gene': {
            'Meta': {'object_name': 'Gene'},
            'aliases': ('django.db.models.fields.TextField', [], {}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'entrezid': ('django.db.models.fields.IntegerField', [], {'unique': 'True', 'null': 'True', 'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'obsolete': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'organism': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['organisms.Organism']"}),
            'standard_name': ('django.db.models.fields.CharField', [], {'max_length': '32', 'null': 'True', 'db_index': 'True'}),
            'systematic_name': ('django.db.models.fields.CharField', [], {'max_length': '32', 'db_index': 'True'}),
            'weight': ('django.db.models.fields.FloatField', [], {'default': '1'})
        },
        u'organisms.organism': {
            'Meta': {'object_name': 'Organism'},
            'common_name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '60'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'scientific_name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '60'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50'}),
            'taxonomy_id': ('django.db.models.fields.PositiveIntegerField', [], {'unique': 'True', 'db_index': 'True'})
        }
    }

    complete_apps = ['genes']