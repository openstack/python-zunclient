==================
appcontainer image
==================

An **appcontainer image** specifies the image for a host.

appcontainer image list
-----------------------

List available images

.. program:: appcontainer image list
.. code:: bash

    openstack appcontainer image list [-h] [-f {csv,json,table,value,yaml}]
                                      [-c COLUMN] [--max-width <integer>]
                                      [--fit-width] [--print-empty]
                                      [--noindent]
                                      [--quote {all,minimal,none,nonnumeric}]
                                      [--sort-column SORT_COLUMN]
                                      [--marker <marker>] [--limit <limit>]
                                      [--sort-key <sort-key>]
                                      [--sort-dir <sort-dir>]

.. option:: -h, --help

    show this help message and exit

.. option:: --marker <marker>

    The last host UUID of the previous page; displays list
    of hosts after "marker".

.. option:: --limit <limit>

    Maximum number of hosts to return

.. option:: --sort-key <sort-key>

    Column to sort results by

.. option:: --sort-dir <sort-dir>

    Direction to sort. "asc" or "desc".

.. option:: -f {csv,json,table,value,yaml},
            --format {csv,json,table,value,yaml}

    the output format, defaults to table

.. option::  -c COLUMN, --column COLUMN

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

appcontainer image show
-----------------------

Describe a specific image

.. program:: appcontainer image show
.. code:: bash

     openstack appcontainer image show [-h]
                                       [-f {json,shell,table,value,yaml}]
                                       [-c COLUMN] [--max-width <integer>]
                                       [--fit-width] [--print-empty]
                                       [--noindent] [--prefix PREFIX]
                                       <uuid>

.. describe:: <uuid>

    UUID of image to describe

.. option:: -h, --help

    show this help message and exit

.. option::  -f {json,shell,table,value,yaml},
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

.. option::  --prefix PREFIX

    add a prefix to all variable names
