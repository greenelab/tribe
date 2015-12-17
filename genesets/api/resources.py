"""
This file, resources.py, sets most of the parameters for how the information will be serialized from the database into
JavaScript Objects by the RESTful API (for documentation on this API, which is also written in Python, see:
http://django-tastypie.readthedocs.org/en/latest/).  However, what you need to know is that this API converts the database objects
into JavaScript objects and makes them available to the user interface (a JavaScript object for a gene set would look like this:
Gene set = {"title": "DNA damage repair set", "description": "First set, adding initial genes", "fork_of": null,
"id": 295, "public": true, "organism": { "scientific_name": "Homo sapiens", "taxonomy_id": 9606}, "user": "rene"}).
For more information on JavaScript Objects, see: http://www.w3schools.com/json/

"""

# Python imports
import logging
logger = logging.getLogger('genesets.api')
from copy import deepcopy

# Django imports
from django.db import IntegrityError
from django.db.models import Q  # Needed for complex database queries
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.middleware.csrf import _sanitize_token, constant_time_compare
from django.utils.http import same_origin
from django.conf import settings
from django.views.decorators.csrf import csrf_protect

# Tribe imports
from organisms.models import Organism
from genes.models import Gene, CrossRef
from genes.utils import translate_genes
from genesets.models import Geneset
from versions.models import Version
from versions.exceptions import VersionContainsNoneGene, NoParentVersionSpecified
from publications.models import Publication
from publications.utils import load_pmids
from collaborations.models import Collaboration, Share
from collaborations.utils import get_collaborators, get_invites, get_inviteds
from profiles.models import Profile


# Tastypie is the RESTful API which manages the JavaScript serialization
from tastypie.resources import ModelResource, ALL, ALL_WITH_RELATIONS
from tastypie import fields
from tastypie import http
from tastypie.authentication import BasicAuthentication, SessionAuthentication, MultiAuthentication
from tastypie.authorization import DjangoAuthorization, Authorization
from tastypie.exceptions import Unauthorized, BadRequest
from tastypie.http import HttpUnauthorized, HttpForbidden
from tastypie.serializers import Serializer
from tastypie.cache import SimpleCache
from tastypie.throttle import CacheDBThrottle

# Haystack imports - Haystack is the Python package that handles the gene search functionality in the server
from django.conf.urls import *
from django.http import Http404
from haystack.query import SearchQuerySet
from tastypie.utils import trailing_slash

# Resources needed for Tribe to be an OAuth2.0 provider
from authenticate import OAuth20Authentication

class UserAuthorization(Authorization):

    def read_list(self, object_list, bundle):
        return object_list.filter(id=bundle.request.user.id)  # Let the user only have read-access to themselves

    def read_detail(self, object_list, bundle):
        return bundle.obj == bundle.request.user

    def create_list(self, object_list, bundle):
        raise Unauthorized("New users can only be registered individually.")

    def create_detail(self, object_list, bundle):
        return True

    def update_list(self, object_list, bundle):
        raise Unauthorized("We're sorry, it is not possible to update.")

    def update_detail(self, object_list, bundle):
        raise Unauthorized("We're sorry, it is not possible to update.")

    def delete_list(self, object_list, bundle):
        raise Unauthorized("Sorry, deleting is not possible.")

    def delete_detail(self, object_list, bundle):
        raise Unauthorized("Sorry, deleting is not possible.")

#Returns only the username. For use with Genesets and Versions.
class BasicUserResource(ModelResource):
    username = fields.CharField(attribute='username')
    id       = fields.IntegerField(attribute='id')
    alt_username = fields.CharField()

    class Meta:
        queryset = User.objects.all()
        fields = ['username',]
        detail_uri_name = 'username'
        authorization = UserAuthorization() # Defined above

    def dehydrate_alt_username(self, bundle):
        # This method will check to see if the user is a temporary user.
        # If it is, username returned will be 'TemporaryUser', without
        # the number appended at the end

        user = bundle.obj
        username = bundle.obj.username
        try:
            temporary = Profile.objects.get(user=user).temporary_acct
        except ObjectDoesNotExist:
            temporary = None

        if (username[:13] == 'TemporaryUser') and (temporary == True):
            return 'TemporaryUser'
        else:
            return username



class EmailUserResource(ModelResource):
    username     = fields.CharField(attribute='username')
    email        = fields.CharField(attribute='email')
    class Meta:
        queryset = User.objects.all()
        fields = ['username', 'email', ]
        detail_uri_name = 'username'
        authorization = UserAuthorization()  # Defined above

class UserResource(ModelResource):
    id              = fields.IntegerField(attribute='id')
    email           = fields.CharField(attribute='email')
    username        = fields.CharField(attribute='username')
    first_name      = fields.CharField(attribute='first_name')
    last_name       = fields.CharField(attribute='last_name')
    collaborators   = fields.ToManyField(EmailUserResource, lambda bundle: get_collaborators(bundle.obj), null=True, full=True, full_detail=True)
    invites         = fields.ToManyField(EmailUserResource, lambda bundle: get_invites(bundle.obj), null=True, full=True, full_detail=True)
    inviteds        = fields.ToManyField(EmailUserResource, lambda bundle: get_inviteds(bundle.obj), null=True, full=True, full_detail=True)
    temporary       = fields.BooleanField(null=True)

    class Meta:
        queryset = User.objects.all()
        fields = ['id', 'email', 'username', 'first_name', 'last_name', 'collaborators', 'invites', 'invited']
        resource_name = 'user'
        authentication = MultiAuthentication(SessionAuthentication(), OAuth20Authentication())
        authorization = UserAuthorization() # Defined above
        filtering = {'username': ALL, 'id': ALL }
        allowed_methods = ['get', 'post']
        cache = SimpleCache()
        detail_uri_name = 'username'

        # Parameters for Throttle are 'throttle_at', 'timeframe' and 'expiration'
        # Default is throttling at 150 requests per 1 hour
        throttle = CacheDBThrottle()


    def alter_list_data_to_serialize(self, request, data):
        if (request.META.has_key('oauth_token_expired')):
            data['meta']['oauth_token_expired'] = True
        return data

    def alter_detail_data_to_serialize(self, request, data):
        if (request.META.has_key('oauth_token_expired')):
            data['meta']['oauth_token_expired'] = True
        return data

    # add URLs for collaboration
    def prepend_urls(self):
        return [
            url(r"^(?P<resource_name>%s)/invite%s$" % (self._meta.resource_name, trailing_slash()), self.wrap_view('add_invite'), name="api_add_invite"),
            url(r"^(?P<resource_name>%s)/reject%s$" % (self._meta.resource_name, trailing_slash()), self.wrap_view('reject_invite'), name="api_reject_invite"),
            url(r"^(?P<resource_name>%s)/login%s$" % (self._meta.resource_name, trailing_slash()), self.wrap_view('login'), name="api_login"),
            url(r"^(?P<resource_name>%s)/logout%s$" % (self._meta.resource_name, trailing_slash()), self.wrap_view('logout'), name="api_logout"),
        ]


    def login(self, request, **kwargs):
        self.method_check(request, allowed=['post'])
        self.throttle_check(request)

        data = self.deserialize(request, request.body, format=request.META.get('CONTENT_TYPE', 'application/json'))

        username = data.get('username', '')
        password = data.get('password', '')

        # Do authentication:
        user = authenticate(username=username, password=password)
        if user:
            if user.is_active:
                login(request, user)
                return self.create_response(request, {'success': True})
            else:
                return self.create_response(request, {'success': False, 'reason': 'disabled',}, HttpForbidden)

        else:
            return self.create_response(request, {'success': False, 'reason': 'incorrect'}, HttpUnauthorized)


    def logout(self, request, **kwargs):
        self.method_check(request, allowed=['post'])
        self.throttle_check(request)

        if request.user and request.user.is_authenticated():
            logout(request)
            return self.create_response(request, {'success': True})
        else:
            return self.create_response(request, {'success': False}, HttpUnauthorized)


    def add_invite(self, request, **kwargs):
        self.method_check(request, allowed=['post', ])
        self.throttle_check(request)
        data = self.deserialize(request, request.body, format=request.META.get('CONTENT_TYPE', 'application/json'))
        email = None
        try:
            email = data['email']
        except KeyError:
            pass
        if email:
            try:
                other_user = User.objects.get(email=email)
            except User.DoesNotExist:
                other_user = None
                print("USER DIDN'T EXIST") #TODO: EMAIL USER
            if other_user is not None:
                collaboration, created = Collaboration.objects.get_or_create(from_user=request.user,
                                                                             to_user=other_user)
        return self.get_detail(request, pk=request.user.pk)

    def reject_invite(self, request, **kwargs):
        self.method_check(request, allowed=['post', ])
        self.throttle_check(request)
        data = self.deserialize(request, request.body, format=request.META.get('CONTENT_TYPE', 'application/json'))
        email = None
        try:
            email = data['email']
        except KeyError:
            pass
        if email:
            try:
                other_user = User.objects.get(email=email)
            except User.DoesNotExist:
                other_user = None
            if other_user is not None:
                Collaboration.objects.filter(from_user=request.user, to_user=other_user).delete()
                Collaboration.objects.filter(from_user=other_user, to_user=request.user).delete()
        return self.get_detail(request, pk=request.user.pk)

    def dehydrate_temporary(self, bundle):
        # This method gets the associated Profile for this User, and returns
        # whether or not the user is temporary
        user = bundle.obj
        try:
            temporary = Profile.objects.get(user=user).temporary_acct
        except ObjectDoesNotExist:
            temporary = None
        return temporary


    def dispatch(self, request_type, request, **kwargs):
        """
        *** RAZ: Overriding this Tastypie method to remove
        authentication when users do a POST request
        to create a user through the API.
        This is so that end-users can create user objects
        and login without being authenticated.
        """

        # Need to import the following methods:
        from tastypie.resources import convert_post_to_put
        from tastypie import http
        from django.http import HttpResponse

        """
        Handles the common operations (allowed HTTP method, authentication,
        throttling, method lookup) surrounding most CRUD interactions.
        """
        allowed_methods = getattr(self._meta, "%s_allowed_methods" % request_type, None)

        if 'HTTP_X_HTTP_METHOD_OVERRIDE' in request.META:
            request.method = request.META['HTTP_X_HTTP_METHOD_OVERRIDE']

        request_method = self.method_check(request, allowed=allowed_methods)
        method = getattr(self, "%s_%s" % (request_method, request_type), None)

        if method is None:
            raise ImmediateHttpResponse(response=http.HttpNotImplemented())

        # *** Do not authenticate if request_method == post!***
        # The Tastypie dispatch method checks for authentication for any type
        # of request out of the box, but we do not want to check authentication
        # if the user isn't logged in and wants to login (or create a user account)
        # via a POST request to the API. If we check for authentication all the
        # time, users would have to be logged in to be able to log in
        # (a contradiction) or to create a new user account (highly
        # unlikely). If we comment out authentication for GET requests as well,
        # then the API returns an empty list '[]' when requesting the user
        # object with a correct OAuth token.
        if not (request_method == 'post'):
            self.is_authenticated(request)
        self.throttle_check(request)

        # All clear. Process the request.
        request = convert_post_to_put(request)
        response = method(request, **kwargs)

        # Add the throttled request.
        self.log_throttled_access(request)

        # If what comes back isn't a ``HttpResponse``, assume that the
        # request was accepted and that some action occurred. This also
        # prevents Django from freaking out.
        if not isinstance(response, HttpResponse):
            return http.HttpNoContent()

        return response

    def obj_create(self, bundle, request=None, **kwargs):
        self.throttle_check(request)

        try:
            bundle = super(UserResource, self).obj_create(bundle, **kwargs)
            bundle.obj.set_password(bundle.data.get('password'))
            bundle.obj.save()
        except IntegrityError:
            raise BadRequest('Username already exists')
        return bundle


class OrganismResource(ModelResource):

    class Meta:
        queryset   = Organism.objects.all()
        filtering  = {'scientific_name': ALL, 'slug': ALL, 'taxonomy_id': ALL}
        allowed_methods = ['get']
        detail_uri_name = 'slug'


class GeneResource(ModelResource):
    entrezid = fields.IntegerField(attribute = 'entrezid')
    pk = fields.IntegerField(attribute = 'id')
    xrids = fields.ToManyField('genesets.api.resources.CrossrefResource', 'crossref_set', related_name='gene', full=True)

    class Meta:
        queryset   = Gene.objects.all()
        resource_name = 'gene'
        filtering = {'entrezid': ALL, 'pk': ALL, 'symbol': ALL}
        allowed_methods = ['get']

    # All of the following is the search code used by Haystack to search for genes and return individual gene 'Resources'
        # that the users can add to their gene sets.
    def prepend_urls(self):
        return [
            url(r"^(?P<resource_name>%s)/search%s$" % (self._meta.resource_name, trailing_slash()), self.wrap_view('get_search'), name="api_get_search"),
            url(r"^(?P<resource_name>%s)/xrid_translate%s$" % (self._meta.resource_name, trailing_slash()), self.wrap_view('translate_gene_ids'), name="api_translate_gene_ids"),
        ]

    def get_search(self, request, **kwargs):
        self.method_check(request, allowed=['get', 'post'])
        self.is_authenticated(request)
        self.throttle_check(request)

        search_string = request.GET.get('query')
        #because the organism is sent as the URI, get the last element (the pk)
        organism_uri = request.GET.get('organism')
        organism = None
        if organism_uri:
            organism = OrganismResource().get_via_uri(organism_uri, request)
        if search_string:
            search_toks = set(search_string.split())
        else:
            search_toks = []

        genes = []

        for search in search_toks:
            item = {}
            item['search'] = search
            sqs = SearchQuerySet().models(Gene)
            if organism is not None:
                sqs = sqs.filter(organism=organism)
            sqs = sqs.filter(content=search)
            sqs = sqs.load_all()[:15]
            objects = []

            for result in sqs:
                bundle = self.build_bundle(obj=result.object, request=request)
                bundle = self.full_dehydrate(bundle)
                objects.append(bundle)

            item['found'] = objects
            genes.append(item)

        self.log_throttled_access(request)
        return self.create_response(request, genes)

    def translate_gene_ids(self, request, **kwargs):
        self.method_check(request, allowed=['post'])
        self.throttle_check(request)

        #extract the relevant parameters
        gene_list = request.POST.getlist('gene_list')
        from_id = request.POST.get('from_id')
        to_id   = request.POST.get('to_id')
        organism = request.POST.get('organism')

        #call the utils method for this
        return_ids_dict = translate_genes(id_list=gene_list, from_id=from_id, to_id=to_id, organism=organism)

        return self.create_response(request, return_ids_dict)

def can_edit_geneset(geneset, user):
    if user.is_authenticated():
        if geneset.creator == user: #creators can edit
            return True
        elif Share.objects.filter(geneset=geneset).filter(to_user=user).count():
            return True #can edit if it's shared with you
    return False

class GenesetAuthorization(Authorization):
    def read_list(self, object_list, bundle):
        if not bundle.request.user:
            logger.debug("No user with the request.")
            return object_list.filter(public=True)
        elif bundle.request.user.is_authenticated():
            logger.debug("User was passed with the request.")
            return object_list.filter(Q(share__to_user=bundle.request.user) | Q(creator=bundle.request.user) | Q(public=True) )
        else:
            logger.debug("Non-authenticated user.")
            return object_list.filter(public=True)

    def read_detail(self, object_list, bundle):
        if (bundle.obj.public):
            return True
        else:
            return can_edit_geneset(bundle.obj, bundle.request.user)

    def create_list(self, object_list, bundle):
        if not bundle.request.user.is_authenticated():
            raise Unauthorized("Only authenticated users can create gene sets.")
        return object_list

    def create_detail(self, object_list, bundle): # Users can only create a gene set if they are logged in
        if not bundle.request.user.is_authenticated():
            raise Unauthorized("Only authenticated users can create gene sets.")
        return bundle.request.user.is_authenticated()

    def update_list(self, object_list, bundle):
        raise Unauthorized("Multiple update not allowed for collections.")

    def update_detail(self, object_list, bundle):
        logger.debug("update_detail for %s by %s." % (bundle.obj, bundle.request.user))
        return can_edit_geneset(bundle.obj, bundle.request.user)

    def delete_list(self, object_list, bundle):
        raise Unauthorized("Sorry, deleting is not possible.")

    def delete_detail(self, object_list, bundle):
        user = bundle.request.user
        if (user.is_authenticated() and bundle.obj.creator == user):
            return True
        else:
            return False


"""
Utility function that gets the tip version for a geneset or None of no versions exist.
This is necessary because we can't just return the empty queryset (tastypie tries to
make it into a VersionResource and complains when it doesn't have a user, for example).
"""
def GetTip(gs):
    vers = Version.objects.filter(geneset=gs).order_by('-commit_date')[:1]
    if not vers.count():
        return None
    else:
        return vers[0]

class GenesetResource(ModelResource):
    title       = fields.CharField(attribute='title')
    creator     = fields.ForeignKey(BasicUserResource, 'creator', full=True)
    organism    = fields.ToOneField(OrganismResource, 'organism', full=True)
    fork_of     = fields.ToOneField('self', 'fork_of', null=True, full=True)
    slug        = fields.CharField(attribute='slug')
    abstr       = fields.CharField(attribute='abstract', null=True) # Using abstr for the interface files so that it does not interfere with the 'abstract' JS keyword
    public      = fields.BooleanField(attribute='public')
    editable    = fields.BooleanField(readonly=True)
    participants= fields.ListField(readonly=True, use_in=lambda bundle: bundle.request.GET.get('show_team', None) == 'true', null=True)
    versions    = fields.ToManyField('genesets.api.resources.GenesetVersionResource', readonly=True, full=True, full_detail=True, full_list=False, attribute=lambda bundle: Version.objects.filter(geneset=bundle.obj).order_by('-commit_date'), use_in=lambda bundle: bundle.request.GET.get('show_versions', None) == 'true', null=True)
    tip         = fields.ForeignKey('genesets.api.resources.GenesetVersionResource', readonly=True, full=True, full_list=True, attribute=lambda bundle: GetTip(bundle.obj), use_in=lambda bundle: bundle.request.GET.get('show_tip', None) == 'true', null=True)
    tags        = fields.ListField(attribute='tag_prop', readonly=True, null=True)

    class Meta:
        queryset      = Geneset.objects.all()
        always_return_data = True
        resource_name = 'geneset'
        authorization = GenesetAuthorization()  # Defined above
        authentication = MultiAuthentication(SessionAuthentication(), OAuth20Authentication())
        filtering     = {
        # Filtering is a tie to the Django ORM filter interface.  It allows the client side to query gene sets by the fields
        # included inside the curly braces.  For example, these filters can pass only the gene set with a specific title AND creator
        # combination to be passed to the user interface.  However, this does NOT include filtering based on whether a user is allowed
        # to see/modify a certain object.  This type of filtering is handled by the authorization class. For more on filtering,
        # see: https://django-tastypie.readthedocs.org/en/latest/resources.html?highlight=filtering#basic-filtering
            'id'        : ALL,
            'creator'   : ALL_WITH_RELATIONS,
            'title'     : ALL_WITH_RELATIONS,
            'query'     : ('exact',),
            'slug'      : ALL_WITH_RELATIONS,
            'organism'  : ALL_WITH_RELATIONS,
        }
        max_limit = None


    """
    This function allows for a filter to be constructed based on the query string. This will
    make sure that authorization and such remains in force after the search query.
    http://django-tastypie.readthedocs.org/en/latest/resources.html#advanced-filtering
    """
    def build_filters(self, filters=None):
        if filters is None:
            filters = {}

        orm_filters = super(GenesetResource, self).build_filters(filters)
        logger.info("Starting ORM Filters.")
        if "query" in filters:
            if filters["query"]:  # don't search if the string is empty
                logger.debug("Filtered by query.")
                sqs = SearchQuerySet().models(Geneset).filter(content=filters["query"]).load_all()
                orm_filters["pk__in"] = [i.pk for i in sqs]
                # TODO: Replace the two lines above with the lines below when
                # this issue: https://github.com/django-haystack/django-haystack/issues/1019
                # is merged and closed. Probably django-haystack 2.4
                #pks = SearchQuerySet().models(Geneset).filter(content=filters["query"]).values_list('pk', flat=True)
                #orm_filters["pk__in"] = [int(x) for x in pks]

        if "filter_tags" in filters:
            if filters["filter_tags"]:  # don't search if the string is empty
                logger.debug("Filtered by tags.")
                toks = filters["filter_tags"].replace("[", "").replace("]", "").replace(" ", "").split(",")
                orm_filters["tags__name__in"] = toks

        return orm_filters

    # URL that allows access by username and slug combined
    # http://django-tastypie.readthedocs.org/en/latest/cookbook.html?highlight=prepend_urls#using-non-pk-data-for-your-urls
    def prepend_urls(self):
        return [
            url(r"^(?P<resource_name>%s)/(?P<creator__username>[\w.-]+)/(?P<slug>[\w.-]+)%s$" % (self._meta.resource_name, trailing_slash()), self.wrap_view('dispatch_detail'), name="api_dispatch_detail"),
            url(r"^(?P<resource_name>%s)/(?P<creator__username>[\w.-]+)/(?P<slug>[\w.-]+)/invite%s$" % (self._meta.resource_name, trailing_slash()), self.wrap_view('invite_team'), name="api_invite_team"),
        ]

    def hydrate_creator(self, bundle):
        # The 'hydrate' method serves to customize what data is being saved back in the server when users create an object
        # In this case, this method states that whoever the logged-in user is when the gene set is created, will be the author
        # of the gene set.
        bundle.obj.creator = bundle.request.user
        return bundle

    def alter_list_data_to_serialize(self, request, data):
        if (request.META.has_key('oauth_token_expired')):
            data['meta']['oauth_token_expired'] = True
        return data

    def alter_detail_data_to_serialize(self, request, data):
        if (request.META.has_key('oauth_token_expired')):
            data['meta']['oauth_token_expired'] = True
        return data

    def dehydrate_editable(self, bundle):
        """
        Return whether or not the user has access to edit this geneset.
        This is for display only, and changing this will not change
        actual permissions.
        """
        return can_edit_geneset(bundle.obj, bundle.request.user)

    def dehydrate_participants(self, bundle):
        """
        Return a list of participants. If the user has update_detail
        authorization, also return email addresses of participants
        and who invited that participant. Otherwise just return usernames.
        """
        #this is to make things angular friendly, which seems to dislike the double underscore
        field_map = {
            'to_user__username' : 'username',
            'to_user__email'    : 'email',
            'from_user__email'  : 'invited_by'
        }
        fields = ['to_user__username', ]
        if can_edit_geneset(bundle.obj, bundle.request.user):
            fields.append('to_user__email')
            fields.append('from_user__email')
        shares = Share.objects.filter(geneset = bundle.obj).values(*fields)
        result = []
        for share in shares:
            new_item = {}
            for field in fields:
                new_item[field_map[field]] = share[field]
            result.append(new_item)
        return result

    """
    Allow new team members to be invited by anyone who has the update_detail authorization.
    """
    def invite_team(self, request, **kwargs):
        logger.debug("invite_team called by %s", (request.user))
        basic_bundle = self.build_bundle(request=request)

        try:
            obj = self.cached_obj_get(bundle=basic_bundle, **self.remove_api_resource_names(kwargs))
        except ObjectDoesNotExist:
            return http.HttpNotFound()
        except MultipleObjectsReturned:
            return http.HttpMultipleChoices("More than one resource is found at this URI.")

        logger.debug("invite_team obj %s found" % (obj))
        bundle = self.build_bundle(obj=obj, request=request)
        self.authorized_update_detail(self.get_object_list(bundle.request), bundle)
        logger.debug("invite_team Authorization passed.")
        self.method_check(request, allowed=['post', ])
        self.throttle_check(request)
        logger.debug("invite_team method and throttle passed.")
        data = self.deserialize(request, request.body, format=request.META.get('CONTENT_TYPE', 'application/json'))
        email = None
        try:
            email = data['email']
        except KeyError:
            pass
        if email:  # Can only share to collaborators
            collaborators = get_collaborators(request.user)
            try:
                other_user = collaborators.get(email=email)
            except User.DoesNotExist:  # user didn't exist or wasn't a collaborator
                other_user = None
            if other_user is not None:
                try:  # don't want to make doubles...
                    Share.objects.get(from_user=request.user, to_user=other_user, geneset=bundle.obj)
                except Share.DoesNotExist:
                    share = Share(from_user=request.user, to_user=other_user, geneset=bundle.obj)
                    logger.info("Added share from %s to %s for geneset %s", share.from_user.username, share.to_user.username, bundle.obj.title)
                    share.save()
        return self.get_detail(request, pk=bundle.obj.pk)  # return the object (modified if a share got added)

    """
    Only allow updates to the title or abstract of an existing geneset.
    """
    def obj_update(self, bundle, **kwargs):
        logger.info('Updating bundle %s', bundle)

        title = None
        try:
            title = bundle.data['title']
            bundle.obj.title = title
        except KeyError:
            pass

        abstract = None
        try:
            abstract = bundle.data['abstract']
            bundle.obj.abstract = abstract
        except KeyError:
            pass

        try:
            public = bundle.data['public']
            bundle.obj.public = public
        except KeyError:
            pass

        if title or abstract:
            self.save(bundle)

        return bundle

    def post_list(self, request, **kwargs):
        # Overriding post_list method to return an error if a geneset with the same creator and slug already exists.
        from tastypie import http
        from tastypie.utils import dict_strip_unicode_keys
        from django.template.defaultfilters import slugify
        deserialized = self.deserialize(request, request.body, format=request.META.get('CONTENT_TYPE', 'application/json'))
        deserialized = self.alter_deserialized_detail_data(request, deserialized)
        bundle = self.build_bundle(data=dict_strip_unicode_keys(deserialized), request=request)

        # Check that creator is actually logged-in:
        request_user = bundle.request.user

        # If there is either no user or the user is not authenticated,
        # return Unauthorized response:
        if (not request.user):  
            return http.HttpUnauthorized()
        elif (not request_user.is_authenticated()):
            return http.HttpUnauthorized()
        else:
            loggedin_creator = bundle.request.user
            gs_slug_max_length = Geneset._meta.get_field('slug').max_length
            gs_slug = slugify(bundle.data['title'])[:gs_slug_max_length]
            non_unique = Geneset.objects.filter(creator=loggedin_creator).filter(slug=gs_slug)
            if (non_unique):
                return http.HttpBadRequest("There is already one"\
                    " collection with this url created by this account. "\
                    "Please choose a different collection title. For more "\
                    "information, see our documentation here: "\
                    + settings.DOCS_URL + "using_tribe.html#collection-urls")
            else:
                updated_bundle = self.obj_create(bundle, **self.remove_api_resource_names(kwargs))
                location = self.get_resource_uri(updated_bundle)
                if not self._meta.always_return_data:
                    return http.HttpCreated(location=location)
                else:
                    updated_bundle = self.full_dehydrate(updated_bundle)
                    updated_bundle = self.alter_detail_data_to_serialize(request, updated_bundle)
                    return self.create_response(request, updated_bundle, response_class=http.HttpCreated, location=location)


    def obj_create(self, bundle, **kwargs):
        logger.info('Creating bundle %s', bundle)
        bundle = super(GenesetResource, self).obj_create(bundle, **kwargs)

        try:
            fork_ver_hash = bundle.data['fork_version']
        except KeyError:
            fork_ver_hash = None

        if fork_ver_hash:  # if this was a fork of a specific version, add all the prior versions

            # Disable commit date so we preserve original dates of versions
            commit_date = Version._meta.get_field_by_name('commit_date')[0]
            commit_date.auto_now_add = False

            # We have to make the first version in that geneset (the one with
            # no parent version) before we start our loop. Otherwise, we get
            # a NoParentVersionSpecified exception
            first_version = Version.objects.get(geneset=bundle.obj.fork_of,
                                                parent=None)
            first_forked_version = deepcopy(first_version)
            first_forked_version.id = None
            first_forked_version.geneset = bundle.obj
            first_forked_version.save()

            fork_version = Version.objects.get(geneset=bundle.obj.fork_of,
                                               ver_hash=fork_ver_hash)

            # Recursively copy all parent versions of this version, *except*
            # for the first version, which we have already copied
            while fork_version.parent is not None:
                new_obj = deepcopy(fork_version)
                new_obj.id = None
                new_obj.geneset = bundle.obj
                new_obj.save()
                fork_version = fork_version.parent
            commit_date.auto_now_add = True

        else:

            try:
                parent_version = bundle.data['parent_version']
            except KeyError:
                parent_version = None

            if 'description' in bundle.data:
                version = Version(geneset=bundle.obj, 
                                  creator=bundle.obj.creator, 
                                  description=bundle.data['description'],
                                  parent=parent_version)
            else:
                version = Version(geneset=bundle.obj,
                                  creator=bundle.obj.creator,
                                  description="Created with collection.",
                                  parent=parent_version)

            try:
                passed_annotations = bundle.data['annotations']
            except KeyError:
                passed_annotations = None     

            try:
                posted_database = bundle.data['xrdb']
            except KeyError:
                posted_database = None

            try:
                full_pubs = bundle.data['full_pubs']
            except KeyError:
                full_pubs = None

            logger.info('Hydrating annotations sent with geneset %s', bundle)

            genes_not_found = None
            if passed_annotations:
                # if annotations were passed, add them to a new version
                logger.info('Annotations were passed to create Geneset,'\
                            'make an initial version with these annotations: %s',
                            passed_annotations)
                formatted_for_db_annotations, genes_not_found =\
                            version.format_annotations(passed_annotations,
                                                       posted_database, full_pubs)
                version.annotations = formatted_for_db_annotations
                version.save()
            else:
                logger.info('Hydrated gene set without any annotations, %s', bundle)

            if genes_not_found:
                bundle.data['Warning - The following genes were not found in our database'] =\
                                                                         list(genes_not_found)

        return bundle


    def get_object_list(self, request):
        return super(GenesetResource, self).get_object_list(request).filter(deleted=False)

    def delete_detail(self, request, **kwargs):
        # Overriding delete_detail method to change the status of genesets to 'deleted'
        # If the geneset is found and marked as deleted, return ``HttpNoContent`` (204 No Content).
        # If the geneset did not exist, return ``Http404`` (404 Not Found).

        # Manually construct the bundle here to change 'deleted'
        # status to True

        basic_bundle = self.build_bundle(request=request)

        try:
            obj = self.cached_obj_get(bundle=basic_bundle, **self.remove_api_resource_names(kwargs)) # build obj first
            bundle = self.build_bundle(obj=obj, request=request)
            bundle = self.full_dehydrate(bundle)
            bundle.obj.deleted = True

            # Check for delete_detail authorization first, which is more stringent than the update_detail authorization
            # (as user needs to be the geneset author in order to delete)
            self.authorized_delete_detail(self.get_object_list(bundle.request), bundle) 
            updated_bundle = self.obj_update(bundle=bundle, **self.remove_api_resource_names(kwargs))
            return http.HttpNoContent()

        except ObjectDoesNotExist:
            return http.HttpNotFound()

        except MultipleObjectsReturned:
            return http.HttpMultipleChoices("More than one resource is found at this URI.")


class VersionAuthorization(Authorization):
    def read_list(self, object_list, bundle):
        if not bundle.request.user:
            return object_list.filter( geneset__public=True )
        elif bundle.request.user.is_authenticated():
            return object_list.filter( Q( geneset__share__to_user=bundle.request.user) | Q(creator=bundle.request.user) | Q(geneset__public=True) )
        else:
            return object_list.filter( geneset__public=True )

    def read_detail(self, object_list, bundle):
        if (bundle.obj.geneset.public == True):
            return True
        else:
            return can_edit_geneset(bundle.obj.geneset, bundle.request.user)

    def update_list(self, object_list, bundle): 
        # Users are not able to update versions;
        # They can only create new versions in their gene sets.
        raise Unauthorized("Versions cannot be modified after they are created.")

    def update_detail(self, object_list, bundle):
        raise Unauthorized("Versions cannot be modified after they are created.")

    def delete_list(self, object_list, bundle):
        raise Unauthorized("Versions cannot be modified after they are created.")

    def delete_detail(self, object_list, bundle):
        raise Unauthorized("Versions cannot be modified after they are created.")

class VersionResource(ModelResource):
    creator     = fields.ForeignKey(BasicUserResource, 'creator', full=True)
    geneset     = fields.ForeignKey(GenesetResource, 'geneset', full=True)
    genes       = fields.ListField(null=True)
    parent      = fields.ToOneField('self', 'parent', null=True, full=False)
    gene_objs   = fields.ToManyField('genesets.api.resources.GeneResource', readonly=True, full=True, full_detail=True, full_list=True, attribute=lambda bundle: Gene.objects.filter(pk__in=[annot[0] for annot in bundle.obj.annotations]), use_in=lambda bundle: (bundle.request.GET.get('full_genes', None) == 'true' or bundle.request.GET.get('xrids_requested', None) == 'true'), null=True)
    annotations = fields.ListField(null=True)

    class Meta:
        queryset = Version.objects.all()
        always_return_data = True
        authorization = VersionAuthorization() # Defined above
        authentication = MultiAuthentication( SessionAuthentication(), OAuth20Authentication())
        fields = ['description', 'commit_date', 'creator', 'ver_hash', 'genes', 'parent', 'geneset', 'annotations']
        filtering     = {
            'creator': ALL_WITH_RELATIONS,
            'geneset': ALL_WITH_RELATIONS,
            'ver_hash': ALL,
        }
        max_limit = None

    # URL that allows access by geneset username and slug combined with the version hash
    # http://django-tastypie.readthedocs.org/en/latest/cookbook.html?highlight=prepend_urls#using-non-pk-data-for-your-urls
    def prepend_urls(self):
        return [
            url(r"^(?P<resource_name>%s)/(?P<geneset__creator__username>[\w.-]+)/(?P<geneset__slug>[\w.-]+)/(?P<ver_hash>[\w.-]+)%s$" % (self._meta.resource_name, trailing_slash()), self.wrap_view('dispatch_detail'), name="api_dispatch_detail"),
        ]

    def dehydrate_annotations(self, bundle):
        logger.info("Dehydrating Annotations")

        """
        Pull out both the gene and publication objects and put them into a list that gets returned.
        Format is: [{genedict}, [{pubdict}, {pubdict}...]]
        """

        xrids_requested = bundle.request.GET.get('xrids_requested', None)
        genes = set()
        pubs = set()
        for annotation in bundle.obj.annotations:
            (gene, pub) = annotation
            genes.add(gene)
            pubs.add(pub)
        gene_cache = {}

        if (xrids_requested == 'true'):
            for gobj in bundle.data['gene_objs']:
                gene_cache[gobj.data['id']] = gobj.data

        else:
            gene_objs = Gene.objects.filter(pk__in=genes).values()
            for gobj in gene_objs:
                gene_cache[gobj['id']] = gobj

        pub_objs = Publication.objects.filter(pk__in=pubs).values()
        pub_cache = {}
        for pobj in pub_objs:
            pub_cache[pobj['id']] = pobj
        results = {}
        for annotation in bundle.obj.annotations:
            (gene, pub) = annotation
            try:
                results[gene].append(pub_cache[pub])
            except KeyError:
                try:
                    results[gene] = [pub_cache[pub],]
                except KeyError:
                    results[gene] = []
        return_list = []
        for (gid, pubs) in results.iteritems():
            return_list.append({'gene':gene_cache[gid],'pubs': pubs})
        return return_list


    def dehydrate_genes(self, bundle):
        return_ids_list = []
        requested_database = bundle.request.GET.get('xrdb', None)
        pk_list = list([annot[0] for annot in bundle.obj.annotations])

        if (( requested_database is None ) or ( requested_database == 'Entrez' )):
            queryset = Gene.objects.filter(pk__in=pk_list)
            return_ids_list = queryset.values_list('entrezid', flat=True)
        elif ( requested_database == 'Symbol' ):
            queryset = Gene.objects.filter(pk__in=pk_list)
            return_ids_list = queryset.values_list('systematic_name', flat=True)
        else:
            return_ids_list = CrossRef.objects.filter(crossrefdb__name=requested_database).filter(gene__in=pk_list).values_list('xrid', flat=True)

        return list(return_ids_list)

    def alter_list_data_to_serialize(self, request, data):
        if (request.META.has_key('oauth_token_expired')):
            data['meta']['oauth_token_expired'] = True
        return data

    def alter_detail_data_to_serialize(self, request, data):
        if (request.META.has_key('oauth_token_expired')):
            data['meta']['oauth_token_expired'] = True
        return data

    def hydrate_creator(self, bundle):
        bundle.obj.creator = bundle.request.user
        return bundle

    def hydrate_annotations(self, bundle):
        try:
            passed_annotations = bundle.data['annotations']
        except KeyError:
            passed_annotations = None
            # Note: This is the right way to return a BadRequest response
            # to the user!!
            raise BadRequest("New versions must have annotations.")

        logger.info('Hydrating annotations - the following annotations were passed to create a Version: %s', passed_annotations)

        try:
            posted_database = bundle.data['xrdb']
        except KeyError:
            posted_database = None

        try:
            full_pubs = bundle.data['full_pubs']
        except KeyError:
            full_pubs = None

        formatted_for_db_annotations, genes_not_found = bundle.obj.format_annotations(passed_annotations, posted_database, full_pubs)

        if genes_not_found:
            bundle.data['Warning - The following genes were not found in our database'] = list(genes_not_found)

        bundle.obj.annotations = formatted_for_db_annotations
        return bundle


    def obj_create(self, bundle, **kwargs):
        """
        This overrides the Resource's default obj_create method. It checks
        to see if the Version model itself throws a 'NoParentVersionSpecified'
        exception when it tries to save the Version (see Version.save() 
        method).
        """
        try:
            bundle = super(VersionResource, self).obj_create(bundle, **kwargs)
        except NoParentVersionSpecified:
            raise BadRequest("This geneset already has at least one version." + \
                " You must specify the parent version of this new version.")
        return bundle


"""
Version resource for the genesets class. Need this so that we can avoid showing geneset when
called from a geneset (painful infinite recursion, tastypie doesn't allow a depth limit).
"""
class GenesetVersionResource(VersionResource):
    creator   = fields.ForeignKey(BasicUserResource, 'creator', full=True)
    geneset   = fields.ForeignKey(GenesetResource, 'geneset', full=False)
    genes     = fields.ListField(null=True)
    parent    = fields.ToOneField('self', 'parent', null=True, full=False)
    annotations = fields.ListField(null=True, use_in=lambda bundle: bundle.request.GET.get('full_annotations', None) == 'true')

    class Meta:
        max_limit = None

        # The resource_name Meta option is very important! It is required
        # for the GeneserVersionResource to be able to return a resource_uri
        resource_name = 'version'

    def dehydrate_annotations(self, bundle):
        """
        Pull out both the gene and publication objects and put them into a list that gets returned.
        Format is: [{genedict}, [{pubdict}, {pubdict}...]]
        """
        genes = set()
        pubs = set()
        for annotation in bundle.obj.annotations:
            (gene, pub) = annotation
            genes.add(gene)
            pubs.add(pub)
        gene_objs = Gene.objects.filter(pk__in=genes).values()
        gene_cache = {}
        for gobj in gene_objs:
            gene_cache[gobj['id']] = gobj
        pub_objs = Publication.objects.filter(pk__in=pubs).values()
        pub_cache = {}
        for pobj in pub_objs:
            pub_cache[pobj['id']] = pobj
        results = {}
        for annotation in bundle.obj.annotations:
            (gene, pub) = annotation
            try:
                results[gene].append(pub_cache[pub])
            except KeyError:
                try:
                    results[gene] = [pub_cache[pub],]
                except KeyError:
                    results[gene] = []
        return_list = []
        for (gid, pubs) in results.iteritems():
            return_list.append({'gene':gene_cache[gid],'pubs': pubs})
        return return_list


class PublicationResource(ModelResource):
    pmid     = fields.IntegerField(attribute='pmid', null=True)
    title    = fields.CharField(attribute='title')
    authors  = fields.CharField(attribute='authors')
    date     = fields.DateField(attribute='date')
    journal  = fields.CharField(attribute='journal')
    volume   = fields.CharField(attribute='volume', null=True)
    pages    = fields.CharField(attribute='pages', null=True)
    issue    = fields.CharField(attribute='issue', null=True)

    class Meta:
        queryset = Publication.objects.all()
        always_return_data = True
        fields = ['id', 'pmid', 'title', 'authors', 'date', 'journal', 'volume', 'pages', 'issue']
        allowed_methods = ['get']
        filtering     = {
            'pmid': ALL,
            'title': ALL,
            'authors': ALL,
            'date': ALL,}

    # URL that allows access by username and slug combined
    # http://django-tastypie.readthedocs.org/en/latest/cookbook.html?highlight=prepend_urls#using-non-pk-data-for-your-urls
    def prepend_urls(self):
        return [
            url(r"^(?P<resource_name>%s)/(?P<pmid>[\w.-]+)%s$" % (self._meta.resource_name, trailing_slash()), self.wrap_view('dispatch_detail'), name="api_dispatch_detail"),
        ]

    def get_detail(self, request, **kwargs):
        pmid = request.GET.get('search_pmid', None)
        if pmid is not None:
            load_pmids([pmid, ])
        return super(PublicationResource, self).get_detail(request, **kwargs)

class CrossrefResource(ModelResource):
    xrid       = fields.CharField(attribute='xrid')
    crossrefdb = fields.CharField(attribute='crossrefdb')
    gene       = fields.ToOneField(GeneResource, 'gene')
    db_url     = fields.CharField(attribute='specific_url')

    class Meta:
        queryset = CrossRef.objects.all()
        fields = ['xrid', 'gene']
        allowed_methods = ['get']
        filtering     = {
            'xrid': ALL,
            'crossrefdb': ALL,
            'gene': ALL_WITH_RELATIONS }