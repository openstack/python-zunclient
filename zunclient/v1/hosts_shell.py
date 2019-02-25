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

import yaml

from oslo_serialization import jsonutils

from zunclient.common import cliutils as utils
from zunclient.common import utils as zun_utils


@utils.arg('--marker',
           metavar='<marker>',
           default=None,
           help='The last host UUID of the previous page; '
                'displays list of hosts after "marker".')
@utils.arg('--limit',
           metavar='<limit>',
           type=int,
           help='Maximum number of hosts to return')
@utils.arg('--sort-key',
           metavar='<sort-key>',
           help='Column to sort results by')
@utils.arg('--sort-dir',
           metavar='<sort-dir>',
           choices=['desc', 'asc'],
           help='Direction to sort. "asc" or "desc".')
def do_host_list(cs, args):
    """Print a list of available host."""
    opts = {}
    opts['marker'] = args.marker
    opts['limit'] = args.limit
    opts['sort_key'] = args.sort_key
    opts['sort_dir'] = args.sort_dir
    opts = zun_utils.remove_null_parms(**opts)
    hosts = cs.hosts.list(**opts)
    columns = ('uuid', 'hostname', 'mem_total', 'cpus', 'disk_total')
    utils.print_list(hosts, columns,
                     {'versions': zun_utils.print_list_field('versions')},
                     sortby_index=None)


@utils.arg('host',
           metavar='<host>',
           help='ID or name of the host to show.')
@utils.arg('-f', '--format',
           metavar='<format>',
           action='store',
           choices=['json', 'yaml', 'table'],
           default='table',
           help='Print representation of the host.'
                'The choices of the output format is json,table,yaml.'
                'Defaults to table.')
def do_host_show(cs, args):
    """Show details of a host."""
    host = cs.hosts.get(args.host)
    if args.format == 'json':
        print(jsonutils.dumps(host._info, indent=4, sort_keys=True))
    elif args.format == 'yaml':
        print(yaml.safe_dump(host._info, default_flow_style=False))
    elif args.format == 'table':
        utils.print_dict(host._info)
