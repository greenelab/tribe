# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('genesets', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Collaboration',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('from_user', models.ForeignKey(related_name='from_users', to=settings.AUTH_USER_MODEL)),
                ('to_user', models.ForeignKey(related_name='to_users', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Share',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('from_user', models.ForeignKey(related_name='share_from_user', to=settings.AUTH_USER_MODEL)),
                ('geneset', models.ForeignKey(to='genesets.Geneset')),
                ('to_user', models.ForeignKey(related_name='share_to_user', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='share',
            unique_together=set([('from_user', 'to_user', 'geneset')]),
        ),
        migrations.AlterUniqueTogether(
            name='collaboration',
            unique_together=set([('from_user', 'to_user')]),
        ),
    ]
