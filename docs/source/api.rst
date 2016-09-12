Accessing Tribe through its API
===================================

Tribe makes it easy to programmatically retrieve many genesets and collections
(and all their versions) at a time, using your gene identifier of preference.


Tribe's API
---------------
Tribe's API can be accessed at https://tribe.greenelab.com/api/v1/?format=json.


.. note:: 

    The '?format=json' querystring allows most web browsers to decode
    Tribe's API json response. You can append it to the end of any of the
    following API endpoints.

|

API Endpoints
---------------

**Organisms Endpoint**
______________________

API URL:: 

    https://tribe.greenelab.com/api/v1/organism


Fetching organisms in Tribe
***************************
 
This python example uses the 
`requests <http://docs.python-requests.org/en/latest/>`_ library to get a
list of organisms currently supported by Tribe.

.. code-block:: python

    import requests

    # Define where Tribe is located
    TRIBE_URL = "https://tribe.greenelab.com"

    # Make a GET request to the organisms endpoint:
    r = requests.get(TRIBE_URL + '/api/v1/organism')

    # The response from tribe is a json object.
    # The requests library can convert this to
    # a python dictionary.
    result = r.json()

    # Find out how many organisms are currently supported in Tribe 
    # by looking up the 'total_count' in the 'meta' section of the
    # response object.
    print("Tribe contains " + str(result['meta']['total_count']) +
          " organisms.")

    # Print out this list of organisms:
    for org_object in result['objects']:
        print(org_object['scientific_name'])


**Cross-Reference Databases Endpoint**
______________________________________

API URL:: 

    https://tribe.greenelab.com/api/v1/crossrefdb


Tribe's database contains many types of gene identifiers used by
different cross-reference gene databases. These include Entrez,
Ensembl, and UniProtKB.

Getting list of cross-reference gene identifier types in Tribe
**************************************************************
 
This python example uses the 
`requests <http://docs.python-requests.org/en/latest/>`_ library to get a
list of gene identifier types currently supported by Tribe.

.. code-block:: python

    import requests

    # Define where Tribe is located
    TRIBE_URL = "https://tribe.greenelab.com"

    # Make a GET request to the cross-reference databases endpoint:
    r = requests.get(TRIBE_URL + '/api/v1/crossrefdb')

    # The response from tribe is a json object.
    # The requests library can convert this to
    # a python dictionary.
    result = r.json()

    # Print out the list of cross-reference gene identifier types
    # currently supported by Tribe:
    for crossref_db_object in result['objects']:
        print(crossref_db_object['name'])


**Geneset Endpoint**
______________________

API URL:: 

    https://tribe.greenelab.com/api/v1/geneset


Retrieving public genesets
*****************************
 
This python example uses the 
`requests <http://docs.python-requests.org/en/latest/>`_ library to get public
genesets from Tribe.

.. code-block:: python

    import requests

    # Define where Tribe is located
    TRIBE_URL = "https://tribe.greenelab.com"

    # Make an initial request to the root geneset endpoint
    r = requests.get(TRIBE_URL + '/api/v1/geneset/')

    # The response from tribe is a json object.
    # The requests library can convert this to
    # a python dictionary.
    result = r.json()

    # Find out how many public collections are 
    # in tribe through 'meta'
    print("Tribe contains " + str(result['meta']['total_count']) +
          " public collections.")

    # 'meta' also supports pagination (providing 
    # api links to next and previous) so that
    # one can easily iterate through all collections.
    # 'meta' contains information about the request 
    # for requests that return a set of objects. 

    collections = []
    # Objects themselves are provided through 'objects'
    collections.extend(result['objects'])

    # Iterate over every collection and extend
    # the collections array. This example uses
    # 'next' from 'meta' to iterate over all
    # pages of results.
    # Warning: There are thousands of publicly available
    # collections/genesets in Tribe, so be prepared to get a very long
    # ``collections`` list at the end of this!
    while result['meta']['next'] is not None:
        r = requests.get(TRIBE_URL + result['meta']['next'])
        result = r.json()
        collections.extend(result['objects'])


Searching for genesets via the API
***********************************

Tribe supports full text search of genesets through the ``'query'`` parameter.

.. code-block:: python

    import requests

    # Define where Tribe is located
    TRIBE_URL = "https://tribe.greenelab.com"

    # Use the search parameter to perform a full
    # text search through all genesets in Tribe.
    parameters = {'query': 'histone acetylation K27'}

    # Make a GET request to the geneset endpoint
    r = requests.get(TRIBE_URL + '/api/v1/geneset/', params=parameters)

    # The response from tribe is a json object.
    # The requests library can convert this to
    # a python dictionary.
    result = r.json()

    # Print all matching collections
    while True:
        for collection in result['objects']:
            print("Title: " + collection['title'])
        if result['meta']['next'] is None:
            break
        r = requests.get(TRIBE_URL + result['meta']['next'])
        result = r.json()

    # Running the above code prints:
    # Title: GO-BP-0043974:histone H3-K27 acetylation
    # Title: GO-BP-1901674:regulation of histone H3-K27 acetylation
    # Title: GO-BP-1901675:negative regulation of histone H3-K27 acetylation
    # Title: GO-BP-1901676:positive regulation of histone H3-K27 acetylation


Fetching a geneset's genes
****************************

When retrieving collections, getting gene identifiers in the most convenient
format is easy with Tribe. We use the ``'show_tip'`` parameter to retrieve the
most recent collection version and all of its genes, using whatever gene
identifier we want.

.. code-block:: python

    import requests

    # Define where Tribe is located
    TRIBE_URL = "https://tribe.greenelab.com"

    # 'show_tip' includes the most recent version and its
    # genes with the payload.
    parameters = {'show_tip': 'true'}

    # Make a GET request to the geneset endpoint
    r = requests.get(TRIBE_URL + '/api/v1/geneset/', params=parameters)
    result = r.json()

    # Get the first collection
    collection = result['objects'][0]

    # The most recently saved version of a collection is the 'tip'
    tip = collection['tip']

    # Print all genes in this 'tip' version. By default, Tribe returns genes
    # using Entrez identifiers.
    print(tip['genes'])

    # If instead we wanted symbols, we would we would add
    # 'xrdb' to the parameters:
    parameters['xrdb'] = 'Symbol'

    # Then use the same code as before
    r = requests.get(TRIBE_URL + '/api/v1/geneset/', params=parameters)
    result = r.json()
    collection = result['objects'][0]
    tip = collection['tip']

    # This now prints a list of symbols.
    print(tip['genes'])


In addition to 'Symbol', any database that Tribe knows about can be passed.
Click :ref:`here<supported_organisms_and_identifiers>` for a full list of
supported gene identifiers/databases.

If you find a collection via the Tribe web interface (such as
https://tribe.greenelab.com/#/use/detail/annotation.refinery/go0060260-homo-sapiens),
and you want to get its latest list of genes as Entrez identifiers, you can
build a similar request using the last part of this url
('annotation.refinery/go0060260-homo-sapiens').

.. note:: 

    The key is to know that this geneset's specific url
    is defined by the the last two fragments of the url: 
        a) The geneset creator's username ("annotation.refinery/"), and
        b) A url-friendly version of its ID and species ("go0060260-homo-sapiens")


.. code-block:: python

    import requests

    # Define where Tribe is located
    TRIBE_URL = "https://tribe.greenelab.com"

    # Concatenate the string for our desired geneset's specific url, adding
    # the geneset api endpoint ('/api/v1/geneset/'), 'annotation.refinery/' for
    # the creator username, and 'go0060260-homo-sapiens' for url-friendly
    # version of its ID and species.
    specific_geneset_url = TRIBE_URL + '/api/v1/geneset/' + 'annotation.refinery/' + \
                           'go0060260-homo-sapiens'

    parameters = {'show_tip': 'true'}

    # Make a GET request to that geneset's endpoint
    r = requests.get(specific_geneset_url, params=parameters)
    result = r.json()

    # Get the most recently saved version ('tip')
    tip = result['tip']

    # Print all genes in this 'tip' version. By default, Tribe returns genes
    # using Entrez identifiers.
    print(tip['genes'])

    # Again, if we wanted another gene identifier instead of Entrez IDs, we
    # would we would add it as an 'xrdb' to the parameters:
    parameters['xrdb'] = 'Ensembl'

    # Then use the same code as before
    r = requests.get(specific_geneset_url, params=parameters)
    result = r.json()
    tip = result['tip']

    # This now prints a list of this geneset's genes as Ensembl IDs.
    print(tip['genes'])

|

**Versions Endpoint**
________________________

API URL:: 

    https://tribe.greenelab.com/api/v1/version

You can get the full version history from any Tribe collection you have access
to

.. code-block:: python

    import requests

    # Define where Tribe is located
    TRIBE_URL = "https://tribe.greenelab.com"

    # We get the versions for the geneset that matches the title we want:
    parameters = {
        'geneset__slug': 'go0060260-homo-sapiens',
        'xrdb': 'Ensembl'
        }

    # Make a GET request to the versions endpoint
    r = requests.get(TRIBE_URL + '/api/v1/version', params=parameters)
     
    # The response from tribe is a json object.
    # The requests library can convert this to
    # a python dictionary.
    versions_returned = r.json()['objects']

    print('Date saved\tGenes')
    for version in versions_returned:
        print(str(version['commit_date']) + '\t' + str(version['genes']))

|

**Genes Endpoint**
_____________________

API URL::

    https://tribe.greenelab.com/api/v1/gene


Tribe supports most common gene identifiers. Currently that means we support
Symbol, Ensembl, Entrez, HGNC, HPRD, MGI, MIM, SGD, UniProtKB, TAIR, WormBase,
RGD, FLYBASE, ZFIN, Vega, IMGT/GENE-DB, and miRBase. If there's something that
we don't support that you'd like to see, please
`contact us <tribe.greenelab@gmail.com>`_. We'd be happy to help.

**Tribe Translate**
***********************

Tribe also offers a service that lets you translate gene IDs between different
gene identifiers programmatically. The URL for Tribe's gene translate endpoint
is::

    https://tribe.greenelab.com/api/v1/gene/xrid_translate


The following example uses the same
`requests <http://docs.python-requests.org/en/latest/>`_ library as the
examples above to translate 3 genes from Entrez identifiers to Symbols.
However, you can use Tribe Translate to translate hundreds of genes at a time.

.. code-block:: python

    import requests

    # Define the Tribe gene translate endpoint
    TRIBE_URL = "https://tribe.greenelab.com"

    # Enter the type of gene IDs you are translating to and from and fill up
    # the 'gene_list' list with the genes you want translated in the payload
    # parameters. In this case, we will use the following 3 Entrez IDs to 
    # translate to Symbols, but 'from_id' and 'to_id' parameters could be any
    # identifier we support. We can also include an 'organism' parameter and
    # the name of the species we want (this is useful when giving Tribe gene
    # symbols that could belong to different species). 

    gene_list = [6279, 1363, 56892]
    payload = {'from_id': 'Entrez', 'to_id': 'Symbol', 'gene_list': gene_list,
               'organism': 'Homo sapiens'}

    # Make a POST request to the gene translation endpoint
    r = requests.post(TRIBE_URL + '/api/v1/gene/xrid_translate', data=payload)

    # The response from tribe is a json object.
    # The requests library can convert this to
    # a python dictionary.
    result_dictionary = r.json()

    # Print the results of this request:
    for gene_query, search_result in result_dictionary.iteritems():
        print(gene_query + ": " + str(search_result))

    # Running the above code prints:
    # 6279: [u'S100A8']
    # not_found: []
    # 1363: [u'CPE']
    # 56892: [u'C8orf4']

    # As shown, Tribe returns a results list for each gene that is queried,
    # as well as a list of gene IDs that were entered but were not found.

|

Creating new resources through Tribe's API
---------------------------------------------
Creating new genesets and versions of these genesets is easy through Tribe's
API using the `OAuth2 <http://oauth.net/2/>`_ protocol. 

If you have a server built using
`Django <https://docs.djangoproject.com/en/dev/>`_, you can follow the steps in
the :ref:`tribe_client<tribe_client-quickstart>` package section.

If you are looking to create resources via some other application or tool, you
can follow these steps:

1. First, you must register your client application/tool at
https://tribe.greenelab.com/oauth2/applications/. Make sure to:

  a. Be logged-in using your Tribe account
  b. Select "Confidential" under ``Client type`` and
  c. Select "Resource owner password-based" under ``Authorization grant type``

  .. note:: 

    Currently, Tribe supports the following ``Authorization grant types``:

      * Authorization code
      * Resource owner password-based

    and does not support the following:

      * Implicit
      * Client credentials


2. Write down and save the Client ID and the Client secret that are assigned
to you. Your application/tool will need these when requesting an OAuth token
from Tribe to create resources.

3. Now you can create new genesets and versions using the Client ID, secret,
and your username and password.

  .. note:: 

    The OAuth token is configured to expire **14 days** from when it was created.


The following code is an example of how you
might go about doing this. This code also uses
`requests <http://docs.python-requests.org/en/latest/>`_.

.. code-block:: python

    # Sample code to remotely create a new geneset/collection on Tribe.
    # This sample geneset is based on this GO term collection:
    # https://tribe.greenelab.com/#/use/detail/annotation.refinery/go0060260-mus-musculus

    # This script uses the 'requests' python library:
    # http://docs.python-requests.org/en/latest/
    import requests
    import json

    # Define where Tribe is located
    TRIBE_URL = "https://tribe.greenelab.com"

    # Function to get access_token
    def obtain_token_using_credentials(username, password, client_id, client_secret):
    	oauth_url = TRIBE_URL + '/oauth2/token/'
    	payload = {'grant_type': 'password', 'username': username, 'password': password, 'client_id': client_id, 'client_secret': client_secret}
    	r = requests.post(oauth_url, data=payload)
    	tribe_response = r.json()
    	print(tribe_response)
    	return tribe_response['access_token']

    # Start by defining a dictionary of our geneset payload
    geneset = {}

    # The API requires the organism to be the organism's URI, which is just '/api/v1/organism/' plus the url-friendly version of the species name
    geneset['organism'] = "/api/v1/organism/mus-musculus"

    geneset['title'] = 'Sample RNA polymerase II geneset - created remotely'
    geneset['abstract'] = 'Any process that modulates the rate, frequency or extent of a process involved in starting transcription from an RNA polymerase II promoter.'
    geneset['public'] = False # You will want to make this True  if you want anybody to be able to see your geneset

    # For this geneset's annotations, we will use the Entrez IDs for four of
    # the genes in the GO term (Paxip1, Nkx2-5, Ctnnbip1, and Wnt10b), and
    # the pubmed IDs of related publications for each gene. (The whole 
    # list of the annotations for the original collection can also be found at:
    # https://tribe.greenelab.com/#/use/detail/annotation.refinery/go0060260-mus-musculus)
    geneset['annotations'] = {55982: [20671152, 19583951], 18091: [8887666], 67087: [], 22410:[]}
    geneset['xrdb'] = 'Entrez'
    geneset['description'] = 'First version' # Description for the first version - this is optional

    # Get our access_token
    # ***** MUST FILL OUT username, password, client_id and client_secret!!!! *****
    access_token = obtain_token_using_credentials(username, password, client_id, client_secret)

    # This next part creates the post request
    headers = {'Authorization': 'OAuth ' + access_token, 'Content-Type': 'application/json'}
    payload = json.dumps(geneset)
    genesets_url = TRIBE_URL + '/api/v1/geneset'
    r = requests.post(genesets_url, data=payload, headers=headers)
    print(r)
    response = r.json()
    print(response)

    # Once you have created a geneset, you can new versions of it at will.

    # First, we get this new geneset's resource_uri from the response we just got:
    geneset_uri = response['resource_uri']

    # We just created the first version of our geneset, so we will get the resource_uri
    # for it to assign it as the parent of the new version we are about to create.
    headers = {'Authorization': 'OAuth ' + access_token, 'Content-Type': 'application/json'}
    r = requests.get(TRIBE_URL + geneset_uri, params={'show_tip': 'true'}, headers=headers)
    print(r)
    response = r.json()
    print(response)
    parent_uri = response['tip']['resource_uri']

    # Say we want our new annotations to be the following (say we want to remove
    # gene Ctnnbip1):
    new_annotation_dict = {55982: [20671152, 19583951],
                           18091: [8887666], 22410:[]}

    version = {"geneset": geneset_uri, "parent": parent_uri,
    "annotations": new_annotation_dict, "xrdb": "Entrez",
    "description": "Removing gene Ctnnbip1"}

    headers = {'Authorization': 'OAuth ' + access_token, 'Content-Type': 'application/json'}
    payload = json.dumps(version)
    versions_url = TRIBE_URL + '/api/v1/version'
    r = requests.post(versions_url, data=payload, headers=headers)
    print(r)
    response = r.json()
    print(response)