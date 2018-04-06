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


def _get_client(obj, parsed_args):
    obj.log.debug("take_action(%s)" % parsed_args)
    return obj.app.client_manager.container


class ListService(command.Lister):
    """Print a list of zun services."""

    log = logging.getLogger(__name__ + ".ListService")

    def get_parser(self, prog_name):
        parser = super(ListService, self).get_parser(prog_name)
        return parser

    def take_action(self, parsed_args):
        client = _get_client(self, parsed_args)
        services = client.services.list()
        columns = ('Id', 'Host', 'Binary', 'State', 'Disabled',
                   'Disabled Reason', 'Updated At',
                   'Availability Zone')
        return (columns, (utils.get_item_properties(service, columns)
                          for service in services))


class DeleteService(command.Command):
    """Delete the Zun binaries/services."""

    log = logging.getLogger(__name__ + ".DeleteService")

    def get_parser(self, prog_name):
        parser = super(DeleteService, self).get_parser(prog_name)
        parser.add_argument(
            'host',
            metavar='<host>',
            help='Name of host')
        parser.add_argument(
            'binary',
            metavar='<binary>',
            help='Name of the binary to delete')
        return parser

    def take_action(self, parsed_args):
        client = _get_client(self, parsed_args)
        host = parsed_args.host
        binary = parsed_args.binary
        try:
            client.services.delete(host, binary)
            print("Request to delete binary %s on host %s has been accepted." %
                  (binary, host))
        except Exception as e:
            print("Delete for binary %s on host %s failed: %s" %
                  (binary, host, e))


class EnableService(command.ShowOne):
    """Enable the Zun service."""
    log = logging.getLogger(__name__ + ".EnableService")

    def get_parser(self, prog_name):
        parser = super(EnableService, self).get_parser(prog_name)
        parser.add_argument(
            'host',
            metavar='<host>',
            help='Name of host')
        parser.add_argument(
            'binary',
            metavar='<binary>',
            help='Name of the binary to enable')
        return parser

    def take_action(self, parsed_args):
        client = _get_client(self, parsed_args)
        host = parsed_args.host
        binary = parsed_args.binary
        res = client.services.enable(host, binary)
        columns = ('Host', 'Binary', 'Disabled', 'Disabled Reason')
        return columns, (utils.get_dict_properties(res[1]['service'],
                                                   columns))


class DisableService(command.ShowOne):
    """Disable the Zun service."""
    log = logging.getLogger(__name__ + ".DisableService")

    def get_parser(self, prog_name):
        parser = super(DisableService, self).get_parser(prog_name)
        parser.add_argument(
            'host',
            metavar='<host>',
            help='Name of host')
        parser.add_argument(
            'binary',
            metavar='<binary>',
            help='Name of the binary to disable')
        parser.add_argument(
            '--reason',
            metavar='<reason>',
            help='Reason for disabling service')
        return parser

    def take_action(self, parsed_args):
        client = _get_client(self, parsed_args)
        host = parsed_args.host
        binary = parsed_args.binary
        reason = parsed_args.reason
        res = client.services.disable(host, binary, reason)
        columns = ('Host', 'Binary', 'Disabled', 'Disabled Reason')
        return columns, (utils.get_dict_properties(res[1]['service'],
                                                   columns))


class ForceDownService(command.ShowOne):
    """Force the Zun service to down or up."""
    log = logging.getLogger(__name__ + ".ForceDownService")

    def get_parser(self, prog_name):
        parser = super(ForceDownService, self).get_parser(prog_name)
        parser.add_argument(
            'host',
            metavar='<host>',
            help='Name of host')
        parser.add_argument(
            'binary',
            metavar='<binary>',
            help='Name of the binary to disable')
        parser.add_argument(
            '--unset',
            dest='force_down',
            help='Unset the force state down of service',
            action='store_false',
            default=True)
        return parser

    def take_action(self, parsed_args):
        client = _get_client(self, parsed_args)
        host = parsed_args.host
        binary = parsed_args.binary
        force_down = parsed_args.force_down
        res = client.services.force_down(host, binary, force_down)
        columns = ('Host', 'Binary', 'Forced_down')
        return columns, (utils.get_dict_properties(res[1]['service'],
                                                   columns))
