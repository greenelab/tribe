# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings
import taggit.managers


class Migration(migrations.Migration):

    dependencies = [
        ('taggit', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('organisms', '__first__'),
    ]

    operations = [
        migrations.CreateModel(
            name='Geneset',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.TextField(help_text=b'Title of gene set assigned by gene set author.')),
                ('abstract', models.TextField(null=True)),
                ('slug', models.SlugField(help_text=b'Slugified title field', max_length=75)),
                ('public', models.BooleanField(default=False, help_text=b'Do you want other users to have read-access to this gene set?')),
                ('deleted', models.BooleanField(default=False, help_text=b"Do you want to mark this gene set as 'deleted'?")),
                ('tip_item_count', models.IntegerField(help_text=b'Holds how many items (e.g. genes) are saved in the tip version of this Geneset.', null=True)),
                ('creator', models.ForeignKey(help_text=b'Creator of the gene set.', to=settings.AUTH_USER_MODEL)),
                ('fork_of', models.ForeignKey(editable=False, to='genesets.Geneset', help_text=b'Stores what gene set this set is a fork of, if any.', null=True)),
                ('organism', models.ForeignKey(help_text=b'The organism the genes in this set belong to.', to='organisms.Organism')),
                ('tags', taggit.managers.TaggableManager(to='taggit.Tag', through='taggit.TaggedItem', help_text='A comma-separated list of tags.', verbose_name='Tags')),
            ],
            options={
                'ordering': ['pk'],
            },
        ),
        migrations.AlterUniqueTogether(
            name='geneset',
            unique_together=set([('slug', 'creator')]),
        ),
    ]
