# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('organisms', '__first__'),
    ]

    operations = [
        migrations.CreateModel(
            name='CrossRef',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('xrid', models.CharField(max_length=32, db_index=True)),
            ],
        ),
        migrations.CreateModel(
            name='CrossRefDB',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=64, db_index=True)),
                ('url', models.URLField()),
            ],
            options={
                'verbose_name': 'Cross Reference Database',
            },
        ),
        migrations.CreateModel(
            name='Gene',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('entrezid', models.IntegerField(unique=True, null=True, db_index=True)),
                ('systematic_name', models.CharField(max_length=32, db_index=True)),
                ('standard_name', models.CharField(max_length=32, null=True, db_index=True)),
                ('description', models.TextField()),
                ('aliases', models.TextField()),
                ('obsolete', models.BooleanField(default=False)),
                ('weight', models.FloatField(default=1)),
                ('organism', models.ForeignKey(to='organisms.Organism')),
            ],
        ),
        migrations.AddField(
            model_name='crossref',
            name='crossrefdb',
            field=models.ForeignKey(to='genes.CrossRefDB'),
        ),
        migrations.AddField(
            model_name='crossref',
            name='gene',
            field=models.ForeignKey(to='genes.Gene'),
        ),
    ]
