"""
Management utility to create users.
"""

import re
from optparse import make_option
from django.contrib.auth import get_user_model
from django.core import exceptions
from django.core.management.base import BaseCommand, CommandError
from django.utils.translation import ugettext as _

RE_VALID_USERNAME = re.compile('[\w.@+-]+$')

EMAIL_RE = re.compile(
    r"(^[-!#$%&'*+/=?^_`{}|~0-9A-Z]+(\.[-!#$%&'*+/=?^_`{}|~0-9A-Z]+)*"  # dot-atom
    r'|^"([\001-\010\013\014\016-\037!#-\[\]-\177]|\\[\001-\011\013\014\016-\177])*"' # quoted-string
    r')@(?:[A-Z0-9-]+\.)+[A-Z]{2,6}$', re.IGNORECASE)  # domain

def is_valid_email(value):
    if not EMAIL_RE.search(value):
        raise exceptions.ValidationError(_('Enter a valid e-mail address.'))

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--username', dest='username', default=None,
            help='Specifies the username.'),
        make_option('--email', dest='email', default=None,
            help='Specifies the email address.'),
    )
    help = 'Used to create a user.'

    def handle(self, *args, **options):
        username = options.get('username', None)
        email = options.get('email', None)
        verbosity = int(options.get('verbosity', 1))

        # Do quick and dirty validation if --noinput
        if not username or not email:
            raise CommandError("You must use --username and --email.")
        if not RE_VALID_USERNAME.match(username):
            raise CommandError("Invalid username. Use only letters, digits, and underscores")
        try:
            is_valid_email(email)
        except exceptions.ValidationError:
            raise CommandError("Invalid email address.")

        user = None
        try:
            user = get_user_model().objects.get(username=username)
            user.email = email
        except get_user_model().DoesNotExist:
            user = get_user_model().objects.create_user(username, email, None)
        print("User created successfully.")
