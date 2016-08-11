# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Share'
        db.create_table(u'collaborations_share', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('from_user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='share_from_user', to=orm['auth.User'])),
            ('to_user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='share_to_user', to=orm['auth.User'])),
            ('geneset', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['genesets.Geneset'])),
        ))
        db.send_create_signal(u'collaborations', ['Share'])

        # Adding unique constraint on 'Share', fields ['from_user', 'to_user', 'geneset']
        db.create_unique(u'collaborations_share', ['from_user_id', 'to_user_id', 'geneset_id'])

        # Adding model 'Collaboration'
        db.create_table(u'collaborations_collaboration', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('from_user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='from_users', to=orm['auth.User'])),
            ('to_user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='to_users', to=orm['auth.User'])),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal(u'collaborations', ['Collaboration'])

        # Adding unique constraint on 'Collaboration', fields ['from_user', 'to_user']
        db.create_unique(u'collaborations_collaboration', ['from_user_id', 'to_user_id'])


    def backwards(self, orm):
        # Removing unique constraint on 'Collaboration', fields ['from_user', 'to_user']
        db.delete_unique(u'collaborations_collaboration', ['from_user_id', 'to_user_id'])

        # Removing unique constraint on 'Share', fields ['from_user', 'to_user', 'geneset']
        db.delete_unique(u'collaborations_share', ['from_user_id', 'to_user_id', 'geneset_id'])

        # Deleting model 'Share'
        db.delete_table(u'collaborations_share')

        # Deleting model 'Collaboration'
        db.delete_table(u'collaborations_collaboration')


    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'collaborations': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'collaborators'", 'symmetrical': 'False', 'through': u"orm['collaborations.Collaboration']", 'to': u"orm['auth.User']"}),
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Group']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Permission']"}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'collaborations.collaboration': {
            'Meta': {'unique_together': "(('from_user', 'to_user'),)", 'object_name': 'Collaboration'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'from_user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'from_users'", 'to': u"orm['auth.User']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'to_user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'to_users'", 'to': u"orm['auth.User']"})
        },
        u'collaborations.share': {
            'Meta': {'unique_together': "(('from_user', 'to_user', 'geneset'),)", 'object_name': 'Share'},
            'from_user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'share_from_user'", 'to': u"orm['auth.User']"}),
            'geneset': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['genesets.Geneset']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'to_user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'share_to_user'", 'to': u"orm['auth.User']"})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'genesets.geneset': {
            'Meta': {'ordering': "['pk']", 'unique_together': "(('slug', 'creator'),)", 'object_name': 'Geneset'},
            'abstract': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"}),
            'deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'fork_of': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['genesets.Geneset']", 'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'organism': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['organisms.Organism']"}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '75'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '75'})
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

    complete_apps = ['collaborations']