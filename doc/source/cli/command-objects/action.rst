===================
appcontainer action
===================

An **appcontainer action** specifies the action details for a container.

appcontainer action list
------------------------

List actions on a container

.. program:: appcontainer action list
.. code:: bash

    openstack appcontainer action list [-h]
                                       [-f {csv,json,table,value,yaml}]
                                       [-c COLUMN] [--max-width <integer>]
                                       [--fit-width] [--print-empty]
                                       [--noindent]
                                       [--quote {all,minimal,none,nonnumeric}]
                                       [--sort-column SORT_COLUMN]
                                       <container>

.. describe:: <container>

    ID or name of the container to list actions.

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

    Fit the table to the display width. Implied if --max-width
    greater than 0. Set the environment variable
    CLIFF_FIT_WIDTH=1 to always enable

.. option:: --print-empty

    Print empty table if there is no data to show.

.. option:: --noindent

    whether to disable indenting the JSON

.. option:: --quote {all,minimal,none,nonnumeric}

    when to include quotes, defaults to nonnumeric

appcontainer action show
------------------------

Shows action

.. program:: appcontainer action show
.. code:: bash

    openstack appcontainer action show [-h]
                                       [-f {json,shell,table,value,yaml}]
                                       [-c COLUMN] [--max-width <integer>]
                                       [--fit-width] [--print-empty]
                                       [--noindent] [--prefix PREFIX]
                                       <container> <request_id>

.. describe:: <container>

    ID or name of the container to show.

.. describe:: <request_id>

    request ID of action to describe.

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

    Fit the table to the display width. Implied if --max-width
    greater than 0. Set the environment variable CLIFF_FIT_WIDTH
    =1 to always enable

.. option:: --print-empty

    Print empty table if there is no data to show.

.. option:: --noindent

   whether to disable indenting the JSON

.. option:: --prefix PREFIX

    add a prefix to all variable names
