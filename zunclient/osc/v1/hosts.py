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

from oslo_log import log as logging

from osc_lib.command import command
from osc_lib import utils

from zunclient.common import utils as zun_utils


def _host_columns(host):
    return host._info.keys()


def _get_client(obj, parsed_args):
    obj.log.debug("take_action(%s)" % parsed_args)
    return obj.app.client_manager.container


class ListHost(command.Lister):
    """List available hosts"""

    log = logging.getLogger(__name__ + ".ListHost")

    def get_parser(self, prog_name):
        parser = super(ListHost, self).get_parser(prog_name)
        parser.add_argument(
            '--marker',
            metavar='<marker>',
            default=None,
            help='The last host UUID of the previous page; '
                 'displays list of hosts after "marker".')
        parser.add_argument(
            '--limit',
            metavar='<limit>',
            type=int,
            help='Maximum number of hosts to return')
        parser.add_argument(
            '--sort-key',
            metavar='<sort-key>',
            help='Column to sort results by')
        parser.add_argument(
            '--sort-dir',
            metavar='<sort-dir>',
            choices=['desc', 'asc'],
            help='Direction to sort. "asc" or "desc".')
        return parser

    def take_action(self, parsed_args):
        client = _get_client(self, parsed_args)
        opts = {}
        opts['marker'] = parsed_args.marker
        opts['limit'] = parsed_args.limit
        opts['sort_key'] = parsed_args.sort_key
        opts['sort_dir'] = parsed_args.sort_dir
        opts = zun_utils.remove_null_parms(**opts)
        hosts = client.hosts.list(**opts)
        columns = ('uuid', 'hostname', 'mem_total', 'cpus', 'disk_total')
        return (columns, (utils.get_item_properties(host, columns)
                          for host in hosts))


class ShowHost(command.ShowOne):
    """Show a host"""

    log = logging.getLogger(__name__ + ".ShowHost")

    def get_parser(self, prog_name):
        parser = super(ShowHost, self).get_parser(prog_name)
        parser.add_argument(
            'host',
            metavar='<host>',
            help='ID or name of the host to show.')
        return parser

    def take_action(self, parsed_args):
        client = _get_client(self, parsed_args)
        host = parsed_args.host
        host = client.hosts.get(host)
        columns = _host_columns(host)

        return columns, utils.get_item_properties(host, columns)
