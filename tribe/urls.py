from django.conf.urls import patterns, include, url
from django.views.generic import TemplateView
from django.views.decorators.csrf import ensure_csrf_cookie
from django.conf import settings

from tastypie.api import Api

from organisms.api import OrganismResource
from genes.api import GeneResource
from genes.api import CrossRefResource
from genes.api import CrossRefDBResource

from genesets.api.resources import UserResource
from genesets.api.resources import GenesetResource
from genesets.api.resources import VersionResource
from genesets.api.resources import PublicationResource

v1_api = Api()
v1_api.register(UserResource())
v1_api.register(OrganismResource())
v1_api.register(GeneResource())
v1_api.register(CrossRefResource())
v1_api.register(CrossRefDBResource())
v1_api.register(GenesetResource())
v1_api.register(VersionResource())
v1_api.register(PublicationResource())

urlpatterns = patterns('',
    url(r'^$',
        ensure_csrf_cookie(TemplateView.as_view(template_name="index.html")),
        {'ga_code': settings.GA_CODE}, name='home'),

    (r'^api/', include(v1_api.urls)),
    (r'^accounts/', include('allauth.urls')),
    (r'^accounts/', include('profiles.urls')),

    # OAuth2 provider urls:
    url(r'^oauth2/', include('oauth2_provider.urls',
                             namespace='oauth2_provider')),

    # All other urls are handled through AngularJS and 'ui-router'
    # in the interface.

)

def handler500(request):
   """
   500 error handler which includes "request" in the context.

   Templates: '500.html'
   Context: None
   """
   from django.template import Context, loader
   from django.http import HttpResponseServerError

   t = loader.get_template('500.html') # 500.html template needs to be created
   return HttpResponseServerError(t.render(Context({
       'request': request,
   })))
