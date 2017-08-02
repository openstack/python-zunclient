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
from contextlib import closing
import io
import logging
import os
import tarfile
import time

from osc_lib.command import command
from osc_lib import utils

from zunclient.common import utils as zun_utils
from zunclient.common.websocketclient import exceptions
from zunclient.common.websocketclient import websocketclient
from zunclient import exceptions as exc
from zunclient.i18n import _


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
            'image',
            metavar='<image>',
            help='name or ID of the image')
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
                 '"always": Always pull the image from repository.'
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
        parser.add_argument(
            '--interactive',
            dest='interactive',
            action='store_true',
            default=False,
            help='Keep STDIN open even if not attached, allocate a pseudo-TTY')
        parser.add_argument(
            '--security-group',
            metavar='<security_group>',
            action='append', default=[],
            help='The name of security group for the container. '
                 'May be used multiple times.')
        parser.add_argument(
            'command',
            metavar='<command>',
            nargs=argparse.REMAINDER,
            help='Send command to the container')
        parser.add_argument(
            '--hint',
            metavar='<key=value>',
            action='append',
            default=[],
            help='The key-value pair(s) for scheduler to select host. '
                 'The format of this parameter is "key=value[,key=value]". '
                 'May be used multiple times.')
        parser.add_argument(
            '--net',
            metavar='<auto, networks=networks, port=port-uuid,'
                    'v4-fixed-ip=ip-addr,v6-fixed-ip=ip-addr>',
            action='append',
            default=[],
            help='Create network enpoints for the container. '
                 'auto: do not specify the network, zun will automatically '
                 'create one. '
                 'network: attach container to the specified neutron networks.'
                 ' port: attach container to the neutron port with this UUID. '
                 'v4-fixed-ip: IPv4 fixed address for container. '
                 'v6-fixed-ip: IPv6 fixed address for container.')
        parser.add_argument(
            '--rm',
            dest='auto_remove',
            action='store_true',
            default=False,
            help='Automatically remove the container when it exits')
        return parser

    def take_action(self, parsed_args):
        client = _get_client(self, parsed_args)
        opts = {}
        opts['name'] = parsed_args.name
        opts['image'] = parsed_args.image
        opts['memory'] = parsed_args.memory
        opts['cpu'] = parsed_args.cpu
        opts['environment'] = zun_utils.format_args(parsed_args.environment)
        opts['workdir'] = parsed_args.workdir
        opts['labels'] = zun_utils.format_args(parsed_args.label)
        opts['image_pull_policy'] = parsed_args.image_pull_policy
        opts['image_driver'] = parsed_args.image_driver
        opts['auto_remove'] = parsed_args.auto_remove
        if parsed_args.security_group:
            opts['security_groups'] = parsed_args.security_group
        if parsed_args.command:
            opts['command'] = zun_utils.parse_command(parsed_args.command)
        if parsed_args.restart:
            opts['restart_policy'] = \
                zun_utils.check_restart_policy(parsed_args.restart)
        if parsed_args.interactive:
            opts['interactive'] = True
        opts['hints'] = zun_utils.format_args(parsed_args.hint)
        opts['nets'] = zun_utils.parse_nets(parsed_args.net)

        opts = zun_utils.remove_null_parms(**opts)
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
        parser.add_argument(
            '--all-tenants',
            action="store_true",
            default=False,
            help='Show container(s) in all tenant by name.')
        return parser

    def take_action(self, parsed_args):
        client = _get_client(self, parsed_args)
        opts = {}
        opts['id'] = parsed_args.container
        opts['all_tenants'] = parsed_args.all_tenants
        opts = zun_utils.remove_null_parms(**opts)
        container = client.containers.get(**opts)
        columns = _container_columns(container)

        return columns, utils.get_item_properties(container, columns)


class ListContainer(command.Lister):
    """List available containers"""

    log = logging.getLogger(__name__ + ".ListContainers")

    def get_parser(self, prog_name):
        parser = super(ListContainer, self).get_parser(prog_name)
        parser.add_argument(
            '--all-tenants',
            action="store_true",
            default=False,
            help='List containers in all tenants')
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
        opts['all_tenants'] = parsed_args.all_tenants
        opts['marker'] = parsed_args.marker
        opts['limit'] = parsed_args.limit
        opts['sort_key'] = parsed_args.sort_key
        opts['sort_dir'] = parsed_args.sort_dir
        opts = zun_utils.remove_null_parms(**opts)
        containers = client.containers.list(**opts)
        for c in containers:
            zun_utils.format_container_addresses(c)
        columns = ('uuid', 'name', 'image', 'status', 'task_state',
                   'addresses', 'ports')
        return (columns, (utils.get_item_properties(container, columns)
                          for container in containers))


class DeleteContainer(command.Command):
    """Delete specified container(s)"""

    log = logging.getLogger(__name__ + ".Deletecontainer")

    def get_parser(self, prog_name):
        parser = super(DeleteContainer, self).get_parser(prog_name)
        parser.add_argument(
            'container',
            metavar='<container>',
            nargs='+',
            help='ID or name of the container(s) to delete.')
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force delete the container.')
        parser.add_argument(
            '--all-tenants',
            action="store_true",
            default=False,
            help='Delete container(s) in all tenant by name.')
        return parser

    def take_action(self, parsed_args):
        client = _get_client(self, parsed_args)
        containers = parsed_args.container
        for container in containers:
            opts = {}
            opts['id'] = container
            opts['force'] = parsed_args.force
            opts['all_tenants'] = parsed_args.all_tenants
            opts = zun_utils.remove_null_parms(**opts)
            try:
                client.containers.delete(**opts)
                print(_('Request to delete container %s has been accepted.')
                      % container)
            except Exception as e:
                print("Delete for container %(container)s failed: %(e)s" %
                      {'container': container, 'e': e})


class RestartContainer(command.Command):
    """Restart specified container"""
    log = logging.getLogger(__name__ + ".RestartContainer")

    def get_parser(self, prog_name):
        parser = super(RestartContainer, self).get_parser(prog_name)
        parser.add_argument(
            'container',
            metavar='<container>',
            nargs='+',
            help='ID or name of the (container)s to restart.')
        parser.add_argument(
            '--timeout',
            metavar='<timeout>',
            default=10,
            help='Seconds to wait for stop before restarting (container)s')
        return parser

    def take_action(self, parsed_args):
        client = _get_client(self, parsed_args)
        containers = parsed_args.container
        for container in containers:
            try:
                client.containers.restart(container, parsed_args.timeout)
                print(_('Request to restart container %s has been accepted')
                      % container)
            except Exception as e:
                print("Restart for container %(container)s failed: %(e)s" %
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
    """Execute command in a running container"""
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
        parser.add_argument(
            '--interactive',
            dest='interactive',
            action='store_true',
            default=False,
            help='Keep STDIN open and allocate a pseudo-TTY for interactive')
        return parser

    def take_action(self, parsed_args):
        client = _get_client(self, parsed_args)
        container = parsed_args.container
        opts = {}
        opts['command'] = zun_utils.parse_command(parsed_args.command)
        if parsed_args.interactive:
            opts['interactive'] = True
            opts['run'] = False
        response = client.containers.execute(container, **opts)
        if parsed_args.interactive:
            exec_id = response['exec_id']
            url = response['url']
            websocketclient.do_exec(client, url, container, exec_id, "~", 0.5)
        else:
            output = response['output']
            exit_code = response['exit_code']
            print(output)
            return exit_code


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
        parser.add_argument(
            '--since',
            metavar='<since>',
            default=None,
            help='Show logs since a given datetime or integer '
                 'epoch (in seconds).')
        parser.add_argument(
            '--timestamps',
            dest='timestamps',
            action='store_true',
            default=False,
            help='Show timestamps.')
        parser.add_argument(
            '--tail',
            metavar='<tail>',
            default='all',
            help='Number of lines to show from the end of the logs.')
        return parser

    def take_action(self, parsed_args):
        client = _get_client(self, parsed_args)
        opts = {}
        opts['id'] = parsed_args.container
        opts['stdout'] = parsed_args.stdout
        opts['stderr'] = parsed_args.stderr
        opts['since'] = parsed_args.since
        opts['timestamps'] = parsed_args.timestamps
        opts['tail'] = parsed_args.tail
        opts = zun_utils.remove_null_parms(**opts)
        logs = client.containers.logs(**opts)
        print(logs)


class KillContainer(command.Command):
    """Kill one or more running container(s)"""
    log = logging.getLogger(__name__ + ".KillContainers")

    def get_parser(self, prog_name):
        parser = super(KillContainer, self).get_parser(prog_name)
        parser.add_argument(
            'containers',
            metavar='<container>',
            nargs='+',
            help='ID or name of the (container)s to kill.')
        parser.add_argument(
            '--signal',
            metavar='<signal>',
            default=None,
            help='The signal to kill')
        return parser

    def take_action(self, parsed_args):
        client = _get_client(self, parsed_args)
        for container in parsed_args.containers:
            opts = {}
            opts['id'] = container
            opts['signal'] = parsed_args.signal
            opts = zun_utils.remove_null_parms(**opts)
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
    """Create and run a new container"""

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
                 '"always": Always pull the image from repository.'
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
        parser.add_argument(
            '--interactive',
            dest='interactive',
            action='store_true',
            default=False,
            help='Keep STDIN open even if not attached, allocate a pseudo-TTY')
        parser.add_argument(
            '--security-group',
            metavar='<security_group>',
            action='append', default=[],
            help='The name of security group for the container. '
                 'May be used multiple times.')
        parser.add_argument(
            'command',
            metavar='<command>',
            nargs=argparse.REMAINDER,
            help='Send command to the container')
        parser.add_argument(
            '--hint',
            metavar='<key=value>',
            action='append',
            default=[],
            help='The key-value pair(s) for scheduler to select host. '
                 'The format of this parameter is "key=value[,key=value]". '
                 'May be used multiple times.')
        parser.add_argument(
            '--net',
            metavar='<auto, networks=networks, port=port-uuid,'
                    'v4-fixed-ip=ip-addr,v6-fixed-ip=ip-addr>',
            action='append',
            default=[],
            help='Create network enpoints for the container. '
                 'auto: do not specify the network, zun will automatically '
                 'create one. '
                 'network: attach container to the specified neutron networks.'
                 ' port: attach container to the neutron port with this UUID. '
                 'v4-fixed-ip: IPv4 fixed address for container. '
                 'v6-fixed-ip: IPv6 fixed address for container.')
        parser.add_argument(
            '--rm',
            dest='auto_remove',
            action='store_true',
            default=False,
            help='Automatically remove the container when it exits')
        return parser

    def take_action(self, parsed_args):
        client = _get_client(self, parsed_args)
        opts = {}
        opts['name'] = parsed_args.name
        opts['image'] = parsed_args.image
        opts['memory'] = parsed_args.memory
        opts['cpu'] = parsed_args.cpu
        opts['environment'] = zun_utils.format_args(parsed_args.environment)
        opts['workdir'] = parsed_args.workdir
        opts['labels'] = zun_utils.format_args(parsed_args.label)
        opts['image_pull_policy'] = parsed_args.image_pull_policy
        opts['image_driver'] = parsed_args.image_driver
        opts['auto_remove'] = parsed_args.auto_remove
        if parsed_args.security_group:
            opts['security_groups'] = parsed_args.security_group
        if parsed_args.command:
            opts['command'] = zun_utils.parse_command(parsed_args.command)
        if parsed_args.restart:
            opts['restart_policy'] = \
                zun_utils.check_restart_policy(parsed_args.restart)
        if parsed_args.interactive:
            opts['interactive'] = True
        opts['hints'] = zun_utils.format_args(parsed_args.hint)
        opts['nets'] = zun_utils.parse_nets(parsed_args.net)

        opts = zun_utils.remove_null_parms(**opts)
        container = client.containers.run(**opts)
        columns = _container_columns(container)
        container_uuid = getattr(container, 'uuid', None)
        if parsed_args.interactive:
            ready_for_attach = False
            while True:
                container = client.containers.get(container_uuid)
                if zun_utils.check_container_status(container, 'Running'):
                    ready_for_attach = True
                    break
                if zun_utils.check_container_status(container, 'Error'):
                    break
                print("Waiting for container start")
                time.sleep(1)
            if ready_for_attach is True:
                response = client.containers.attach(container_uuid)
                websocketclient.do_attach(client, response, container_uuid,
                                          "~", 0.5)
            else:
                raise exceptions.InvalidWebSocketLink(container_uuid)

        return columns, utils.get_item_properties(container, columns)


class RenameContainer(command.Command):
    """Rename specified container"""
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
    """Display the running processes inside the container"""
    log = logging.getLogger(__name__ + ".TopContainer")

    def get_parser(self, prog_name):
        parser = super(TopContainer, self).get_parser(prog_name)
        parser.add_argument(
            'container',
            metavar='<container>',
            help='ID or name of the container to display processes.')
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


class UpdateContainer(command.ShowOne):
    """Update one or more attributes of the container"""
    log = logging.getLogger(__name__ + ".UpdateContainer")

    def get_parser(self, prog_name):
        parser = super(UpdateContainer, self).get_parser(prog_name)
        parser.add_argument(
            'container',
            metavar='<container>',
            help="ID or name of the container to update.")
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
        opts = zun_utils.remove_null_parms(**opts)
        if not opts:
            raise exc.CommandError("You must update at least one property")
        container = client.containers.update(container, **opts)
        columns = _container_columns(container)
        return columns, utils.get_item_properties(container, columns)


class AttachContainer(command.Command):
    """Attach to a running container"""

    log = logging.getLogger(__name__ + ".AttachContainer")

    def get_parser(self, prog_name):
        parser = super(AttachContainer, self).get_parser(prog_name)
        parser.add_argument(
            'container',
            metavar='<container>',
            help='ID or name of the container to be attached to.')
        return parser

    def take_action(self, parsed_args):
        client = _get_client(self, parsed_args)
        response = client.containers.attach(parsed_args.container)
        websocketclient.do_attach(client, response, parsed_args.container,
                                  "~", 0.5)


class CopyContainer(command.Command):
    """Copy files/tars between a container and the local filesystem."""
    log = logging.getLogger(__name__ + ".CopyContainer")

    def get_parser(self, prog_name):
        parser = super(CopyContainer, self).get_parser(prog_name)
        parser.add_argument(
            'source',
            metavar='<source>',
            help='The source should be copied to the container or localhost. '
                 'The format of this parameter is [container:]src_path.')
        parser.add_argument(
            'destination',
            metavar='<destination>',
            help='The directory destination where save the source. '
                 'The format of this parameter is [container:]dest_path.')
        return parser

    def take_action(self, parsed_args):
        client = _get_client(self, parsed_args)
        if ':' in parsed_args.source:
            source_parts = parsed_args.source.split(':', 1)
            container_id = source_parts[0]
            container_path = source_parts[1]
            opts = {}
            opts['id'] = container_id
            opts['path'] = container_path

            res = client.containers.get_archive(**opts)
            dest_path = parsed_args.destination
            tardata = io.BytesIO(res['data'].encode())
            with closing(tarfile.open(fileobj=tardata)) as tar:
                tar.extractall(dest_path)

        elif ':' in parsed_args.destination:
            dest_parts = parsed_args.destination.split(':', 1)
            container_id = dest_parts[0]
            container_path = dest_parts[1]
            filename = os.path.split(parsed_args.source)[1]
            opts = {}
            opts['id'] = container_id
            opts['path'] = container_path
            tardata = io.BytesIO()
            with closing(tarfile.open(fileobj=tardata, mode='w')) as tar:
                tar.add(parsed_args.source, arcname=filename)
            opts['data'] = tardata.getvalue()
            client.containers.put_archive(**opts)
        else:
            print("Please check the parameters for zun copy!")
            print("Usage:")
            print("openstack appcontainer cp container:src_path dest_path|-")
            print("openstack appcontainer cp src_path|- container:dest_path")


class StatsContainer(command.ShowOne):
    """Display stats of the container."""
    log = logging.getLogger(__name__ + ".StatsContainer")

    def get_parser(self, prog_name):
        parser = super(StatsContainer, self).get_parser(prog_name)
        parser.add_argument(
            'container',
            metavar='<container>',
            help='ID or name of the (container)s to  display stats.')
        return parser

    def take_action(self, parsed_args):
        client = _get_client(self, parsed_args)
        container = parsed_args.container
        stats_info = client.containers.stats(container)
        return stats_info.keys(), stats_info.values()


class CommitContainer(command.Command):
    """Create a new image from a container's changes"""
    log = logging.getLogger(__name__ + ".CommitContainer")

    def get_parser(self, prog_name):
        parser = super(CommitContainer, self).get_parser(prog_name)
        parser.add_argument(
            'container',
            metavar='<container>',
            help='ID or name of the (container)s to commit.')
        parser.add_argument(
            '--repository',
            required=True,
            metavar='<repository>',
            help='Repository of the new image.')
        parser.add_argument(
            '--tag',
            metavar='<tag>',
            help='Tag of the new iamge')
        return parser

    def take_action(self, parsed_args):
        client = _get_client(self, parsed_args)
        container = parsed_args.container
        opts = {}
        opts['repository'] = parsed_args.repository
        opts['tag'] = parsed_args.tag
        opts = zun_utils.remove_null_parms(**opts)
        try:
            image = client.containers.commit(container, **opts)
            print("Request to commit container %s has been accepted. "
                  "The image is %s." % (container, image))
        except Exception as e:
            print("commit container %(container)s failed: %(e)s" %
                  {'container': container, 'e': e})
