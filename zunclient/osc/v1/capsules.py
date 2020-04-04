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

from zunclient.common import template_utils
from zunclient.common import utils as zun_utils
from zunclient.i18n import _


def _capsule_columns(capsule):
    return capsule._info.keys()


def _get_client(obj, parsed_args):
    obj.log.debug("take_action(%s)" % parsed_args)
    return obj.app.client_manager.container


class CreateCapsule(command.ShowOne):
    """Create a capsule"""

    log = logging.getLogger(__name__ + ".CreateCapsule")

    def get_parser(self, prog_name):
        parser = super(CreateCapsule, self).get_parser(prog_name)
        parser.add_argument(
            '--file',
            metavar='<template_file>',
            required=True,
            help='Path to the capsule template file.')
        return parser

    def take_action(self, parsed_args):
        client = _get_client(self, parsed_args)
        opts = {}
        opts['template'] = template_utils.get_template_contents(
            parsed_args.file)
        capsule = client.capsules.create(**opts)
        columns = _capsule_columns(capsule)
        return columns, utils.get_item_properties(capsule, columns)


class ShowCapsule(command.ShowOne):
    """Show a capsule"""

    log = logging.getLogger(__name__ + ".ShowCapsule")

    def get_parser(self, prog_name):
        parser = super(ShowCapsule, self).get_parser(prog_name)
        parser.add_argument(
            'capsule',
            metavar='<capsule>',
            help='ID or name of the capsule to show.')
        return parser

    def take_action(self, parsed_args):
        client = _get_client(self, parsed_args)
        opts = {}
        opts['id'] = parsed_args.capsule
        opts = zun_utils.remove_null_parms(**opts)
        capsule = client.capsules.get(**opts)
        zun_utils.format_container_addresses(capsule)
        columns = _capsule_columns(capsule)
        return columns, utils.get_item_properties(capsule, columns)


class ListCapsule(command.Lister):
    """List available capsules"""

    log = logging.getLogger(__name__ + ".ListCapsule")

    def get_parser(self, prog_name):
        parser = super(ListCapsule, self).get_parser(prog_name)
        parser.add_argument(
            '--all-projects',
            action="store_true",
            default=False,
            help='List capsules in all projects')
        parser.add_argument(
            '--marker',
            metavar='<marker>',
            help='The last capsule UUID of the previous page; '
                 'displays list of capsules after "marker".')
        parser.add_argument(
            '--limit',
            metavar='<limit>',
            type=int,
            help='Maximum number of capsules to return')
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
        opts['all_projects'] = parsed_args.all_projects
        opts['marker'] = parsed_args.marker
        opts['limit'] = parsed_args.limit
        opts['sort_key'] = parsed_args.sort_key
        opts['sort_dir'] = parsed_args.sort_dir
        opts = zun_utils.remove_null_parms(**opts)
        capsules = client.capsules.list(**opts)
        for capsule in capsules:
            zun_utils.format_container_addresses(capsule)
        columns = ('uuid', 'name', 'status', 'addresses')
        return (columns, (utils.get_item_properties(capsule, columns)
                          for capsule in capsules))


class DeleteCapsule(command.Command):
    """Delete specified capsule(s)"""

    log = logging.getLogger(__name__ + ".DeleteCapsule")

    def get_parser(self, prog_name):
        parser = super(DeleteCapsule, self).get_parser(prog_name)
        parser.add_argument(
            'capsule',
            metavar='<capsule>',
            nargs='+',
            help='ID or name of the capsule(s) to delete.')
        return parser

    def take_action(self, parsed_args):
        client = _get_client(self, parsed_args)
        capsules = parsed_args.capsule
        for capsule in capsules:
            opts = {}
            opts['id'] = capsule
            try:
                client.capsules.delete(**opts)
                print(_('Request to delete capsule %s has been accepted.')
                      % capsule)
            except Exception as e:
                print("Delete for capsule %(capsule)s failed: %(e)s" %
                      {'capsule': capsule, 'e': e})
