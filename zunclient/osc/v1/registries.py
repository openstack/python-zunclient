# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from osc_lib.command import command
from osc_lib import utils
from oslo_log import log as logging
import six

from zunclient.common import utils as zun_utils
from zunclient import exceptions as exc
from zunclient.i18n import _


def _get_client(obj, parsed_args):
    obj.log.debug("take_action(%s)" % parsed_args)
    return obj.app.client_manager.container


class CreateRegistry(command.ShowOne):
    """Create a registry"""

    log = logging.getLogger(__name__ + ".CreateRegistry")

    def get_parser(self, prog_name):
        parser = super(CreateRegistry, self).get_parser(prog_name)
        parser.add_argument(
            '--name',
            metavar='<name>',
            help='The name of the registry.')
        parser.add_argument(
            '--username',
            metavar='<username>',
            help='The username to login to the registry.')
        parser.add_argument(
            '--password',
            metavar='<password>',
            help='The password to login to the registry.')
        parser.add_argument(
            '--domain',
            metavar='<domain>',
            required=True,
            help='The domain of the registry.')
        return parser

    def take_action(self, parsed_args):
        client = _get_client(self, parsed_args)
        opts = {}
        opts['name'] = parsed_args.name
        opts['domain'] = parsed_args.domain
        opts['username'] = parsed_args.username
        opts['password'] = parsed_args.password
        opts = zun_utils.remove_null_parms(**opts)
        registry = client.registries.create(**opts)
        return zip(*sorted(six.iteritems(registry._info['registry'])))


class ShowRegistry(command.ShowOne):
    """Show a registry"""

    log = logging.getLogger(__name__ + ".ShowRegistry")

    def get_parser(self, prog_name):
        parser = super(ShowRegistry, self).get_parser(prog_name)
        parser.add_argument(
            'registry',
            metavar='<registry>',
            help='ID or name of the registry to show.')
        return parser

    def take_action(self, parsed_args):
        client = _get_client(self, parsed_args)
        opts = {}
        opts['id'] = parsed_args.registry
        opts = zun_utils.remove_null_parms(**opts)
        registry = client.registries.get(**opts)

        return zip(*sorted(six.iteritems(registry._info['registry'])))


class ListRegistry(command.Lister):
    """List available registries"""

    log = logging.getLogger(__name__ + ".ListRegistrys")

    def get_parser(self, prog_name):
        parser = super(ListRegistry, self).get_parser(prog_name)
        parser.add_argument(
            '--all-projects',
            action="store_true",
            default=False,
            help='List registries in all projects')
        parser.add_argument(
            '--marker',
            metavar='<marker>',
            help='The last registry UUID of the previous page; '
                 'displays list of registries after "marker".')
        parser.add_argument(
            '--limit',
            metavar='<limit>',
            type=int,
            help='Maximum number of registries to return')
        parser.add_argument(
            '--sort-key',
            metavar='<sort-key>',
            help='Column to sort results by')
        parser.add_argument(
            '--sort-dir',
            metavar='<sort-dir>',
            choices=['desc', 'asc'],
            help='Direction to sort. "asc" or "desc".')
        parser.add_argument(
            '--name',
            metavar='<name>',
            help='List registries according to their name.')
        parser.add_argument(
            '--domain',
            metavar='<domain>',
            help='List registries according to their domain.')
        parser.add_argument(
            '--project-id',
            metavar='<project-id>',
            help='List registries according to their project_id')
        parser.add_argument(
            '--user-id',
            metavar='<user-id>',
            help='List registries according to their user_id')
        parser.add_argument(
            '--username',
            metavar='<username>',
            help='List registries according to their username')
        return parser

    def take_action(self, parsed_args):
        client = _get_client(self, parsed_args)
        opts = {}
        opts['all_projects'] = parsed_args.all_projects
        opts['marker'] = parsed_args.marker
        opts['limit'] = parsed_args.limit
        opts['sort_key'] = parsed_args.sort_key
        opts['sort_dir'] = parsed_args.sort_dir
        opts['domain'] = parsed_args.domain
        opts['name'] = parsed_args.name
        opts['project_id'] = parsed_args.project_id
        opts['user_id'] = parsed_args.user_id
        opts['username'] = parsed_args.username
        opts = zun_utils.remove_null_parms(**opts)
        registries = client.registries.list(**opts)
        columns = ('uuid', 'name', 'domain', 'username', 'password')
        return (columns, (utils.get_item_properties(registry, columns)
                          for registry in registries))


class DeleteRegistry(command.Command):
    """Delete specified registry(s)"""

    log = logging.getLogger(__name__ + ".Deleteregistry")

    def get_parser(self, prog_name):
        parser = super(DeleteRegistry, self).get_parser(prog_name)
        parser.add_argument(
            'registry',
            metavar='<registry>',
            nargs='+',
            help='ID or name of the registry(s) to delete.')
        return parser

    def take_action(self, parsed_args):
        client = _get_client(self, parsed_args)
        registries = parsed_args.registry
        for registry in registries:
            opts = {}
            opts['id'] = registry
            opts = zun_utils.remove_null_parms(**opts)
            try:
                client.registries.delete(**opts)
                print(_('Request to delete registry %s has been accepted.')
                      % registry)
            except Exception as e:
                print("Delete for registry %(registry)s failed: %(e)s" %
                      {'registry': registry, 'e': e})


class UpdateRegistry(command.ShowOne):
    """Update one or more attributes of the registry"""
    log = logging.getLogger(__name__ + ".UpdateRegistry")

    def get_parser(self, prog_name):
        parser = super(UpdateRegistry, self).get_parser(prog_name)
        parser.add_argument(
            'registry',
            metavar='<registry>',
            help="ID or name of the registry to update.")
        parser.add_argument(
            '--username',
            metavar='<username>',
            help='The new username of registry to update.')
        parser.add_argument(
            '--password',
            metavar='<password>',
            help='The new password of registry to update.')
        parser.add_argument(
            '--name',
            metavar='<name>',
            help='The new name of registry to update.')
        parser.add_argument(
            '--domain',
            metavar='<domain>',
            help='The new domain of registry to update.')
        return parser

    def take_action(self, parsed_args):
        client = _get_client(self, parsed_args)
        registry = parsed_args.registry
        opts = {}
        opts['username'] = parsed_args.username
        opts['password'] = parsed_args.password
        opts['domain'] = parsed_args.domain
        opts['name'] = parsed_args.name
        opts = zun_utils.remove_null_parms(**opts)
        if not opts:
            raise exc.CommandError("You must update at least one property")
        registry = client.registries.update(registry, **opts)
        return zip(*sorted(six.iteritems(registry._info['registry'])))
