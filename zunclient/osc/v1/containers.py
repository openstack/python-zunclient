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

import logging

from osc_lib.command import command
from osc_lib import utils

from zunclient.common import utils as zun_utils


def _container_columns(container):
    del container._info['links']
    return container._info.keys()


def _get_client(obj, parsed_args):
    obj.log.debug("take_action(%s)" % parsed_args)
    return obj.app.client_manager.container


class CreateContainer(command.ShowOne):
    """Create a container"""

    log = logging.getLogger(__name__ + ".CreateContainer")

    def get_parser(self, prog_name):
        parser = super(CreateContainer, self).get_parser(prog_name)
        parser.add_argument(
            '--name',
            metavar='<name>',
            help='name of the container')
        parser.add_argument(
            '--image',
            required=True,
            metavar='<image>',
            help='name or ID of the image')
        parser.add_argument(
            '--command',
            metavar='<command>',
            help='Send command to the container')
        parser.add_argument(
            '--cpu',
            metavar='<cpu>',
            help='The memory of virtual cpus.')
        parser.add_argument(
            '--memory',
            metavar='<memory>',
            help='The container memory size (format: <number><optional unit>, '
                 'where unit = b, k, m or g)')
        parser.add_argument(
            '--environment',
            metavar='<KEY=VALUE>',
            action='append', default=[],
            help='The environment variabled')
        parser.add_argument(
            '--workdir',
            metavar='<workdir>',
            help='The working directory for commands to run in')
        parser.add_argument(
            '--expose',
            metavar='<port>',
            action='append', default=[],
            help='A port or a list of ports to expose. '
                 'May be used multiple times.')
        parser.add_argument(
            '--hostname',
            metavar='<hostname>',
            help='The hostname to use for the container')
        parser.add_argument(
            '--label',
            metavar='<KEY=VALUE>',
            action='append', default=[],
            help='Adds a map of labels to a container. '
                 'May be used multiple times.')
        parser.add_argument(
            '--image-pull-policy',
            dest='image_pull_policy',
            metavar='<policy>',
            choices=['never', 'always', 'ifnotpresent'],
            help='The policy which determines if the image should '
                 'be pulled prior to starting the container. '
                 'It can have following values: '
                 '"ifnotpresent": only pull the image if it does not '
                 'already exist on the node. '
                 '"always": Always pull the image from repositery.'
                 '"never": never pull the image')
        return parser

    def take_action(self, parsed_args):
        client = _get_client(self, parsed_args)
        opts = {}
        opts['name'] = parsed_args.name
        opts['image'] = parsed_args.image
        opts['command'] = parsed_args.command
        opts['memory'] = parsed_args.memory
        opts['cpu'] = parsed_args.cpu
        opts['environment'] = zun_utils.format_labels(parsed_args.environment)
        opts['workdir'] = parsed_args.workdir
        opts['ports'] = parsed_args.expose
        opts['hostname'] = parsed_args.hostname
        opts['labels'] = zun_utils.format_labels(parsed_args.label)
        opts['image_pull_policy'] = parsed_args.image_pull_policy

        container = client.containers.create(**opts)
        columns = _container_columns(container)
        return columns, utils.get_item_properties(container, columns)


class ShowContainer(command.ShowOne):
    """Show a container"""

    log = logging.getLogger(__name__ + ".ShowContainer")

    def get_parser(self, prog_name):
        parser = super(ShowContainer, self).get_parser(prog_name)
        parser.add_argument(
            'container',
            metavar='<container>',
            help='ID or name of the container to show.')
        return parser

    def take_action(self, parsed_args):
        client = _get_client(self, parsed_args)
        container = parsed_args.container
        container = client.containers.get(container)
        columns = _container_columns(container)
        return columns, utils.get_item_properties(container, columns)