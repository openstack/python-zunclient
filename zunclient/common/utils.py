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

import base64
import binascii
import os
import re

from oslo_serialization import jsonutils
from oslo_utils import netutils
import six
from six.moves.urllib import parse
from six.moves.urllib import request
from zunclient.common.apiclient import exceptions as apiexec
from zunclient.common import cliutils as utils
from zunclient import exceptions as exc
from zunclient.i18n import _

VALID_UNITS = (
    K,
    M,
    G,
) = (
    1024,
    1024 * 1024,
    1024 * 1024 * 1024,
)


def common_filters(marker=None, limit=None, sort_key=None,
                   sort_dir=None, all_projects=False):
    """Generate common filters for any list request.

    :param all_projects: list containers in all projects or not
    :param marker: entity ID from which to start returning entities.
    :param limit: maximum number of entities to return.
    :param sort_key: field to use for sorting.
    :param sort_dir: direction of sorting: 'asc' or 'desc'.
    :returns: list of string filters.
    """
    filters = []
    if all_projects is True:
        filters.append('all_projects=1')
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
        value = jsonutils.loads(value)
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


def check_commit_container_args(commit_args):
    opts = {}
    if commit_args.repository is not None:
        if ':' in commit_args.repository:
            args_list = commit_args.repository.rsplit(':')
            opts['repository'] = args_list[0]
            opts['tag'] = args_list[1]
        else:
            opts['repository'] = commit_args.repository
    return opts


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
    networks = []
    try:
        for address_name, address_list in addresses.items():
            for a in address_list:
                output.append(a['addr'])
            networks.append(address_name)
    except Exception:
        pass

    setattr(container, 'addresses', ', '.join(output))
    setattr(container, 'networks', ', '.join(networks))
    container._info['addresses'] = ', '.join(output)
    container._info['networks'] = ', '.join(networks)


def list_containers(containers):
    for c in containers:
        format_container_addresses(c)
    columns = ('uuid', 'name', 'image', 'status', 'task_state', 'addresses',
               'ports')
    utils.print_list(containers, columns,
                     {'versions': print_list_field('versions')},
                     sortby_index=None)


def list_availability_zones(zones):
    columns = ('availability_zone',)
    utils.print_list(zones, columns,
                     {'versions': print_list_field('versions')},
                     sortby_index=None)


def parse_command(command):
    output = []
    if command:
        if isinstance(command, six.string_types):
            command = [command]
        for c in command:
            c = '"' + c + '"'
            output.append(c)
    return " ".join(output)


def parse_mounts(mounts):
    err_msg = ("Invalid mounts argument '%s'. mounts arguments must be of "
               "the form --mount source=<volume>,destination=<path>, "
               "or use --mount size=<size>,destination=<path> to create "
               "a new volume and mount to the container, "
               "or use --mount type=bind,source=<file>,destination=<path> "
               "to inject file into a path in the container.")
    parsed_mounts = []
    for mount in mounts:
        keys = ["source", "destination", "size", "type"]
        mount_info = {}
        for mnt in mount.split(","):
            try:
                k, v = mnt.split("=", 1)
                k = k.strip()
                v = v.strip()
            except ValueError:
                raise apiexec.CommandError(err_msg % mnt)
            if k in keys:
                if mount_info.get(k):
                    raise apiexec.CommandError(err_msg % mnt)
                mount_info[k] = v
            else:
                raise apiexec.CommandError(err_msg % mnt)

        if not mount_info.get('destination'):
            raise apiexec.CommandError(err_msg % mount)

        if not mount_info.get('source') and not mount_info.get('size'):
            raise apiexec.CommandError(err_msg % mount)

        type = mount_info.get('type', 'volume')
        if type not in ('volume', 'bind'):
            mnt = "type=%s" % type
            raise apiexec.CommandError(err_msg % mnt)

        if type == 'bind':
            # TODO(hongbin): handle the case that 'source' is a directory
            filename = mount_info.pop('source')
            with open(filename, 'rb') as file:
                mount_info['source'] = file.read()

        parsed_mounts.append(mount_info)
    return parsed_mounts


def parse_nets(ns):
    err_msg = ("Invalid nets argument '%s'. nets arguments must be of "
               "the form --nets <network=network, v4-fixed-ip=ip-addr,"
               "v6-fixed-ip=ip-addr, port=port-uuid>, "
               "with only one of network, or port specified.")
    nets = []
    for net_str in ns:
        keys = ["network", "port", "v4-fixed-ip", "v6-fixed-ip"]
        net_info = {}
        for kv_str in net_str.split(","):
            try:
                k, v = kv_str.split("=", 1)
                k = k.strip()
                v = v.strip()
            except ValueError:
                raise apiexec.CommandError(err_msg % net_str)
            if k in keys:
                if net_info.get(k):
                    raise apiexec.CommandError(err_msg % net_str)
                net_info[k] = v
            else:
                raise apiexec.CommandError(err_msg % net_str)

        if net_info.get('v4-fixed-ip') and not netutils.is_valid_ipv4(
                net_info['v4-fixed-ip']):
            raise apiexec.CommandError("Invalid ipv4 address.")

        if net_info.get('v6-fixed-ip') and not netutils.is_valid_ipv6(
                net_info['v6-fixed-ip']):
            raise apiexec.CommandError("Invalid ipv6 address.")

        if bool(net_info.get('network')) == bool(net_info.get('port')):
            raise apiexec.CommandError(err_msg % net_str)

        nets.append(net_info)
    return nets


def parse_health(hc_str):
    err_msg = ("Invalid healthcheck argument '%s'. healthcheck arguments"
               " must be of the form --healthcheck <cmd='command',"
               "interval=time,retries=integer,timeout=time>, and the unit "
               "of time is s(seconds), m(minutes), h(hours).") % hc_str
    keys = ["cmd", "interval", "retries", "timeout"]
    health_info = {}
    for kv_str in hc_str[0].split(","):
        try:
            k, v = kv_str.split("=", 1)
            k = k.strip()
            v = v.strip()
        except ValueError:
            raise apiexec.CommandError(err_msg)
        if k in keys:
            if health_info.get(k):
                raise apiexec.CommandError(err_msg)
            elif k in ['interval', 'timeout']:
                health_info[k] = _convert_healthcheck_para(v, err_msg)
            elif k == "retries":
                health_info[k] = int(v)
            else:
                health_info[k] = v
        else:
            raise apiexec.CommandError(err_msg)
    return health_info


def _convert_healthcheck_para(time, err_msg):
    int_pattern = '^\d+$'
    time_pattern = '^\d+(s|m|h)$'
    ret = 0
    if re.match(int_pattern, time):
        ret = int(time)
    elif re.match(time_pattern, time):
        if time.endswith('s'):
            ret = int(time.split('s')[0])
        elif time.endswith('m'):
            ret = int(time.split('m')[0]) * 60
        elif time.endswith('h'):
            ret = int(time.split('h')[0]) * 3600
    else:
        raise apiexec.CommandError(err_msg)
    return ret


def parse_exposed_ports(ports):
    return {p: {} for p in ports}


def normalise_file_path_to_url(path):
    if parse.urlparse(path).scheme:
        return path
    path = os.path.abspath(path)
    return parse.urljoin('file:', request.pathname2url(path))


def base_url_for_url(url):
    parsed = parse.urlparse(url)
    parsed_dir = os.path.dirname(parsed.path)
    return parse.urljoin(url, parsed_dir)


def list_capsules(capsules):
    for c in capsules:
        format_container_addresses(c)
    columns = ('uuid', 'name', 'status', 'addresses')
    utils.print_list(capsules, columns,
                     {'versions': print_list_field('versions')},
                     sortby_index=None)


def format_fixed_ips(fixed_ips):
    if fixed_ips is None:
        return None

    return ",".join([fip['ip_address'] for fip in fixed_ips])


def format_network_fixed_ips(network):
    return format_fixed_ips(network.fixed_ips)


def list_container_networks(networks):
    columns = ('net_id', 'port_id', 'fixed_ips')
    utils.print_list(networks, columns,
                     {'fixed_ips': format_network_fixed_ips},
                     sortby_index=None)


def encode_file_data(data):
    if six.PY3 and isinstance(data, str):
        data = data.encode('utf-8')
    return base64.b64encode(data).decode('utf-8')


def decode_file_data(data):
    # Py3 raises binascii.Error instead of TypeError as in Py27
    try:
        return base64.b64decode(data)
    except (TypeError, binascii.Error):
        raise exc.CommandError(_('Invalid Base 64 file data.'))
