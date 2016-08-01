"""
Check to see if celery_haystack is installed. If it is, set up
celery app. If not, just pass.

The lines of code that import the celery app are copied
from the Celery documentation for working with Django:
http://docs.celeryproject.org/en/latest/django/first-steps-with-django.html

"""
from __future__ import absolute_import

try:
    import celery_haystack

    # This will make sure the app is always imported when
    # Django starts so that shared_task will use this app.
    from .celery import app as celery_app

except ImportError:
    pass
