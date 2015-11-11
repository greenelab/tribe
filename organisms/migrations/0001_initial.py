# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Organism'
        db.create_table(u'organisms_organism', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('taxonomy_id', self.gf('django.db.models.fields.PositiveIntegerField')(unique=True, db_index=True)),
            ('common_name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=60)),
            ('scientific_name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=60)),
            ('slug', self.gf('django.db.models.fields.SlugField')(unique=True, max_length=50)),
        ))
        db.send_create_signal(u'organisms', ['Organism'])


    def backwards(self, orm):
        # Deleting model 'Organism'
        db.delete_table(u'organisms_organism')


    models = {
        u'organisms.organism': {
            'Meta': {'object_name': 'Organism'},
            'common_name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '60'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'scientific_name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '60'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50'}),
            'taxonomy_id': ('django.db.models.fields.PositiveIntegerField', [], {'unique': 'True', 'db_index': 'True'})
        }
    }

    complete_apps = ['organisms']