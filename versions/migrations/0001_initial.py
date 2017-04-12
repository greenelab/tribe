# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import versions.models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('genesets', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Version',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('ver_hash', models.CharField(help_text=b'A 40-character sha1 hash that identifies this version.', max_length=40, db_index=True)),
                ('description', models.TextField(null=True)),
                ('commit_date', models.DateTimeField(auto_now_add=True)),
                ('annotations', versions.models.FrozenSetField(help_text=b"Holds gene PK's.", editable=False)),
                ('creator', models.ForeignKey(help_text=b'Must be the same as the author of the gene set.', to=settings.AUTH_USER_MODEL)),
                ('geneset', models.ForeignKey(help_text=b'The gene set this will be a new version of.', to='genesets.Geneset')),
                ('parent', models.ForeignKey(editable=False, to='versions.Version', help_text=b'Previous version in gene set line. Is null if it is the first version.', null=True)),
            ],
            options={
                'ordering': ['geneset', 'commit_date'],
            },
        ),
        migrations.AlterUniqueTogether(
            name='version',
            unique_together=set([('geneset', 'ver_hash')]),
        ),
    ]
