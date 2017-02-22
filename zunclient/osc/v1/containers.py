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

import argparse
import logging

from osc_lib.command import command
from osc_lib import utils

from zunclient.common import utils as zun_utils
from zunclient import exceptions as exc
from zunclient.i18n import _


def _container_columns(container):
    del container._info['links']
    return container._info.keys()


def _get_client(obj, parsed_args):
    obj.log.debug("take_action(%s)" % parsed_args)
    return obj.app.client_manager.container


def _check_restart_policy(policy):
    if ":" in policy:
        name, count = policy.split(":")
        restart_policy = {"Name": name, "MaximumRetryCount": count}
    else:
        restart_policy = {"Name": policy,
                          "MaximumRetryCount": '0'}
    return restart_policy


def _remove_null_parms(**kwargs):
    new = {}
    for (key, value) in kwargs.items():
        if value:
            new[key] = value
    return new


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
            'image',
            metavar='<image>',
            help='name or ID of the image')
        parser.add_argument(
            '--command',
            metavar='<command>',
            help='Send command to the container')
        parser.add_argument(
            '--cpu',
            metavar='<cpu>',
            help='The number of virtual cpus.')
        parser.add_argument(
            '--memory',
            metavar='<memory>',
            help='The container memory size in MiB')
        parser.add_argument(
            '--environment',
            metavar='<KEY=VALUE>',
            action='append', default=[],
            help='The environment variables')
        parser.add_argument(
            '--workdir',
            metavar='<workdir>',
            help='The working directory for commands to run in')
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
        parser.add_argument(
            '--restart',
            metavar='<restart>',
            help='Restart policy to apply when a container exits'
                 '(no, on-failure[:max-retry], always, unless-stopped)')
        parser.add_argument(
            '--image-driver',
            metavar='<image_driver>',
            help='The image driver to use to pull container image. '
                 'It can have following values: '
                 '"docker": pull the image from Docker Hub. '
                 '"glance": pull the image from Glance. ')
        return parser

    def take_action(self, parsed_args):
        client = _get_client(self, parsed_args)
        opts = {}
        opts['name'] = parsed_args.name
        opts['image'] = parsed_args.image
        opts['command'] = parsed_args.command
        opts['memory'] = parsed_args.memory
        opts['cpu'] = parsed_args.cpu
        opts['environment'] = zun_utils.format_args(parsed_args.environment)
        opts['workdir'] = parsed_args.workdir
        opts['labels'] = zun_utils.format_args(parsed_args.label)
        opts['image_pull_policy'] = parsed_args.image_pull_policy
        opts['image_driver'] = parsed_args.image_driver
        if parsed_args.restart:
            opts['restart_policy'] = _check_restart_policy(parsed_args.restart)

        opts = _remove_null_parms(**opts)
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


class ListContainer(command.Lister):
    """List available containers"""

    log = logging.getLogger(__name__ + ".ListContainers")

    def get_parser(self, prog_name):
        parser = super(ListContainer, self).get_parser(prog_name)
        parser.add_argument(
            '--marker',
            metavar='<marker>',
            help='The last container UUID of the previous page; '
                 'displays list of containers after "marker".')
        parser.add_argument(
            '--limit',
            metavar='<limit>',
            type=int,
            help='Maximum number of containers to return')
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
        opts = _remove_null_parms(**opts)
        containers = client.containers.list(**opts)
        columns = ['uuid', 'name', 'status', 'image', 'command']
        return (columns, (utils.get_item_properties(container, columns)
                          for container in containers))


class DeleteContainer(command.Command):
    """Delete a container"""

    log = logging.getLogger(__name__ + ".Deletecontainer")

    def get_parser(self, prog_name):
        parser = super(DeleteContainer, self).get_parser(prog_name)
        parser.add_argument(
            'container',
            metavar='<container>',
            nargs='+',
            help='ID or name of the (container)s to delete.')
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force delete the container.')
        return parser

    def take_action(self, parsed_args):
        client = _get_client(self, parsed_args)
        containers = parsed_args.container
        force = getattr(parsed_args, 'force')
        for container in containers:
            try:
                client.containers.delete(container, force)
                print(_('Request to delete container %s has been accepted.')
                      % container)
            except Exception as e:
                print("Delete for container %(container)s failed: %(e)s" %
                      {'container': container, 'e': e})


class RebootContainer(command.Command):
    """Reboot specified container"""
    log = logging.getLogger(__name__ + ".RebootContainer")

    def get_parser(self, prog_name):
        parser = super(RebootContainer, self).get_parser(prog_name)
        parser.add_argument(
            'container',
            metavar='<container>',
            nargs='+',
            help='ID or name of the (container)s to reboot.')
        parser.add_argument(
            '--timeout',
            metavar='<timeout>',
            default=10,
            help='Seconds to wait for stop before rebooting (container)s')
        return parser

    def take_action(self, parsed_args):
        client = _get_client(self, parsed_args)
        containers = parsed_args.container
        for container in containers:
            try:
                client.containers.reboot(container, parsed_args.timeout)
                print(_('Request to reboot container %s has been accepted')
                      % container)
            except Exception as e:
                print("Reboot for container %(container)s failed: %(e)s" %
                      {'container': container, 'e': e})


class StartContainer(command.Command):
    """Start specified container"""
    log = logging.getLogger(__name__ + ".StartContainer")

    def get_parser(self, prog_name):
        parser = super(StartContainer, self).get_parser(prog_name)
        parser.add_argument(
            'container',
            metavar='<container>',
            nargs='+',
            help='ID or name of the (container)s to start.')
        return parser

    def take_action(self, parsed_args):
        client = _get_client(self, parsed_args)
        containers = parsed_args.container
        for container in containers:
            try:
                client.containers.start(container)
                print(_('Request to start container %s has been accepted')
                      % container)
            except Exception as e:
                print("Start for container %(container)s failed: %(e)s" %
                      {'container': container, 'e': e})


class PauseContainer(command.Command):
    """Pause specified container"""
    log = logging.getLogger(__name__ + ".PauseContainer")

    def get_parser(self, prog_name):
        parser = super(PauseContainer, self).get_parser(prog_name)
        parser.add_argument(
            'container',
            metavar='<container>',
            nargs='+',
            help='ID or name of the (container)s to pause.')
        return parser

    def take_action(self, parsed_args):
        client = _get_client(self, parsed_args)
        containers = parsed_args.container
        for container in containers:
            try:
                client.containers.pause(container)
                print(_('Request to pause container %s has been accepted')
                      % container)
            except Exception as e:
                print("Pause for container %(container)s failed: %(e)s" %
                      {'container': container, 'e': e})


class UnpauseContainer(command.Command):
    """unpause specified container"""
    log = logging.getLogger(__name__ + ".UnpauseContainer")

    def get_parser(self, prog_name):
        parser = super(UnpauseContainer, self).get_parser(prog_name)
        parser.add_argument(
            'container',
            metavar='<container>',
            nargs='+',
            help='ID or name of the (container)s to unpause.')
        return parser

    def take_action(self, parsed_args):
        client = _get_client(self, parsed_args)
        containers = parsed_args.container
        for container in containers:
            try:
                client.containers.unpause(container)
                print(_('Request to unpause container %s has been accepted')
                      % container)
            except Exception as e:
                print("unpause for container %(container)s failed: %(e)s" %
                      {'container': container, 'e': e})


class ExecContainer(command.Command):
    """Execute specified container"""
    log = logging.getLogger(__name__ + ".ExecContainer")

    def get_parser(self, prog_name):
        parser = super(ExecContainer, self).get_parser(prog_name)
        parser.add_argument(
            'container',
            metavar='<container>',
            help='ID or name of the container to execute command in.')
        parser.add_argument(
            'command',
            metavar='<command>',
            nargs=argparse.REMAINDER,
            help='The command to execute.')
        return parser

    def take_action(self, parsed_args):
        client = _get_client(self, parsed_args)
        container = parsed_args.container
        command = ' '.join(parsed_args.command)
        output = client.containers.execute(container, command)
        print(output)


class LogsContainer(command.Command):
    """Get logs of a container"""
    log = logging.getLogger(__name__ + ".LogsContainer")

    def get_parser(self, prog_name):
        parser = super(LogsContainer, self).get_parser(prog_name)
        parser.add_argument(
            'container',
            metavar='<container>',
            help='ID or name of the container to get logs for.')
        parser.add_argument(
            '--stdout',
            action='store_true',
            help='Only stdout logs of container.')
        parser.add_argument(
            '--stderr',
            action='store_true',
            help='Only stderr logs of container.')
        return parser

    def take_action(self, parsed_args):
        client = _get_client(self, parsed_args)
        container = parsed_args.container
        stdout = parsed_args.stdout
        stderr = parsed_args.stderr
        logs = client.containers.logs(container, stdout, stderr)
        print(logs)


class KillContainer(command.Command):
    """Kill signal to a container"""

    log = logging.getLogger(__name__ + ".KillContainers")

    def get_parser(self, prog_name):
        parser = super(KillContainer, self).get_parser(prog_name)
        parser.add_argument(
            'container',
            metavar='<container>',
            help='ID or name of the container to kill signal to.')
        parser.add_argument(
            '--signal',
            metavar='<signal>',
            default=None,
            help='The signal to kill')
        return parser

    def take_action(self, parsed_args):
        client = _get_client(self, parsed_args)
        container = parsed_args.container
        opts = {}
        opts['id'] = parsed_args.container
        opts['signal'] = parsed_args.signal
        opts = _remove_null_parms(**opts)
        try:
            client.containers.kill(**opts)
            print(_('Request to send kill signal to container %s has '
                    'been accepted') % container)
        except Exception as e:
            print("kill signal for container %(container)s failed: %(e)s" %
                  {'container': container, 'e': e})


class StopContainer(command.Command):
    """Stop specified containers"""

    log = logging.getLogger(__name__ + ".StopContainer")

    def get_parser(self, prog_name):
        parser = super(StopContainer, self).get_parser(prog_name)
        parser.add_argument(
            'container',
            metavar='<container>',
            nargs='+',
            help='ID or name of the (container)s to stop.')
        parser.add_argument(
            '--timeout',
            metavar='<timeout>',
            default=10,
            help='Seconds to wait for stop before killing (container)s')
        return parser

    def take_action(self, parsed_args):
        client = _get_client(self, parsed_args)
        containers = parsed_args.container
        for container in containers:
            try:
                client.containers.stop(container, parsed_args.timeout)
                print(_('Request to stop container %s has been accepted.')
                      % container)
            except Exception as e:
                print("Stop for container %(container)s failed: %(e)s" %
                      {'container': container, 'e': e})


class RunContainer(command.ShowOne):
    """Creates and run a new container"""

    log = logging.getLogger(__name__ + ".RunContainer")

    def get_parser(self, prog_name):
        parser = super(RunContainer, self).get_parser(prog_name)
        parser.add_argument(
            '--name',
            metavar='<name>',
            help='name of the container')
        parser.add_argument(
            'image',
            metavar='<image>',
            help='name or ID of the image')
        parser.add_argument(
            '--command',
            metavar='<command>',
            help='Send command to the container')
        parser.add_argument(
            '--cpu',
            metavar='<cpu>',
            help='The number of virtual cpus.')
        parser.add_argument(
            '--memory',
            metavar='<memory>',
            help='The container memory size in MiB')
        parser.add_argument(
            '--environment',
            metavar='<KEY=VALUE>',
            action='append', default=[],
            help='The environment variables')
        parser.add_argument(
            '--workdir',
            metavar='<workdir>',
            help='The working directory for commands to run in')
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
        parser.add_argument(
            '--restart',
            metavar='<restart>',
            help='Restart policy to apply when a container exits'
                 '(no, on-failure[:max-retry], always, unless-stopped)')
        parser.add_argument(
            '--image-driver',
            metavar='<image_driver>',
            help='The image driver to use to pull container image. '
                 'It can have following values: '
                 '"docker": pull the image from Docker Hub. '
                 '"glance": pull the image from Glance. ')
        return parser

    def take_action(self, parsed_args):
        client = _get_client(self, parsed_args)
        opts = {}
        opts['name'] = parsed_args.name
        opts['image'] = parsed_args.image
        opts['command'] = parsed_args.command
        opts['memory'] = parsed_args.memory
        opts['cpu'] = parsed_args.cpu
        opts['environment'] = zun_utils.format_args(parsed_args.environment)
        opts['workdir'] = parsed_args.workdir
        opts['labels'] = zun_utils.format_args(parsed_args.label)
        opts['image_pull_policy'] = parsed_args.image_pull_policy
        opts['image_driver'] = parsed_args.image_driver
        if parsed_args.restart:
            opts['restart_policy'] = _check_restart_policy(parsed_args.restart)

        opts = _remove_null_parms(**opts)
        container = client.containers.run(**opts)
        columns = _container_columns(container)
        return columns, utils.get_item_properties(container, columns)


class RenameContainer(command.Command):
    """rename specified container"""
    log = logging.getLogger(__name__ + ".RenameContainer")

    def get_parser(self, prog_name):
        parser = super(RenameContainer, self).get_parser(prog_name)
        parser.add_argument(
            'container',
            metavar='<container>',
            help='ID or name of the container to rename.')
        parser.add_argument(
            'name',
            metavar='<name>',
            help='The new name for the container')
        return parser

    def take_action(self, parsed_args):
        client = _get_client(self, parsed_args)
        container = parsed_args.container
        name = parsed_args.name
        try:
            client.containers.rename(container, name)
            print(_('Request to rename container %s has been accepted')
                  % container)
        except Exception as e:
            print("rename for container %(container)s failed: %(e)s" %
                  {'container': container, 'e': e})


class TopContainer(command.Command):
    """display the running progesses inside the container"""
    log = logging.getLogger(__name__ + ".TopContainer")

    def get_parser(self, prog_name):
        parser = super(TopContainer, self).get_parser(prog_name)
        parser.add_argument(
            'container',
            metavar='<container>',
            help='ID or name of the container to display progesses.')
        parser.add_argument(
            'ps_args',
            metavar='<ps_args>',
            nargs=argparse.REMAINDER,
            help='The args of the ps command.')
        return parser

    def take_action(self, parsed_args):
        client = _get_client(self, parsed_args)
        container = parsed_args.container
        ps = ' '.join(parsed_args.ps_args)
        output = client.containers.top(container, ps)
        for titles in output['Titles']:
            print("%-20s") % titles,
        for process in output['Processes']:
            print("")
            for info in process:
                print("%-20s") % info,


class UpdateContainer(command.Command):
    """Updates one or more container attributes"""
    log = logging.getLogger(__name__ + ".UpdateContainer")

    def get_parser(self, prog_name):
        parser = super(UpdateContainer, self).get_parser(prog_name)
        parser.add_argument(
            'container',
            metavar='<container>',
            help="ID or name of the container to udate.")
        parser.add_argument(
            '--cpu',
            metavar='<cpu>',
            help='The number of virtual cpus.')
        parser.add_argument(
            '--memory',
            metavar='<memory>',
            help='The container memory size in MiB')
        return parser

    def take_action(self, parsed_args):
        client = _get_client(self, parsed_args)
        container = parsed_args.container
        opts = {}
        opts['memory'] = parsed_args.memory
        opts['cpu'] = parsed_args.cpu
        opts = _remove_null_parms(**opts)
        if not opts:
            raise exc.CommandError("You must update at least one property")
        try:
            client.containers.update(container, **opts)
            print(_('Request to update container %s has been accepted')
                  % container)
        except Exception as e:
            print("update for container %(container)s failed: %(e)s" %
                  {'container': container, 'e': e})
