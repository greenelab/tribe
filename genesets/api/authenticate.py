import logging
import json

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.utils import timezone
from tastypie.authentication import Authentication


"""
This is a simple OAuth 2.0 authentication model for tastypie

Copied nearly verbatim from amrox's example
- https://github.com/amrox/django-tastypie-two-legged-oauth

Dependencies (one of these):
- django-oauth-toolkit: https://github.com/evonove/django-oauth-toolkit
- django-oauth2-provider: https://github.com/caffeinehit/django-oauth2-provider
"""

log = logging.getLogger('tastypie_oauth')


class OAuthError(RuntimeError):
    """Generic exception class."""
    def __init__(self, message='OAuth error occured.'):
        self.message = message


class OAuth20Authentication(Authentication):
    """
    OAuth authenticator.

    This Authentication method checks for a provided HTTP_AUTHORIZATION
    and looks up to see if this is a valid OAuth Access Token
    """
    def __init__(self, realm='API'):
        self.realm = realm

    def is_authenticated(self, request, **kwargs):
        """
        Verify 2-legged oauth request. Parameters accepted as
        values in "Authorization" header, or as a GET request parameter,
        or in a POST body.
        """
        log.info("OAuth20Authentication")

        try:    # This is here not because of the GET.get and POST.get keys, but rather
                # in case the verify_access_token throws an exception

            key = request.GET.get('oauth_consumer_key')

            if not key:
                for header in ['Authorization', 'HTTP_AUTHORIZATION']:
                    auth_header_value = request.META.get(header)
                    if auth_header_value:
                        key = auth_header_value.split(' ')[1]
                        break

            if not key and request.method == 'POST':
                if request.META.get('CONTENT_TYPE') == 'application/json':
                    decoded_body = request.body.decode('utf8')
                    key = json.loads(decoded_body)['oauth_consumer_key']

            if not key:
                log.info('OAuth20Authentication. No consumer_key found.')
                request.user = AnonymousUser()
                return True     # The important thing is to return True, otherwise we get a 401-Unauthorized response

            """
            If verify_access_token() does not pass, it will raise an error
            """
            token = verify_access_token(key)

            if (token == 'AccessToken has expired.'):
                request.META['oauth_token_expired'] = True
                request.user = AnonymousUser()
                return False

            # If OAuth authentication is successful, set the request user to
            # the token user for authorization
            request.user = token.user

            # If OAuth authentication is successfu, set oauth_consumer_key on
            # request in case we need it later
            request.META['oauth_consumer_key'] = key

            return True

        except KeyError:
            log.exception("Error in OAuth20Authentication.")
            request.user = AnonymousUser()
            return False

        except Exception:
            log.exception("Error in OAuth20Authentication.")
            request.user = AnonymousUser
            return False


def verify_access_token(key):
    # Import the AccessToken model (in this case it will come from django-oauth-toolkit's AccessToken)
    model = settings.OAUTH_ACCESS_TOKEN_MODEL
    try:
        model_parts = model.split('.')
        module_path = '.'.join(model_parts[:-1])
        module = __import__(module_path, globals(), locals(), ['AccessToken'])
        AccessToken = getattr(module, model_parts[-1])

    except ImportError:
        raise OAuthError("Error importing AccessToken model: %s" % model) 


    # Check if key is in AccessToken key
    try:
        token = AccessToken.objects.get(token=key)

        # Check if token has expired
        if token.expires < timezone.now():
            log.info('AccessToken has expired.')
            return 'AccessToken has expired.'

        else:
            log.info('Valid access')
            return token

    except AccessToken.DoesNotExist, e:
        raise OAuthError("AccessToken not found at all")
