# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('genesets', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='geneset',
            name='creator',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='geneset',
            name='deleted',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='geneset',
            name='fork_of',
            field=models.ForeignKey(editable=False, to='genesets.Geneset', null=True),
        ),
        migrations.AlterField(
            model_name='geneset',
            name='organism',
            field=models.ForeignKey(to='organisms.Organism'),
        ),
        migrations.AlterField(
            model_name='geneset',
            name='public',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='geneset',
            name='tip_item_count',
            field=models.IntegerField(null=True),
        ),
        migrations.AlterField(
            model_name='geneset',
            name='title',
            field=models.TextField(),
        ),
    ]
