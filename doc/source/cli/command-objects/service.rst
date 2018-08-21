====================
appcontainer service
====================

An **appcontainer service** specifies the zun services.

appcontainer service list
-------------------------

Print a list of zun services

.. program:: appcontainer service list
.. code:: bash

    openstack appcontainer service list [-h]
                                        [-f {csv,json,table,value,yaml}]
                                        [-c COLUMN] [--max-width <integer>]
                                        [--fit-width] [--print-empty]
                                        [--noindent]
                                        [--quote {all,minimal,none,nonnumeric}]
                                        [--sort-column SORT_COLUMN]

.. option:: -h, --help

    show this help message and exit

.. option:: -f {csv,json,table,value,yaml},
            --format {csv,json,table,value,yaml}

    the output format, defaults to table

.. option:: -c COLUMN, --column COLUMN

    specify the column(s) to include, can be repeated

.. option:: --sort-column SORT_COLUMN

    specify the column(s) to sort the data (columns
    specified first have a priority, non-existing columns
    are ignored), can be repeated

.. option:: --max-width <integer>

    Maximum display width, <1 to disable. You can also use
    the CLIFF_MAX_TERM_WIDTH environment variable, but the
    parameter takes precedence.

.. option:: --fit-width

    Fit the table to the display width. Implied if --max-
    width greater than 0. Set the environment variable
    CLIFF_FIT_WIDTH=1 to always enable

.. option:: --print-empty

    Print empty table if there is no data to show.

.. option:: --noindent

    whether to disable indenting the JSON

.. option:: --quote {all,minimal,none,nonnumeric}

    when to include quotes, defaults to nonnumeric

appcontainer service delete
---------------------------

Delete the Zun binaries/services.

.. program:: appcontainer service delete
.. code:: bash

    openstack appcontainer service delete [-h] <host> <binary>

.. describe:: <host>

    Name of host

.. describe:: <binary>

    Name of the binary to delete

.. option:: -h, --help

    show this help message and exit

appcontainer service forcedown
------------------------------

Force the Zun service to down or up.

.. program:: appcontainer service forcedown
.. code:: bash

    openstack appcontainer service forcedown [-h]
                                             [-f {json,shell,table,value,yaml}]
                                             [-c COLUMN]
                                             [--max-width <integer>]
                                             [--fit-width] [--print-empty]
                                             [--noindent] [--prefix PREFIX]
                                             [--unset]
                                             <host> <binary>

.. describe:: <host>

    Name of host

.. describe:: <binary>

    Name of the binary to forcedown

.. option:: -h, --help

    show this help message and exit

.. option:: --unset

    Unset the force state down of service

.. option:: -f {json,shell,table,value,yaml},
            --format {json,shell,table,value,yaml}

    the output format, defaults to table

.. option:: -c COLUMN, --column COLUMN

    specify the column(s) to include, can be repeated

.. option:: --max-width <integer>

     Maximum display width, <1 to disable. You can also use
     the CLIFF_MAX_TERM_WIDTH environment variable, but the
     parameter takes precedence.

.. option:: --fit-width

    Fit the table to the display width. Implied if --max-
    width greater than 0. Set the environment variable
    CLIFF_FIT_WIDTH=1 to always enable

.. option:: --print-empty

    Print empty table if there is no data to show.

.. option:: --noindent

    whether to disable indenting the JSON

.. option:: --prefix PREFIX

    add a prefix to all variable names
