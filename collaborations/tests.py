"""
Tests for collaboration.

This includes tests for shares, and uses the API provided by genesets. Ultimately it might be good
to extract each of the API components into their respective reusable modules.
"""

from django.contrib.auth.models import User

from fixtureless import Factory

from tastypie.test import ResourceTestCase, TestApiClient

from organisms.models import Organism
from genes.models import Gene
from genesets.models import Geneset
from collaborations.models import Share, Collaboration
from collaborations.utils import get_collaborators, get_invites, get_inviteds

factory = Factory()


class ShareFromTestCase(ResourceTestCase):

    """
    Test that collaborators can share.

    Test that collaborators can share via the API. These test cases are for two users, u1 and u2
    who collaborate and need to share genesets.
    """

    def setUp(self):
        """
        Set up test environment.

        Make two users, log in one of the users, create some genes and an organism, a geneset,
        and a collaboration.
        """
        super(ShareFromTestCase, self).setUp()

        # Make Two Users
        self.u1 = "asdf"
        self.e1 = "asdf@example.com"
        self.p1 = "qwerty"
        self.owner = User.objects.create_user(self.u1, self.e1, self.p1)

        self.u2 = "asdf2"
        self.e2 = "asdf2@example.com"
        self.p2 = "qwerty2"
        self.other = User.objects.create_user(self.u2, self.e2, self.p2)

        # log in the owner
        self.api_client.client.login(username=self.u1, password=self.p1)

        # Make Organism and Genes
        self.org = factory.create(Organism)
        initial = {'organism': self.org}  # Make sure these are for the right organism.
        self.g1 = factory.create(Gene, initial)
        self.g2 = factory.create(Gene, initial)

        # Make our geneset.
        self.geneset = Geneset.objects.create(creator=self.owner, title='Test Geneset 1',
                                              organism=self.org, deleted=False,
                                              abstract='Collaboration Invitations.', public=False)

        self.geneset_url = '/api/v1/geneset/%s/%s/invite' % (self.geneset.creator.username, self.geneset.slug)

        # Make Collaboration, requires reciprocal
        c1 = Collaboration(from_user=self.owner, to_user=self.other)
        c1.save()
        c2 = Collaboration(from_user=self.other, to_user=self.owner)
        c2.save()

    def testNoEmailPassed(self):
        """
        Test invite without passed user.

        If the user has permissions to invite, but no user e-mail address was passed,
        we should just return the detail view.
        """
        resp = self.api_client.post(self.geneset_url, format="json")
        self.assertValidJSONResponse(resp)
        self.assertEqual(self.deserialize(resp)['title'], 'Test Geneset 1')

    def testEmailPassed(self):
        """
        Test invite without passed user.

        If the user has permissions to invite, but no user e-mail address was passed,
        we should just return the detail view.
        """
        resp = self.api_client.post(self.geneset_url, data={'email': self.e2}, format="json")
        self.assertValidJSONResponse(resp)
        self.assertEqual(self.deserialize(resp)['title'], 'Test Geneset 1')
        result = Geneset.objects.get(pk=self.deserialize(resp)['id'])
        shares = Share.objects.filter(geneset=result)
        self.assertEqual(len(shares), 1)

    def tearDown(self):
        """
        Remove setup components.

        tearDown is called by django at the end to clean up any changes to the database that occured
        in setUp.
        """
        User.objects.all().delete()
        Organism.objects.all().delete()
        Gene.objects.all().delete()
        Geneset.objects.all().delete()
        Collaboration.objects.all().delete()


class NoCollaborationShareFromTestCase(ResourceTestCase):

    """
    Test that non-collaborating users can't share genesets.

    Only collaborators are eligible to share genesets. These tests insure that users that don't
    collaborate can't share.
    """

    def setUp(self):
        super(NoCollaborationShareFromTestCase, self).setUp()

        # Make Two Users
        self.u1 = "asdf"
        self.e1 = "asdf@example.com"
        self.p1 = "qwerty"
        self.owner = User.objects.create_user(self.u1, self.e1, self.p1)

        self.u2 = "asdf2"
        self.e2 = "asdf2@example.com"
        self.p2 = "qwerty2"
        self.other = User.objects.create_user(self.u2, self.e2, self.p2)

        # log in the owner
        self.api_client.client.login(username=self.u1, password=self.p1)

        # Make Organism and Genes
        self.org = factory.create(Organism)
        initial = {'organism': self.org}  # Make sure these are for the right organism.
        self.g1 = factory.create(Gene, initial)
        self.g2 = factory.create(Gene, initial)

        # Make our geneset.
        self.geneset = Geneset.objects.create(creator=self.owner, title='Test Geneset 1',
                                              organism=self.org, deleted=False,
                                              abstract='Collaboration Invitations.', public=False)

        self.geneset_url = '/api/v1/geneset/%s/%s/invite' % (self.geneset.creator.username, self.geneset.slug)

    def testNoEmailPassed(self):
        """
        Test invite without passed user.

        If the user has permissions to invite, but no user e-mail address was passed,
        we should just return the detail view.
        """
        resp = self.api_client.post(self.geneset_url, format="json")
        self.assertValidJSONResponse(resp)
        self.assertEqual(self.deserialize(resp)['title'], 'Test Geneset 1')

    def testEmailPassed(self):
        """
        Test invite without passed user.

        If the user has permissions to invite, but no user e-mail address was passed,
        we should just return the detail view.
        """
        resp = self.api_client.post(self.geneset_url, data={'email': self.e2}, format="json")
        self.assertValidJSONResponse(resp)
        self.assertEqual(self.deserialize(resp)['title'], 'Test Geneset 1')
        result = Geneset.objects.get(pk=self.deserialize(resp)['id'])
        shares = Share.objects.filter(geneset=result)
        self.assertEqual(len(shares), 0)


    def tearDown(self):
        """
        Remove setup components.

        tearDown is called by django at the end to clean up any changes to the database that occured
        in setUp.
        """
        User.objects.all().delete()
        Organism.objects.all().delete()
        Gene.objects.all().delete()
        Geneset.objects.all().delete()


class ShareReverseRequestTestCase(ResourceTestCase):

    """
    Test that collaborators cannot add themselves to genesets they don't own yet.

    Test that collaborators cannot force a share via the API. These test cases are for two users, u1
    and u2 who collaborate, and the request to share comes from a non-creator w/o permissions u2.
    """

    def setUp(self):
        """
        Set up test environment.

        Make two users, log in one of the users, create some genes and an organism, a geneset,
        and a collaboration.
        """
        super(ShareReverseRequestTestCase, self).setUp()

        # Make Two Users
        self.u1 = "asdf"
        self.e1 = "asdf@example.com"
        self.p1 = "qwerty"
        self.owner = User.objects.create_user(self.u1, self.e1, self.p1)

        self.u2 = "asdf2"
        self.e2 = "asdf2@example.com"
        self.p2 = "qwerty2"
        self.other = User.objects.create_user(self.u2, self.e2, self.p2)

        # log in the owner
        self.api_client.client.login(username=self.u2, password=self.p2)

        # Make Organism and Genes
        self.org = factory.create(Organism)
        initial = {'organism': self.org}  # Make sure these are for the right organism.
        self.g1 = factory.create(Gene, initial)
        self.g2 = factory.create(Gene, initial)

        # Make our geneset.
        self.geneset = Geneset.objects.create(creator=self.owner, title='Test Geneset 1',
                                              organism=self.org, deleted=False,
                                              abstract='Collaboration Invitations.', public=False)

        self.geneset_url = '/api/v1/geneset/%s/%s/invite' % (self.geneset.creator.username, self.geneset.slug)

        # Make Collaboration, requires reciprocal
        c1 = Collaboration(from_user=self.owner, to_user=self.other)
        c1.save()
        c2 = Collaboration(from_user=self.other, to_user=self.owner)
        c2.save()

    def testNoEmailPassed(self):
        """
        Test invite without passed user.

        If the user has permissions to invite, but no user e-mail address was passed,
        we should just return the detail view.
        """
        resp = self.api_client.post(self.geneset_url, format="json")
        self.assertHttpUnauthorized(resp)

    def testEmailPassed(self):
        """
        Test invite without passed user.

        If the user has permissions to invite, but no user e-mail address was passed,
        we should just return the detail view.
        """
        resp = self.api_client.post(self.geneset_url, data={'email': self.e2}, format="json")
        self.assertHttpUnauthorized(resp)


    def tearDown(self):
        """
        Remove setup components.

        tearDown is called by django at the end to clean up any changes to the database that occured
        in setUp.
        """
        User.objects.all().delete()
        Organism.objects.all().delete()
        Gene.objects.all().delete()
        Geneset.objects.all().delete()
        Collaboration.objects.all().delete()


class CollaborationTestCase(ResourceTestCase):

    """
    Test that users can create collaborations.

    Test that users can create collaborations via the API.
    """

    def setUp(self):
        """
        Set up test environment.

        Make two user.
        """
        super(CollaborationTestCase, self).setUp()

        # Make Two Users
        self.u1 = "asdf"
        self.e1 = "asdf@example.com"
        self.p1 = "qwerty"
        self.owner = User.objects.create_user(self.u1, self.e1, self.p1)
        self.expected_owner = {u'email': u'asdf@example.com', u'resource_uri': u'', u'username': u'asdf'}

        self.u2 = "asdf2"
        self.e2 = "asdf2@example.com"
        self.p2 = "qwerty2"
        self.other = User.objects.create_user(self.u2, self.e2, self.p2)
        self.expected_other = {u'email': u'asdf2@example.com', u'resource_uri': u'', u'username': u'asdf2'}

    def testInviteNotLoggedIn(self):
        """
        Test invite without a logged in user.

        Without anyone logged in, 404 should be returned.
        """
        resp = self.api_client.post('/api/v1/user/invite', format="json")
        self.assertHttpNotFound(resp)

    def testRejectNotLoggedIn(self):
        """
        Test reject without a logged in user.

        Without anyone logged in, 404 should be returned.
        """
        resp = self.api_client.post('/api/v1/user/reject', format="json")
        self.assertHttpNotFound(resp)

    def testInviteNoContent(self):
        """
        Test invite with a logged in user but no content.

        The user object should be returned without any invites.
        """
        client = TestApiClient()
        client.client.login(username=self.u1, password=self.p1)
        resp = client.post('/api/v1/user/invite', format="json")
        self.assertValidJSONResponse(resp)
        self.assertEqual(self.deserialize(resp)['invites'], [])

    def testPOSTInvite(self):
        """
        Test POST invite with a logged in user.

        The user object should be returned with u2 in invites.
        """
        client = TestApiClient()
        client.client.login(username=self.u1, password=self.p1)
        resp = client.post('/api/v1/user/invite', format="json", data={'email': self.e2})
        self.assertValidJSONResponse(resp)
        self.assertEqual(self.deserialize(resp)['invites'], [self.expected_other])
        self.assertListEqual(list(get_invites(self.owner)), [self.other])
        self.assertListEqual(list(get_inviteds(self.other)), [self.owner])
        self.assertListEqual(list(get_collaborators(self.owner)), [])
        self.assertListEqual(list(get_collaborators(self.other)), [])

    def testCollaboration(self):
        """
        Test that both users confirming results in a collaboration.

        The user objects returned should each be collaborators with each other.
        """
        c1 = TestApiClient()
        c1.client.login(username=self.u1, password=self.p1)
        r1 = c1.post('/api/v1/user/invite', format="json", data={'email': self.e2})
        self.assertValidJSONResponse(r1)

        c2 = TestApiClient()
        c2.client.login(username=self.u2, password=self.p2)
        r2 = c2.post('/api/v1/user/invite', format="json", data={'email': self.e1})
        self.assertValidJSONResponse(r2)

        self.assertListEqual(list(get_collaborators(self.owner)), [self.other])
        self.assertListEqual(list(get_collaborators(self.other)), [self.owner])
        self.assertListEqual(list(get_invites(self.owner)), [])
        self.assertListEqual(list(get_inviteds(self.other)), [])

    def testRejectInvite(self):
        """
        Test that one user rejecting elimintes the invite.

        The user objects returned should each have no relationship with each other after an
        invite + reject.
        """
        c1 = TestApiClient()
        c1.client.login(username=self.u1, password=self.p1)
        r1 = c1.post('/api/v1/user/invite', format="json", data={'email': self.e2})
        self.assertValidJSONResponse(r1)

        c2 = TestApiClient()
        c2.client.login(username=self.u2, password=self.p2)
        r2 = c2.post('/api/v1/user/reject', format="json", data={'email': self.e1})
        self.assertValidJSONResponse(r2)

        self.assertListEqual(list(get_collaborators(self.owner)), [])
        self.assertListEqual(list(get_collaborators(self.other)), [])
        self.assertListEqual(list(get_invites(self.owner)), [])
        self.assertListEqual(list(get_inviteds(self.other)), [])

    def testRejectCollaboration(self):
        """
        Test that one user rejecting an existing collaboration destroys the collaboration.

        The user objects returned should each have no relationship with each other after a
        collaboration + reject.
        """
        c1 = TestApiClient()
        c1.client.login(username=self.u1, password=self.p1)
        r1 = c1.post('/api/v1/user/invite', format="json", data={'email': self.e2})
        self.assertValidJSONResponse(r1)

        c2 = TestApiClient()
        c2.client.login(username=self.u2, password=self.p2)
        r2 = c2.post('/api/v1/user/invite', format="json", data={'email': self.e1})
        self.assertValidJSONResponse(r2)

        # Collaboration Exists
        self.assertListEqual(list(get_collaborators(self.owner)), [self.other])
        self.assertListEqual(list(get_collaborators(self.other)), [self.owner])

        c2 = TestApiClient()
        c2.client.login(username=self.u2, password=self.p2)
        r2 = c2.post('/api/v1/user/reject', format="json", data={'email': self.e1})
        self.assertValidJSONResponse(r2)

        # Collaboration no longer exists.
        self.assertListEqual(list(get_collaborators(self.owner)), [])
        self.assertListEqual(list(get_collaborators(self.other)), [])
        self.assertListEqual(list(get_invites(self.owner)), [])
        self.assertListEqual(list(get_inviteds(self.other)), [])

    def testGETInvite(self):
        """
        Test GET invite with a logged in user.

        Only POST is allowed, so this should return 405.
        """
        client = TestApiClient()
        client.client.login(username=self.u1, password=self.p1)
        resp = client.get('/api/v1/user/invite', format="json", data={'email': self.e2})
        self.assertHttpMethodNotAllowed(resp)

    def tearDown(self):
        """
        Remove setup components.

        tearDown is called by django at the end to clean up any changes to the database that occured
        in setUp.
        """
        User.objects.all().delete()
        Organism.objects.all().delete()
        Gene.objects.all().delete()
        Geneset.objects.all().delete()
        Collaboration.objects.all().delete()
