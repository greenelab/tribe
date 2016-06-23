Using Tribe
===================================

Tribe helps biologists and bioinformaticists create seamless data mining
pipelines. It stores the user's knowledge base in the form of collections
of genes. These collections can then be shared with collaborators, downloaded
programatically, or used directly by any analysis tool or webserver that is
connected to Tribe.


Authentication
-----------------

In order to create and save collections in Tribe, you can either:

    a) Create an anonymous temporary account, which does not require an email
    address or password, or

    b) Create a full user account, which will allow you to share your
    collections with your collaborators


Temporary anonymous accounts and full user accounts
_____________________________________________________

**Temporary anonymous accounts**

A temporary anonymous account will allow you to create, edit and delete your
own collections. You do not need an email address or password to create a
temporary anonymous account. You will only be able to access this temporary
account from the computer and Internet browser you are currently using to view
this page. You will be able to access your account for 1 year from the date you
create it, until you erase the cookies from this browser, or until you log out
of the account from this browser.

Before your account expires, you will have the option to upgrade your temporary
anonymous account into a full, regular Tribe account by entering an email
address and a password.

**Full user accounts**

A full user account will allow you to share collections and invite collaborators
via email addresses. When running analyses in webservers connected to Tribe
(such as `GIANT <http://giant.princeton.edu>`_), you will also be able login
via Tribe-authentication and access all of your Tribe resources in the client
webserver.

|

Creating and saving collections
----------------------------------

To see examples of how to create and save collections in Tribe, check out
our video tutorials on our
`YouTube channel <https://www.youtube.com/channel/UCuR7hyPD76JyuqEHmJetUjA>`_
or our section on creating collections through our web interface
:ref:`here <creating_collections_web_interface>`


Collection URLs
_____________________________________________________

A concept fundamental to Tribe's functionality is the fact that every
collection resource must have a unique URL.

A collection's URL is made up of a combination of its creator's username
and a shortened (the first 75 characters), url-friendly version of its title.
This means all letters are converted to lower-case and spaces are changed to
hyphens. For example:: 

    If your username in Tribe is "awesomeuser1" and you create a collection
    with the title "Super Collection", then its URL will be:

    "awesomeuser1" + "/" + "super-collection" = "awesomeuser1/super-collection"

Tribe will not allow two collections to have the exact same URL (as it uses
this URL behind the scenes in the API to fetch the resource). Therefore, it will
ask you to pick a different collection title if the new collection url matches
the url for a collection that already exists.