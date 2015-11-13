"""
Tests for user creation/authentication through REST API.

"""
from django.contrib.auth.models import User
from organisms.models import Organism
from genesets.models import Geneset
from fixtureless import Factory
from tastypie.test import ResourceTestCase, TestApiClient
from oauth2_provider.models import Application

factory = Factory()


class UserBasicLoginTestCase(ResourceTestCase):
    """
    Test basic API access to user objects if users are/are not logged in (using
    the test-client login method).
    """

    def setUp(self):
        super(UserBasicLoginTestCase, self).setUp()

        self.username = "hjkl"
        self.email = "hjkl@example.com"
        self.password = "1234"
        self.user1 = User.objects.create_user(self.username, self.email, self.password)


    def testCheckAuthorizationNotLoggedIn(self):
        """
        Check that a user has access to NO user objects if they are not logged
        in.
        """
        client = TestApiClient()
        resp = client.get('/api/v1/user', format="json")

        self.assertValidJSONResponse(resp)
        self.assertEqual(self.deserialize(resp)['objects'], [])


    def testCheckAuthorizationLoggedIn(self):
        """
        Check that a user has access to user object created previously if they
        ARE logged in (using the test-client login method).
        """
        client = TestApiClient()
        client.client.login(username=self.username, password=self.password)
        resp = client.get('/api/v1/user', format="json")

        self.assertValidJSONResponse(resp)
        self.assertEqual(self.deserialize(resp)['objects'][0]['username'], self.username)


    def tearDown(self):
        """
        Remove setup components.

        tearDown is called by django at the end to clean up any changes to the database that occured
        in setUp.
        """
        User.objects.all().delete()


class UserCreationTestCase(ResourceTestCase):
    """
    Test that users can be created from json objects through API UserResource
    """

    def setUp(self):
        super(UserCreationTestCase, self).setUp()

        self.post_user_data = {
            'username': 'asdf',
            'email': 'asdf@example.com',
            'password': 'qwerty'
        }

        # Create the organism 'Human' in the database (not using factory, since it needs to have a resource uri)
        org = Organism.objects.create(common_name="Human", scientific_name="Homo sapiens", slug="homo-sapiens", taxonomy_id=9606)


    def testCreateUserObj(self):
        """
        Check that the end-user can create a user through the API. Check that:

        a) they have access to this user object they just created via the API
        if they are logged in (using the test-client login method), and

        b) the user object is what we expect.
        """
        client = TestApiClient()

        resp = client.post('/api/v1/user', format="json", data=self.post_user_data)
        self.assertHttpCreated(resp)

        client.client.login(username=self.post_user_data['username'], password=self.post_user_data['password'])
        resp = client.get('/api/v1/user', format="json")

        self.assertValidJSONResponse(resp)
        self.assertEqual(self.deserialize(resp)['objects'][0]['username'], self.post_user_data['username'])


    def testCheckUserPassword(self):
        """
        Check that users have no access to user objects they just created if
        they supply the correct username but wrong password (This checks that
        the password is being set correctly when creating the user).
        """
        client = TestApiClient()

        client.post('/api/v1/user', format="json", data=self.post_user_data)
        client.client.login(username=self.post_user_data['username'], password='WrongPassword')
        resp = client.get('/api/v1/user', format="json")

        self.assertValidJSONResponse(resp)
        self.assertEqual(self.deserialize(resp)['objects'], [])


    def testCreatingGenesetWithNewUser(self):
        client = TestApiClient()

        # Create user and log in
        client.post('/api/v1/user', format="json", data=self.post_user_data)
        client.client.login(username=self.post_user_data['username'], password=self.post_user_data['password'])

        post_geneset_data = {
            # Does not need user info because the API automatically gathers that from the request
            'title': 'TestGeneset2',
            'organism': '/api/v1/organism/homo-sapiens',
            'abstract': 'Second test geneset created by user.',
            'public' : False,
            'annotations': {55982: [20671152, 19583951], 18091: [8887666], 67087: [], 22410:[]},
            'xrdb': 'Entrez',
            'description': 'First version.',
        }

        # Create a geneset, check for '201 Created' response
        r1 = client.post('/api/v1/geneset', format="json", data=post_geneset_data)
        self.assertHttpCreated(r1)

        # Check that the title for geneset we created matches
        r2 = client.get('/api/v1/geneset', format="json")
        self.assertValidJSONResponse(r2)
        self.assertEqual(self.deserialize(r2)['objects'][0]['title'], post_geneset_data['title'])


    def testCreatingGenesetNotLoggedIn(self):
        """
        Test that this fails and returns an Unauthorized response
        """

        client = TestApiClient()

        post_geneset_data = {
            # Does not need user info because the API automatically gathers that from the request
            'title': 'TestGeneset2',
            'organism': '/api/v1/organism/homo-sapiens',
            'abstract': 'Second test geneset created by user.',
            'public' : False,
            'annotations': {55982: [20671152, 19583951], 18091: [8887666], 67087: [], 22410:[]},
            'xrdb': 'Entrez',
            'description': 'First version.',
        }

        # Try to create a geneset without being logged in, check for Unauthorized response
        r1 = client.post('/api/v1/geneset', format="json", data=post_geneset_data)
        self.assertHttpUnauthorized(r1)


    def tearDown(self):
        """
        Remove setup components.

        tearDown is called by django at the end to clean up any changes to the database that occured
        in setUp.
        """
        User.objects.all().delete()


class UserLoginLogoutTestCase(ResourceTestCase):
    """
    Test user login/logout through API UserResource method
    """
    def setUp(self):
        super(UserLoginLogoutTestCase, self).setUp()

        # Have a pre-created user, which we will use for some of the tests
        self.username = "hjkl"
        self.email = "hjkl@example.com"
        self.password = "1234"
        self.user1 = User.objects.create_user(self.username, self.email, self.password)

        # Create the organism 'Human' in the database (not using factory, since it needs to have a resource uri)
        org = Organism.objects.create(common_name="Human", scientific_name="Homo sapiens", slug="homo-sapiens", taxonomy_id=9606)

        # Create a test geneset, which is not public
        self.geneset1 = Geneset.objects.create(
            creator=self.user1, title='TestGeneset1', organism=org, abstract='Test geneset created by user.', public=False)

        # Post data for user 2
        self.post_user2_data = {
            'username': 'asdf',
            'email': 'asdf@example.com',
            'password': 'qwerty'
        }


    def testCheckAuthorizationNotLoggedIn(self):
        """
        Check that any end-user has no access to user objects OR genesets (since
        the only geneset at this point is private) if they are not logged in.
        """
        client = TestApiClient()
        resp = client.get('/api/v1/user', format="json")

        self.assertValidJSONResponse(resp)
        self.assertEqual(self.deserialize(resp)['objects'], [])

        # Check access to genesets
        r2 = client.get('/api/v1/geneset', format="json")
        self.assertValidJSONResponse(r2)
        self.assertEqual(self.deserialize(r2)['objects'], [])


    def testLoggingInWithPreCreatedUser(self):
        """
        Check logging in through API with previously created user. Check access
        to user object AND user's geneset (self.geneset1, which is not public)
        """
        client = TestApiClient()

        client.post('/api/v1/user/login', format="json", data={'username': self.username, 'password': self.password})
        r1 = client.get('/api/v1/user', format="json")

        self.assertValidJSONResponse(r1)
        self.assertEqual(self.deserialize(r1)['objects'][0]['username'], self.username)

        # Check access to user geneset
        r2 = client.get('/api/v1/geneset', format="json")
        self.assertValidJSONResponse(r2)
        self.assertEqual(self.deserialize(r2)['objects'][0]['title'], self.geneset1.title)


    def testLoggingInWrongCredentials1(self):
        """
        Check trying (and failing) to authenticate with a previously created
        user via the API login method. Check both the user object and genesets.
        """
        client = TestApiClient()

        client.post('/api/v1/user/login', format="json", data={'username': self.username, 'password': 'WrongPassword'})
        r1 = client.get('/api/v1/user', format="json")

        self.assertValidJSONResponse(r1)
        self.assertEqual(self.deserialize(r1)['objects'], [])

        # Also check that there is no access to user geneset
        r2 = client.get('/api/v1/geneset', format="json")
        self.assertValidJSONResponse(r2)
        self.assertEqual(self.deserialize(r2)['objects'], [])


    def testLoggingInWithAPICreatedUser(self):
        """
        Check logging in through API with user created through API.
        Enforcing csrf checks through Django/Tastypie test client is not really
        possible.
        """
        client = TestApiClient()

        # Create new user through API
        r1 = client.post('/api/v1/user', format="json", data=self.post_user2_data)
        self.assertHttpCreated(r1)

        # Login through API
        client.post('/api/v1/user/login', format="json", data=self.post_user2_data)

        resp = client.get('/api/v1/user', format="json")
        self.assertValidJSONResponse(resp)
        self.assertEqual(self.deserialize(resp)['objects'][0]['username'], self.post_user2_data['username'])


    def testLoggingInWrongCredentials2(self):
        """
        Test logging in with wrong credentials for a user that was created
        through the API.
        """
        client = TestApiClient()

        client.post('/api/v1/user', format="json", data=self.post_user2_data)
        client.post('/api/v1/user/login', format="json", data={'username': self.post_user2_data['username'], 'password': 'WrongPassword'})
        resp = client.get('/api/v1/user', format="json")

        self.assertValidJSONResponse(resp)
        self.assertEqual(self.deserialize(resp)['objects'], [])

        # Also check that there is no access to user geneset
        r2 = client.get('/api/v1/geneset', format="json")
        self.assertValidJSONResponse(r2)
        self.assertEqual(self.deserialize(r2)['objects'], [])


    def testLoggingOutViaAPI(self):
        """
        Check logging out via API method. Check both the user object and
        genesets.
        """
        client = TestApiClient()

        # Log in
        client.post('/api/v1/user/login', format="json", data={'username': self.username, 'password': self.password})

        # Now, log out
        client.post('/api/v1/user/logout', format="json", data={})

        # Check for access to that user object
        resp = client.get('/api/v1/user', format="json")
        self.assertValidJSONResponse(resp)
        self.assertEqual(self.deserialize(resp)['objects'], [])

        # Also check access that there is no access to user geneset
        r2 = client.get('/api/v1/geneset', format="json")
        self.assertValidJSONResponse(r2)
        self.assertEqual(self.deserialize(r2)['objects'], [])


    def testLoggingOutNotLoggedIn(self):
        """
        Test that this just returns Unauthorized and gives users no access
        to user objects or genesets.
        """
        client = TestApiClient()

        # Try to log out without logging in, check for Unauthorized response
        r1 = client.post('/api/v1/user/logout', format="json", data={})
        self.assertHttpUnauthorized(r1)
        self.assertEqual(self.deserialize(r1)['success'], False)

        # Check that whoever makes this request still has no access to user objects
        r2 = client.get('/api/v1/user', format="json")
        self.assertValidJSONResponse(r2)
        self.assertEqual(self.deserialize(r2)['objects'], [])

        # Also check access that there is no access to user geneset
        r3 = client.get('/api/v1/geneset', format="json")
        self.assertValidJSONResponse(r3)
        self.assertEqual(self.deserialize(r3)['objects'], [])


    def testCreatingAndAccessingGenesetWithCorrectLogin(self):
        client = TestApiClient()

        # Create the second user and log in
        client.post('/api/v1/user', format="json", data=self.post_user2_data)
        client.post('/api/v1/user/login', format="json", data=self.post_user2_data)

        # Create a geneset, check for '201 Created' response
        post_geneset_data = {
            # Does not need user info because the API automatically gathers that from the request
            'title': 'TestGeneset2',
            'organism': '/api/v1/organism/homo-sapiens',
            'abstract': 'Second test geneset created by user.',
            'public' : False,
            'annotations': {55982: [20671152, 19583951], 18091: [8887666], 67087: [], 22410:[]},
            'xrdb': 'Entrez',
            'description': 'First version.',
        }
        r1 = client.post('/api/v1/geneset', format="json", data=post_geneset_data)
        self.assertHttpCreated(r1)

        # Check that the title for geneset we created matches
        r2 = client.get('/api/v1/geneset', format="json")
        self.assertValidJSONResponse(r2)
        self.assertEqual(self.deserialize(r2)['objects'][0]['title'], post_geneset_data['title'])

        # And finally, check that this user only has access to the geneset they created, not the first geneset (created in the setUp method by user1)
        self.assertEqual(len(self.deserialize(r2)['objects']), 1)


    def tearDown(self):
        """
        Remove setup components.

        tearDown is called by django at the end to clean up any changes to the database that occured
        in setUp.
        """
        User.objects.all().delete()


class OAuthTokenTestCase(ResourceTestCase):
    """
    Test authentication using OAuth token
    """

    def setUp(self):
        super(OAuthTokenTestCase, self).setUp()

        # Have a pre-created user, which we will use for some of the tests
        self.username = "hjkl"
        self.email = "hjkl@example.com"
        self.password = "1234"
        self.user1 = User.objects.create_user(self.username, self.email, self.password)

        # Create the organism 'Human' in the database (not using factory, since it needs to have a resource uri)
        org = Organism.objects.create(common_name="Human", scientific_name="Homo sapiens", slug="homo-sapiens", taxonomy_id=9606)

        self.client_application = Application.objects.create(name='testapp', 
            client_id='1111111111111111111111111111111111111111', 
            client_secret='22222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222', 
            client_type='confidential', authorization_grant_type='password',
            redirect_uris='', user=self.user1)

        self.bad_application = Application.objects.create(name='testapp2', 
            client_id='3333333333333333333333333333333333333333', 
            client_secret='44444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444', 
            client_type='confidential', authorization_grant_type='client-credentials',
            redirect_uris='', user=self.user1)


    def testCreatingGenesetWithOAuthToken(self):
        from django.test import Client
        import json

        # For this one, we will use the django test client, since for some
        # reason, the oauth2/token/ url does not like the format of the other
        # requests.
        client = Client()

        payload = {'grant_type': 'password', 'username': self.username,
                   'password': self.password, 'client_id': self.client_application.client_id, 
                   'client_secret': self.client_application.client_secret}

        r1 = client.post('/oauth2/token/', payload)
        response = json.loads(r1.content)

        # Note - this must be converted to a string (from unicode)
        # for OAuth authentication to work.
        access_token = str(response["access_token"])

        post_geneset_data = {
            'title': 'TestGeneset3',
            'organism': '/api/v1/organism/homo-sapiens',
            'abstract': 'Second test geneset created by user.',
            'public' : False,
            'annotations': {55982: [20671152, 19583951], 18091: [8887666],
                            67087: [], 22410:[]},
            'xrdb': 'Entrez',
            'description': 'First version.'
        }

        # Create a geneset, check for '201 Created' response
        # The 'json.dumps' part for json format is important!!!
        r1 = client.post('/api/v1/geneset', json.dumps(post_geneset_data),
                         content_type="application/json",
                         Authorization='OAuth ' + access_token)

        self.assertHttpCreated(r1)

        # Check that the we have access to the geneset we just created with
        # OAuth token and check that title of geneset we created matches.
        r2 = client.get('/api/v1/geneset', Authorization='OAuth ' + access_token)
        self.assertValidJSONResponse(r2)
        self.assertEqual(self.deserialize(r2)['objects'][0]['title'], 
                        post_geneset_data['title'])


    def testWrongAuthGrantTypeNoUser(self):
        """
        Testing that Tribe returns an Unauthorized response if type of
        authorization grant has no user associated with it.
        """
        from django.test import Client
        import json

        # For this one, we will use the django test client, since for some
        # reason, the oauth2/token/ url does not like the format of the other
        # requests.
        client = Client()

        payload = {'grant_type': 'client_credentials', 'username': self.username,
                   'password': self.password, 'client_id': self.bad_application.client_id, 
                   'client_secret': self.bad_application.client_secret}

        r1 = client.post('/oauth2/token/', payload)
        response = json.loads(r1.content)

        # Note - this must be converted to a string (from unicode)
        # for OAuth authentication to work.
        access_token = str(response["access_token"])

        post_geneset_data = {
            'title': 'TestGeneset3',
            'organism': '/api/v1/organism/homo-sapiens',
            'abstract': 'Second test geneset created by user.',
            'public' : False,
            'annotations': {55982: [20671152, 19583951], 18091: [8887666],
                            67087: [], 22410:[]},
            'xrdb': 'Entrez',
            'description': 'First version.'
        }

        # Create a geneset, check for '201 Created' response
        # The 'json.dumps' part for json format is important!!!
        r1 = client.post('/api/v1/geneset', json.dumps(post_geneset_data),
                         content_type="application/json",
                         Authorization='OAuth ' + access_token)

        self.assertHttpUnauthorized(r1)

        # Check that no genesets were created
        self.assertEqual(list(Geneset.objects.all()), [])


    def testCreatingGenesetWithBadOAuthToken(self):
        """
        Try to create a geneset with a false OAuth token - receive a 401-
        Unauthorized response.
        """
        from django.test import Client
        import json

        client = Client()

        post_geneset_data = {
            'title': 'TestGeneset3',
            'organism': '/api/v1/organism/homo-sapiens',
            'abstract': 'Second test geneset created by user.',
            'public' : False,
            'annotations': {55982: [20671152, 19583951], 18091: [8887666],
                            67087: [], 22410:[]},
            'xrdb': 'Entrez',
            'description': 'First version.'
        }

        # Attempt to create a geneset, check for '401 Unauthorized' response
        # The 'json.dumps' part for json format is important!!!
        r1 = client.post('/api/v1/geneset', json.dumps(post_geneset_data),
                         content_type="application/json",
                         Authorization='OAuth asdfasdf')

        self.assertHttpUnauthorized(r1)


    def tearDown(self):
        """
        Remove setup components.

        tearDown is called by django at the end to clean up any changes to
        the database that occured in setUp.
        """
        User.objects.all().delete()