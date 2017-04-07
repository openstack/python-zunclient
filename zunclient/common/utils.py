#
# Copyright 2012 OpenStack LLC.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import json

from zunclient.common import cliutils as utils
from zunclient import exceptions as exc
from zunclient.i18n import _


def common_filters(marker=None, limit=None, sort_key=None,
                   sort_dir=None, all_tenants=False):
    """Generate common filters for any list request.

    :param all_tenants: list containers in all tenants or not
    :param marker: entity ID from which to start returning entities.
    :param limit: maximum number of entities to return.
    :param sort_key: field to use for sorting.
    :param sort_dir: direction of sorting: 'asc' or 'desc'.
    :returns: list of string filters.
    """
    filters = []
    if all_tenants is True:
        filters.append('all_tenants=1')
    if isinstance(limit, int):
        filters.append('limit=%s' % limit)
    if marker is not None:
        filters.append('marker=%s' % marker)
    if sort_key is not None:
        filters.append('sort_key=%s' % sort_key)
    if sort_dir is not None:
        filters.append('sort_dir=%s' % sort_dir)
    return filters


def split_and_deserialize(string):
    """Split and try to JSON deserialize a string.

    Gets a string with the KEY=VALUE format, split it (using '=' as the
    separator) and try to JSON deserialize the VALUE.
    :returns: A tuple of (key, value).
    """
    try:
        key, value = string.split("=", 1)
    except ValueError:
        raise exc.CommandError(_('Attributes must be a list of '
                                 'PATH=VALUE not "%s"') % string)
    try:
        value = json.loads(value)
    except ValueError:
        pass

    return (key, value)


def args_array_to_patch(attributes):
    patch = []
    for attr in attributes:
        path, value = split_and_deserialize(attr)
        patch.append({path: value})
    return patch


def format_args(args, parse_comma=True):
    '''Reformat a list of key-value arguments into a dict.

    Convert arguments into format expected by the API.
    '''
    if not args:
        return {}

    if parse_comma:
        # expect multiple invocations of --label (or other arguments) but fall
        # back to either , or ; delimited if only one --label is specified
        if len(args) == 1:
            args = args[0].replace(';', ',').split(',')

    fmt_args = {}
    for arg in args:
        try:
            (k, v) = arg.split(('='), 1)
        except ValueError:
            raise exc.CommandError(_('arguments must be a list of KEY=VALUE '
                                     'not %s') % arg)
        if k not in fmt_args:
            fmt_args[k] = v
        else:
            if not isinstance(fmt_args[k], list):
                fmt_args[k] = [fmt_args[k]]
            fmt_args[k].append(v)

    return fmt_args


def print_list_field(field):
    return lambda obj: ', '.join(getattr(obj, field))


def check_restart_policy(policy):
    if ":" in policy:
        name, count = policy.split(":")
        restart_policy = {"Name": name, "MaximumRetryCount": count}
    else:
        restart_policy = {"Name": policy,
                          "MaximumRetryCount": '0'}
    return restart_policy


def remove_null_parms(**kwargs):
    new = {}
    for (key, value) in kwargs.items():
        if value is not None:
            new[key] = value
    return new


def check_container_status(container, status):
    if getattr(container, 'status', None) == status:
        return True
    else:
        return False


def format_container_addresses(container):
    addresses = getattr(container, 'addresses', {})
    output = []
    try:
        for address_name, address_list in addresses.items():
            for a in address_list:
                output.append(a['addr'])
    except Exception:
        pass

    setattr(container, 'addresses', ', '.join(output))
    container._info['addresses'] = ', '.join(output)


def list_containers(containers):
    for c in containers:
        format_container_addresses(c)
    columns = ('uuid', 'name', 'image', 'status', 'task_state', 'addresses',
               'ports')
    utils.print_list(containers, columns,
                     {'versions': print_list_field('versions')},
                     sortby_index=None)
