"""
File largely based on sample celery.py file from documentation
for working with Celery and Django here:
http://docs.celeryproject.org/en/latest/django/first-steps-with-django.html
"""
from __future__ import absolute_import

import os

from celery import Celery

from django.conf import settings

# Set the default Django settings module for the 'celery' program
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tribe.settings')

app = Celery('tribe')

# Using a string here means the worker will not have to
# pickle the object when using Windows.
app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

app.conf.update(
    CELERY_RESULT_BACKEND='djcelery.backends.database:DatabaseBackend',
    CELERY_ACCEPT_CONTENT=['pickle', 'json', 'yaml']
)


@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))
