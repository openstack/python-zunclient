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
from zunclient import exceptions as exc


def _show_registry(registry):
    utils.print_dict(registry._info['registry'])


@utils.arg('--name',
           metavar='<name>',
           help='The name of the registry.')
@utils.arg('--username',
           metavar='<username>',
           help='The username to login to the registry.')
@utils.arg('--password',
           metavar='<password>',
           help='The password to login to the registry.')
@utils.arg('--domain',
           metavar='<domain>',
           required=True,
           help='The domain of the registry.')
def do_registry_create(cs, args):
    """Create a registry."""
    opts = {}
    opts['name'] = args.name
    opts['domain'] = args.domain
    opts['username'] = args.username
    opts['password'] = args.password
    opts = zun_utils.remove_null_parms(**opts)
    _show_registry(cs.registries.create(**opts))


@utils.arg('--all-projects',
           action="store_true",
           default=False,
           help='List registries in all projects')
@utils.arg('--marker',
           metavar='<marker>',
           default=None,
           help='The last registry UUID of the previous page; '
                'displays list of registries after "marker".')
@utils.arg('--limit',
           metavar='<limit>',
           type=int,
           help='Maximum number of registries to return')
@utils.arg('--sort-key',
           metavar='<sort-key>',
           help='Column to sort results by')
@utils.arg('--sort-dir',
           metavar='<sort-dir>',
           choices=['desc', 'asc'],
           help='Direction to sort. "asc" or "desc".')
@utils.arg('--name',
           metavar='<name>',
           help='List registries according to their name.')
@utils.arg('--domain',
           metavar='<domain>',
           help='List registries according to their domain.')
@utils.arg('--project-id',
           metavar='<project-id>',
           help='List registries according to their Project_id')
@utils.arg('--user-id',
           metavar='<user-id>',
           help='List registries according to their user_id')
@utils.arg('--username',
           metavar='<username>',
           help='List registries according to their username')
def do_registry_list(cs, args):
    """Print a list of available registries."""
    opts = {}
    opts['all_projects'] = args.all_projects
    opts['marker'] = args.marker
    opts['limit'] = args.limit
    opts['sort_key'] = args.sort_key
    opts['sort_dir'] = args.sort_dir
    opts['domain'] = args.domain
    opts['name'] = args.name
    opts['project_id'] = args.project_id
    opts['user_id'] = args.user_id
    opts['username'] = args.username
    opts = zun_utils.remove_null_parms(**opts)
    registries = cs.registries.list(**opts)
    columns = ('uuid', 'name', 'domain', 'username', 'password')
    utils.print_list(registries, columns,
                     sortby_index=None)


@utils.arg('registries',
           metavar='<registry>',
           nargs='+',
           help='ID or name of the (registry)s to delete.')
def do_registry_delete(cs, args):
    """Delete specified registries."""
    for registry in args.registries:
        opts = {}
        opts['id'] = registry
        opts = zun_utils.remove_null_parms(**opts)
        try:
            cs.registries.delete(**opts)
            print("Request to delete registry %s has been accepted." %
                  registry)
        except Exception as e:
            print("Delete for registry %(registry)s failed: %(e)s" %
                  {'registry': registry, 'e': e})


@utils.arg('registry',
           metavar='<registry>',
           help='ID or name of the registry to show.')
@utils.arg('-f', '--format',
           metavar='<format>',
           action='store',
           choices=['json', 'yaml', 'table'],
           default='table',
           help='Print representation of the container.'
                'The choices of the output format is json,table,yaml.'
                'Defaults to table.')
def do_registry_show(cs, args):
    """Show details of a registry."""
    opts = {}
    opts['id'] = args.registry
    opts = zun_utils.remove_null_parms(**opts)
    registry = cs.registries.get(**opts)
    if args.format == 'json':
        print(jsonutils.dumps(registry._info, indent=4, sort_keys=True))
    elif args.format == 'yaml':
        print(yaml.safe_dump(registry._info, default_flow_style=False))
    elif args.format == 'table':
        _show_registry(registry)


@utils.arg('registry',
           metavar='<registry>',
           help="ID or name of the registry to update.")
@utils.arg('--username',
           metavar='<username>',
           help='The username login to the registry.')
@utils.arg('--password',
           metavar='<password>',
           help='The domain login to the registry.')
@utils.arg('--domain',
           metavar='<domain>',
           help='The domain of the registry.')
@utils.arg('--name',
           metavar='<name>',
           help='The new name for the registry')
def do_registry_update(cs, args):
    """Update one or more attributes of the registry."""
    opts = {}
    opts['username'] = args.username
    opts['password'] = args.password
    opts['domain'] = args.domain
    opts['name'] = args.name
    opts = zun_utils.remove_null_parms(**opts)
    if not opts:
        raise exc.CommandError("You must update at least one property")
    registry = cs.registries.update(args.registry, **opts)
    _show_registry(registry)
