Accessing Tribe through its API
===================================

Tribe makes it easy to programatically retrieve many genesets and collections (and all their versions) at a time, using the gene identifier of preference.


Tribe's API
---------------
Tribe's API can be accessed at http://tribe.greenelab.com/api/v1/?format=json.


.. note:: The '?format=json' querystring allows most web browsers to decode Tribe's API json response. You can append it to the end of any of the following API endpoints.


API Endpoints
---------------


Geneset Endpoint
__________________

API URL:: 

	http://tribe.greenelab.com/api/v1/geneset



This python example uses the requests library to get public genesets from Tribe.

.. code-block:: python

	import requests

	# Define where Tribe is located
	TRIBE_URL = "http://tribe.greenelab.com"

	# Make an initial request to the root.
	r = requests.get(TRIBE_URL + '/api/v1/geneset/')

	# The response from tribe is a json object.
	# The requests library can convert this to
	# a python dictionary.
	result = r.json()

	# Find out how many public collections are 
	# in tribe through 'meta'
	print("Tribe contains " + str(result['meta']['total_count']) + " public collections.")

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
	while result['meta']['next'] is not None:
	    r = requests.get(TRIBE_URL + result['meta']['next'])
	    result = r.json()
	    collections.extend(result['objects'])


Tribe supports full text search of genesets through the query parameter.

.. code-block:: python

	import requests

	# Define where Tribe is located
	TRIBE_URL = "http://tribe.greenelab.com"

	# Define the Tribe geneset endpoint
	GENESET_URL = "http://tribe.greenelab.com/api/v1/geneset"

	# Use the search parameter to perform a full
	# text search.
	parameters = {'query': 'histone acetylation K27'}
	r = requests.get(GENESET_URL, params=parameters)

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


When retrieving collections, getting gene identifiers in the most convenient format is easy with Tribe:

.. code-block:: python

	import requests

	# Code from the code examples to get a collection
	GENESET_URL = "http://tribe.greenelab.com/api/v1/geneset"

	# 'show_tip' includes the most recent version and its
	# genes with the payload.
	parameters = {'show_tip': 'true'}

	r = requests.get(GENESET_URL, params=parameters)
	result = r.json()

	# Get the first collection
	collection = result['objects'][0]

	# The most recently saved version of a collection is the 'tip'
	tip = collection['tip']

	# This prints the list of Entrez identifiers.
	print(tip['genes'])

	# If instead we wanted symbols, we would we would add
	# 'xrdb' to the parameters:
	parameters['xrdb'] = 'Symbol'

	# Then with the same code from before
	r = requests.get(GENESET_URL, params=parameters)
	result = r.json()
	collection = result['objects'][0]
	tip = collection['tip']

	# This now prints a list of symbols.
	print(tip['genes'])

	# In addition to 'Symbol' any database that Tribe knows about
	# can be passed.



Versions Endpoint
___________________

API URL:: 

	http://tribe.greenelab.com/api/v1/version

You can get the full version history from any Tribe collection you have access to 

.. code-block:: python

    import requests

    # Define the Tribe version endpoint
    VERSION_URL = "http://tribe.greenelab.com/api/v1/version"

    # We get the versions for the geneset that matches the title we want:
    parameters = {'geneset__slug': 'go0060260-homo-sapiens-regulation-of-transcription',
                  'xrdb': 'Ensembl'}
    r = requests.get(VERSION_URL, params=parameters)
     
    # The response from tribe is a json object.
    # The requests library can convert this to
    # a python dictionary.
    versions_returned = r.json()['objects']

    print('Date saved\tGenes')
    for version in versions_returned:
        print(str(version['commit_date']) + '\t' + str(version['genes']))





Genes Endpoint
___________________

API URL::

	http://tribe.greenelab.com/api/v1/gene


Tribe supports most common gene identifiers. Currently that means we support Symbol, Ensembl, Entrez, HGNC, HPRD, MGI, MIM, SGD, UniProtKB, TAIR, WormBase, RGD, FLYBASE, ZFIN, Vega, IMGT/GENE-DB, and miRBase. If there's something that we don't support that you'd like to see, please contact us. We'd be happy to help.

**Tribe Translate**
***********************

Tribe also offers a service that lets you translate gene IDs between different gene identifiers programmatically. This example uses the same requests library as the examples above to do this.

.. code-block:: python

	import requests

	# Define the Tribe gene translate endpoint
	GENE_TRANSLATE_URL = "http://tribe.greenelab.com/api/v1/gene/xrid_translate"

	# Enter the type of gene IDs you are translating to and from and fill up
	# the 'gene_list' list with the genes you want translated in the payload parameters.
	# In this case, we will use the following 3 Entrez IDs to translate to Symbols, 
	# but 'from_id' and 'to_id' parameters could be any identifier we support.
	# We can also include an 'organism' parameter and the name of the species we want
	# (this is useful when giving Tribe gene symbols that could belong to different species). 

	gene_list = [6279, 1363, 56892]
	payload = {'from_id': 'Entrez', 'to_id': 'Symbol', 'gene_list': gene_list, 'organism': 'Homo sapiens'} 

	r = requests.post(GENE_TRANSLATE_URL, data=payload)

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

	# As you can see, Tribe returns a results list for each gene that is queried,
	# as well as a list of gene IDs that were entered but were not found.