# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Gene'
        db.create_table(u'genes_gene', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('entrezid', self.gf('django.db.models.fields.IntegerField')(unique=True, null=True, db_index=True)),
            ('systematic_name', self.gf('django.db.models.fields.CharField')(max_length=32, db_index=True)),
            ('standard_name', self.gf('django.db.models.fields.CharField')(max_length=32, null=True, db_index=True)),
            ('description', self.gf('django.db.models.fields.TextField')()),
            ('organism', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['organisms.Organism'])),
            ('aliases', self.gf('django.db.models.fields.TextField')()),
            ('obsolete', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('weight', self.gf('django.db.models.fields.FloatField')(default=1)),
        ))
        db.send_create_signal(u'genes', ['Gene'])

        # Adding model 'CrossRefDB'
        db.create_table(u'genes_crossrefdb', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=64, db_index=True)),
            ('url', self.gf('django.db.models.fields.URLField')(max_length=200)),
        ))
        db.send_create_signal(u'genes', ['CrossRefDB'])

        # Adding model 'CrossRef'
        db.create_table(u'genes_crossref', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('crossrefdb', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['genes.CrossRefDB'])),
            ('gene', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['genes.Gene'])),
            ('xrid', self.gf('django.db.models.fields.CharField')(max_length=32)),
        ))
        db.send_create_signal(u'genes', ['CrossRef'])


    def backwards(self, orm):
        # Deleting model 'Gene'
        db.delete_table(u'genes_gene')

        # Deleting model 'CrossRefDB'
        db.delete_table(u'genes_crossrefdb')

        # Deleting model 'CrossRef'
        db.delete_table(u'genes_crossref')


    models = {
        u'genes.crossref': {
            'Meta': {'object_name': 'CrossRef'},
            'crossrefdb': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['genes.CrossRefDB']"}),
            'gene': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['genes.Gene']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'xrid': ('django.db.models.fields.CharField', [], {'max_length': '32'})
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
            'URL_slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50'}),
            'common_name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '60'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'scientific_name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '60'}),
            'taxonomy_id': ('django.db.models.fields.PositiveIntegerField', [], {'unique': 'True', 'db_index': 'True'})
        }
    }

    complete_apps = ['genes']