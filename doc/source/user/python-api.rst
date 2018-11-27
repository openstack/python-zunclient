================================
 The :mod:`zunclient` Python API
================================

.. module:: zunclient
   :synopsis: A client for the OpenStack Zun API.

.. currentmodule:: zunclient

Usage
-----

First create a client instance with your credentials::

    >>> from zunclient import client
    >>> zun = client.Client(VERSION, auth_url=AUTH_URL, username=USERNAME,
    ...                     password=PASSWORD, project_name=PROJECT_NAME,
    ...                     user_domain_name='default',
    ...                     project_domain_name='default')

Here ``VERSION`` can be a string or ``zunclient.api_versions.APIVersion`` obj.
If you prefer string value, you can use ``1`` or
``1.X`` (where X is a microversion).

Alternatively, you can create a client instance using the keystoneauth
session API::

    >>> from keystoneauth1 import loading
    >>> from keystoneauth1 import session
    >>> from zunclient import client
    >>> loader = loading.get_plugin_loader('password')
    >>> auth = loader.load_from_options(auth_url=AUTH_URL,
    ...                                 username=USERNAME,
    ...                                 password=PASSWORD,
    ...                                 project_name=PROJECT_NAME,
    ...                                 user_domain_name='default',
    ...                                 project_domain_name='default')
    >>> sess = session.Session(auth=auth)
    >>> zun = client.Client(VERSION, session=sess)

If you have PROJECT_NAME instead of a PROJECT_ID, use the project_name
parameter. Similarly, if your cloud uses keystone v3 and you have a DOMAIN_NAME
or DOMAIN_ID, provide it as `user_domain_(name|id)` and if you are using a
PROJECT_NAME also provide the domain information as `project_domain_(name|id)`.

Then call methods on its managers::

    >>> zun.containers.list()
    [<Container {...}>]

    >>> zun.containers.run(name="my-container", image='nginx')
    <Container {...}>
