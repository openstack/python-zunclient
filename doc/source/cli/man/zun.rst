.. _manpage:

================
Zun CLI man page
================


SYNOPSIS
========

Zun operation use `zun` command, and also support use `openstack` command.

:program:`zun` [options] <command> [command-options]

:program:`openstack` appcontainer <command> [command-options]


DESCRIPTION
===========

The :program:`zun` command line utility interacts with OpenStack Containers
Service (Zun).

In order to use the CLI, you must provide your OpenStack username, password,
project (historically called tenant), and auth endpoint. You can use
configuration options `--os-username`, `--os-password`, `--os-tenant-name` or
`--os-tenant-id`, and `--os-auth-url` or set corresponding environment
variables::

    export OS_USERNAME=user
    export OS_PASSWORD=pass
    export OS_PROJECT_NAME=myproject
    export OS_AUTH_URL=http://auth.example.com:5000/v3
    export OS_USER_DOMAIN_ID=default
    export OS_PROJECT_DOMAIN_ID=default

OPTIONS
=======

To get a list of available commands and options run::

    zun help

To get usage and options of a command::

    zun help <command>

You can also use openstack command as follow.

To get a list of available commands run::

    openstack help appcontainer

To get usage and options of a command::

    openstack appcontainer <command> --help



EXAMPLES
========

List all the containers::

    zun list

Create new container::

    zun run --name container01 IMAGE01

Describe a specific container::

    zun show container01

You can also use openstack command as follow.

List all the containers::

    openstack appcontainer list

Create new container::

    openstack appcontainer run --name container01 IMAGE01

Describe a specific container::

    openstack appcontainer show container01
