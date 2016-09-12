from django.conf.urls import patterns, include, url
from . import views

urlpatterns = patterns('',
    url(r'^create_temporary/$', views.create_temporary_acct, name = 'create_temporary'),
    url(r'^upgrade_to_full_account', views.convert_to_full_acct, name='convert_to_full_acct'),
    #url(r'^add_profile/$', views.add_profile, name = 'add_profile'),
)
