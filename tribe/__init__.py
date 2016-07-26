"""
The next few lines of code are copied from Celery
documentation for working with Django:
http://docs.celeryproject.org/en/latest/django/first-steps-with-django.html
"""
from __future__ import absolute_import

# This will make sure the app is always imported when
# Django starts so that shared_task will use this app.
from .celery import app as celery_app
