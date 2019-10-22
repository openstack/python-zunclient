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
import os
from oslo_log import log as logging
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
    return container._info.keys()


def _get_client(obj, parsed_args):
    obj.log.debug("take_action(%s)" % parsed_args)
    return obj.app.client_manager.container


def _action_columns(action):
    return action._info.keys()


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
            help='name or ID or repo of the image (e.g. cirros:latest)')
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
        restart_auto_remove_args = parser.add_mutually_exclusive_group()
        restart_auto_remove_args.add_argument(
            '--restart',
            metavar='<restart>',
            help='Restart policy to apply when a container exits'
                 '(no, on-failure[:max-retry], always, unless-stopped)')
        restart_auto_remove_args.add_argument(
            '--auto-remove',
            dest='auto_remove',
            action='store_true',
            default=False,
            help='Automatically remove the container when it exits')
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
        secgroup_expose_port_args = parser.add_mutually_exclusive_group()
        secgroup_expose_port_args.add_argument(
            '--security-group',
            metavar='<security_group>',
            action='append', default=[],
            help='The name of security group for the container. '
                 'May be used multiple times.')
        secgroup_expose_port_args.add_argument(
            '--expose-port',
            action='append',
            default=[],
            metavar='<port>',
            help='Expose container port(s) to outside (format: '
                 '<port>[/<protocol>]).')
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
            metavar='<network=network, port=port-uuid,'
                    'v4-fixed-ip=ip-addr,v6-fixed-ip=ip-addr>',
            action='append',
            default=[],
            help='Create network enpoints for the container. '
                 'network: attach container to the specified neutron networks.'
                 ' port: attach container to the neutron port with this UUID. '
                 'v4-fixed-ip: IPv4 fixed address for container. '
                 'v6-fixed-ip: IPv6 fixed address for container.')
        parser.add_argument(
            '--mount',
            action='append',
            default=[],
            metavar='<mount>',
            help='A dictionary to configure volumes mounted inside the '
                 'container.')
        parser.add_argument(
            '--runtime',
            metavar='<runtime>',
            help='The runtime to use for this container. '
                 'It can have value "runc" or any other custom runtime.')
        parser.add_argument(
            '--hostname',
            metavar='<hostname>',
            help='Container host name')
        parser.add_argument(
            '--disk',
            metavar='<disk>',
            type=int,
            default=None,
            help='The disk size in GiB for per container.')
        parser.add_argument(
            '--availability-zone',
            metavar='<availability_zone>',
            default=None,
            help='The availability zone of the container.')
        parser.add_argument(
            '--auto-heal',
            dest='auto_heal',
            action='store_true',
            default=False,
            help='The flag of healing non-existent container in docker')
        parser.add_argument(
            '--privileged',
            dest='privileged',
            action='store_true',
            default=False,
            help='Give extended privileges to this container')
        parser.add_argument(
            '--healthcheck',
            action='append',
            default=[],
            metavar='<cmd=test_cmd,interval=time,retries=n,timeout=time>',
            help='Specify a test cmd to perform to check that the container'
                 'is healthy. '
                 'cmd: Command to run to check health. '
                 'interval: Time between running the check (``s|m|h``)'
                 '          (default 0s). '
                 'retries: Consecutive failures needed to report unhealthy.'
                 'timeout: Maximum time to allow one check to run (``s|m|h``)'
                 '         (default 0s).')
        parser.add_argument(
            '--wait',
            action='store_true',
            help='Wait for create to complete')
        parser.add_argument(
            '--registry',
            metavar='<registry>',
            help='The container image registry ID or name.')
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
        opts['command'] = parsed_args.command
        opts['registry'] = parsed_args.registry
        if parsed_args.security_group:
            opts['security_groups'] = parsed_args.security_group
        if parsed_args.expose_port:
            opts['exposed_ports'] = zun_utils.parse_exposed_ports(
                parsed_args.expose_port)
        if parsed_args.restart:
            opts['restart_policy'] = \
                zun_utils.check_restart_policy(parsed_args.restart)
        if parsed_args.interactive:
            opts['interactive'] = True
        if parsed_args.privileged:
            opts['privileged'] = True
        opts['hints'] = zun_utils.format_args(parsed_args.hint)
        opts['nets'] = zun_utils.parse_nets(parsed_args.net)
        opts['mounts'] = zun_utils.parse_mounts(parsed_args.mount)
        opts['runtime'] = parsed_args.runtime
        opts['hostname'] = parsed_args.hostname
        opts['disk'] = parsed_args.disk
        opts['availability_zone'] = parsed_args.availability_zone
        if parsed_args.auto_heal:
            opts['auto_heal'] = parsed_args.auto_heal
        if parsed_args.healthcheck:
            opts['healthcheck'] = \
                zun_utils.parse_health(parsed_args.healthcheck)

        opts = zun_utils.remove_null_parms(**opts)
        container = client.containers.create(**opts)
        if parsed_args.wait:
            container_uuid = getattr(container, 'uuid', None)
            if utils.wait_for_status(
                client.containers.get,
                container_uuid,
                success_status=['created'],
            ):
                container = client.containers.get(container_uuid)
            else:
                print('Failed to create container.\n')
                raise SystemExit
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
            '--all-projects',
            action="store_true",
            default=False,
            help='Show container(s) in all projects by name.')
        return parser

    def take_action(self, parsed_args):
        client = _get_client(self, parsed_args)
        opts = {}
        opts['id'] = parsed_args.container
        opts['all_projects'] = parsed_args.all_projects
        opts = zun_utils.remove_null_parms(**opts)
        container = client.containers.get(**opts)
        zun_utils.format_container_addresses(container)
        columns = _container_columns(container)

        return columns, utils.get_item_properties(container, columns)


class ListContainer(command.Lister):
    """List available containers"""

    log = logging.getLogger(__name__ + ".ListContainers")

    def get_parser(self, prog_name):
        parser = super(ListContainer, self).get_parser(prog_name)
        parser.add_argument(
            '--all-projects',
            action="store_true",
            default=False,
            help='List containers in all projects')
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
        parser.add_argument(
            '--name',
            metavar='<name>',
            help='List containers according to their name.')
        parser.add_argument(
            '--image',
            metavar='<image>',
            help='List containers according to their image.')
        parser.add_argument(
            '--project-id',
            metavar='<project-id>',
            help='List containers according to their project_id')
        parser.add_argument(
            '--user-id',
            metavar='<user-id>',
            help='List containers according to their user_id')
        parser.add_argument(
            '--task-state',
            metavar='<task-state>',
            help='List containers according to their task-state')
        parser.add_argument(
            '--status',
            metavar='<status>',
            help='List containers according to their Status')
        parser.add_argument(
            '--memory',
            metavar='<memory>',
            help='List containers according to their memory size in MiB')
        parser.add_argument(
            '--host',
            metavar='<host>',
            help='List containers according to their hostname')
        parser.add_argument(
            '--auto-remove',
            metavar='<auto-remove>',
            help='List containers whether they are auto-removed on exiting')
        return parser

    def take_action(self, parsed_args):
        client = _get_client(self, parsed_args)
        opts = {}
        opts['all_projects'] = parsed_args.all_projects
        opts['marker'] = parsed_args.marker
        opts['limit'] = parsed_args.limit
        opts['sort_key'] = parsed_args.sort_key
        opts['sort_dir'] = parsed_args.sort_dir
        opts['image'] = parsed_args.image
        opts['name'] = parsed_args.name
        opts['project_id'] = parsed_args.project_id
        opts['user_id'] = parsed_args.user_id
        opts['host'] = parsed_args.host
        opts['task_state'] = parsed_args.task_state
        opts['memory'] = parsed_args.memory
        opts['auto_remove'] = parsed_args.auto_remove
        opts['status'] = parsed_args.status
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
            '--stop',
            action='store_true',
            help='Stop the running container first before delete.')
        parser.add_argument(
            '--all-projects',
            action="store_true",
            default=False,
            help='Delete container(s) in all projects by name.')
        parser.add_argument(
            '--wait',
            action='store_true',
            help='Wait for create to complete')
        return parser

    def take_action(self, parsed_args):
        client = _get_client(self, parsed_args)
        containers = parsed_args.container
        for container in containers:
            opts = {}
            opts['id'] = container
            opts['force'] = parsed_args.force
            opts['stop'] = parsed_args.stop
            opts['all_projects'] = parsed_args.all_projects
            opts = zun_utils.remove_null_parms(**opts)
            try:
                client.containers.delete(**opts)
                print(_('Request to delete container %s has been accepted.')
                      % container)
                if parsed_args.wait:
                    if utils.wait_for_delete(
                        client.containers,
                        container,
                        timeout=30
                    ):
                        print("Delete for container %(container)s success." %
                              {'container': container})
                    else:
                        print("Delete for container %(container)s failed." %
                              {'container': container})
                        raise SystemExit
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
            url = response['proxy_url']
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
        restart_auto_remove_args = parser.add_mutually_exclusive_group()
        restart_auto_remove_args.add_argument(
            '--restart',
            metavar='<restart>',
            help='Restart policy to apply when a container exits'
                 '(no, on-failure[:max-retry], always, unless-stopped)')
        restart_auto_remove_args.add_argument(
            '--auto-remove',
            dest='auto_remove',
            action='store_true',
            default=False,
            help='Automatically remove the container when it exits')
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
        secgroup_expose_port_args = parser.add_mutually_exclusive_group()
        secgroup_expose_port_args.add_argument(
            '--security-group',
            metavar='<security_group>',
            action='append', default=[],
            help='The name of security group for the container. '
                 'May be used multiple times.')
        secgroup_expose_port_args.add_argument(
            '--expose-port',
            action='append',
            default=[],
            metavar='<port>',
            help='Expose container port(s) to outside (format: '
                 '<port>[/<protocol>]).')
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
            metavar='<network=network, port=port-uuid,'
                    'v4-fixed-ip=ip-addr,v6-fixed-ip=ip-addr>',
            action='append',
            default=[],
            help='Create network enpoints for the container. '
                 'network: attach container to the specified neutron networks.'
                 ' port: attach container to the neutron port with this UUID. '
                 'v4-fixed-ip: IPv4 fixed address for container. '
                 'v6-fixed-ip: IPv6 fixed address for container.')
        parser.add_argument(
            '--mount',
            action='append',
            default=[],
            metavar='<mount>',
            help='A dictionary to configure volumes mounted inside the '
                 'container.')
        parser.add_argument(
            '--runtime',
            metavar='<runtime>',
            help='The runtime to use for this container. '
                 'It can have value "runc" or any other custom runtime.')
        parser.add_argument(
            '--hostname',
            metavar='<hostname>',
            help='Container host name')
        parser.add_argument(
            '--disk',
            metavar='<disk>',
            type=int,
            default=None,
            help='The disk size in GiB for per container.')
        parser.add_argument(
            '--availability-zone',
            metavar='<availability_zone>',
            default=None,
            help='The availability zone of the container.')
        parser.add_argument(
            '--auto-heal',
            dest='auto_heal',
            action='store_true',
            default=False,
            help='The flag of healing non-existent container in docker')
        parser.add_argument(
            '--privileged',
            dest='privileged',
            action='store_true',
            default=False,
            help='Give extended privileges to this container')
        parser.add_argument(
            '--healthcheck',
            action='append',
            default=[],
            metavar='<cmd=test_cmd,interval=time,retries=n,timeout=time>',
            help='Specify a test cmd to perform to check that the container'
                 'is healthy. '
                 'cmd: Command to run to check health. '
                 'interval: Time between running the check (``s|m|h``)'
                 '          (default 0s). '
                 'retries: Consecutive failures needed to report unhealthy.'
                 'timeout: Maximum time to allow one check to run (``s|m|h``)'
                 '         (default 0s).')
        parser.add_argument(
            '--wait',
            action='store_true',
            help='Wait for run to complete')
        parser.add_argument(
            '--registry',
            metavar='<registry>',
            help='The container image registry ID or name.')
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
        opts['command'] = parsed_args.command
        opts['registry'] = parsed_args.registry
        if parsed_args.security_group:
            opts['security_groups'] = parsed_args.security_group
        if parsed_args.expose_port:
            opts['exposed_ports'] = zun_utils.parse_exposed_ports(
                parsed_args.expose_port)
        if parsed_args.restart:
            opts['restart_policy'] = \
                zun_utils.check_restart_policy(parsed_args.restart)
        if parsed_args.interactive:
            opts['interactive'] = True
        if parsed_args.privileged:
            opts['privileged'] = True
        opts['hints'] = zun_utils.format_args(parsed_args.hint)
        opts['nets'] = zun_utils.parse_nets(parsed_args.net)
        opts['mounts'] = zun_utils.parse_mounts(parsed_args.mount)
        opts['runtime'] = parsed_args.runtime
        opts['hostname'] = parsed_args.hostname
        opts['disk'] = parsed_args.disk
        opts['availability_zone'] = parsed_args.availability_zone
        if parsed_args.auto_heal:
            opts['auto_heal'] = parsed_args.auto_heal
        if parsed_args.healthcheck:
            opts['healthcheck'] = \
                zun_utils.parse_health(parsed_args.healthcheck)

        opts = zun_utils.remove_null_parms(**opts)
        container = client.containers.run(**opts)
        columns = _container_columns(container)
        container_uuid = getattr(container, 'uuid', None)
        if parsed_args.wait:
            if utils.wait_for_status(
                client.containers.get,
                container_uuid,
                success_status=['running'],
            ):
                container = client.containers.get(container_uuid)
            else:
                print('Failed to run container.\n')
                raise SystemExit

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
            '--pid',
            metavar='<pid>',
            action='append', default=[],
            help='The args of the ps id.')
        return parser

    def take_action(self, parsed_args):
        client = _get_client(self, parsed_args)
        if parsed_args.pid:
            # List container single ps id top result
            output = client.containers.top(parsed_args.container,
                                           ' '.join(parsed_args.pid))
        else:
            # List container all processes top result
            output = client.containers.top(parsed_args.container)

        for titles in output['Titles']:
            print("%-20s") % titles,
        if output['Processes']:
            for process in output['Processes']:
                print("")
                for info in process:
                    print("%-20s") % info,
        else:
            print("")


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
        parser.add_argument(
            '--name',
            metavar='<name>',
            help='The new name of container to update')
        auto_heal_value = parser.add_mutually_exclusive_group()
        auto_heal_value.add_argument(
            '--auto-heal',
            required=False,
            action='store_true',
            help='Automatic recovery the status of contaier')
        auto_heal_value.add_argument(
            '--no-auto-heal',
            required=False,
            action='store_true',
            help='Needless recovery the status of contaier')
        return parser

    def take_action(self, parsed_args):
        client = _get_client(self, parsed_args)
        container = parsed_args.container
        opts = {}
        opts['memory'] = parsed_args.memory
        opts['cpu'] = parsed_args.cpu
        opts['name'] = parsed_args.name
        if 'auto_heal' in parsed_args and parsed_args.auto_heal:
            opts['auto_heal'] = True
        if 'no_auto_heal' in parsed_args and parsed_args.no_auto_heal:
            opts['auto_heal'] = False
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
            tardata = io.BytesIO(res['data'])
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
            'repository',
            metavar='<repository>[:<tag>]',
            help='Repository and tag of the new image.')
        return parser

    def take_action(self, parsed_args):
        client = _get_client(self, parsed_args)
        container = parsed_args.container
        opts = zun_utils.check_commit_container_args(parsed_args)
        opts = zun_utils.remove_null_parms(**opts)
        try:
            image = client.containers.commit(container, **opts)
            print("Request to commit container %s has been accepted. "
                  "The image is %s." % (container, image['uuid']))
        except Exception as e:
            print("commit container %(container)s failed: %(e)s" %
                  {'container': container, 'e': e})


class AddSecurityGroup(command.Command):
    """Add security group for specified container."""
    log = logging.getLogger(__name__ + ".AddSecurityGroup")

    def get_parser(self, prog_name):
        parser = super(AddSecurityGroup, self).get_parser(prog_name)
        parser.add_argument(
            'container',
            metavar='<container>',
            help='ID or name of the container to add security group.')
        parser.add_argument(
            'security_group',
            metavar='<security_group>',
            help='Security group ID or name for specified container. ')
        return parser

    def take_action(self, parsed_args):
        client = _get_client(self, parsed_args)
        opts = {}
        opts['id'] = parsed_args.container
        opts['security_group'] = parsed_args.security_group
        opts = zun_utils.remove_null_parms(**opts)
        try:
            # TODO(hongbin): add_security_group is removed starting from
            # API version 1.15. Use Neutron APIs to add security groups
            # to container's ports instead.
            client.containers.add_security_group(**opts)
            print("Request to add security group for container %s "
                  "has been accepted." % parsed_args.container)
        except Exception as e:
            print("Add security group for container %(container)s failed: "
                  "%(e)s" % {'container': parsed_args.container, 'e': e})


class RemoveSecurityGroup(command.Command):
    """Remove security group for specified container."""
    log = logging.getLogger(__name__ + ".RemoveSecurityGroup")

    def get_parser(self, prog_name):
        parser = super(RemoveSecurityGroup, self).get_parser(prog_name)
        parser.add_argument(
            'container',
            metavar='<container>',
            help='ID or name of the container to remove security group.')
        parser.add_argument(
            'security_group',
            metavar='<security_group>',
            help='The security group to remove from specified container. ')
        return parser

    def take_action(self, parsed_args):
        client = _get_client(self, parsed_args)
        opts = {}
        opts['id'] = parsed_args.container
        opts['security_group'] = parsed_args.security_group
        opts = zun_utils.remove_null_parms(**opts)
        try:
            # TODO(hongbin): remove_security_group is removed starting from
            # API version 1.15. Use Neutron APIs to remove security groups
            # from container's ports instead.
            client.containers.remove_security_group(**opts)
            print("Request to remove security group from container %s "
                  "has been accepted." % parsed_args.container)
        except Exception as e:
            print("Remove security group from container %(container)s failed: "
                  "%(e)s" % {'container': parsed_args.container, 'e': e})


class NetworkDetach(command.Command):
    """Detach neutron network from specified container."""
    log = logging.getLogger(__name__ + ".NetworkDetach")

    def get_parser(self, prog_name):
        parser = super(NetworkDetach, self).get_parser(prog_name)
        parser.add_argument(
            'container',
            metavar='<container>',
            help='ID or name of the container to detach network.')
        network_port_args = parser.add_mutually_exclusive_group()
        network_port_args.add_argument(
            '--network',
            metavar='<network>',
            help='The network for specified container to detach.')
        network_port_args.add_argument(
            '--port',
            metavar='<port>',
            help='The port for specified container to detach.')
        return parser

    def take_action(self, parsed_args):
        client = _get_client(self, parsed_args)
        opts = {}
        opts['container'] = parsed_args.container
        opts['network'] = parsed_args.network
        opts['port'] = parsed_args.port
        opts = zun_utils.remove_null_parms(**opts)
        try:
            client.containers.network_detach(**opts)
            print("Request to detach network for container %s "
                  "has been accepted." % parsed_args.container)
        except Exception as e:
            print("Detach network for container %(container)s failed: "
                  "%(e)s" % {'container': parsed_args.container, 'e': e})


class NetworkAttach(command.Command):
    """Attach neutron network to specified container."""
    log = logging.getLogger(__name__ + ".NetworkAttach")

    def get_parser(self, prog_name):
        parser = super(NetworkAttach, self).get_parser(prog_name)
        parser.add_argument(
            'container',
            metavar='<container>',
            help='ID or name of the container to attach network.')
        parser.add_argument(
            '--network',
            metavar='<network>',
            help='The network for specified container to attach.')
        parser.add_argument(
            '--port',
            metavar='<port>',
            help='The port for specified container to attach.')
        parser.add_argument(
            '--fixed-ip',
            metavar='<fixed_ip>',
            help='The fixed-ip that container will attach to.')
        return parser

    def take_action(self, parsed_args):
        client = _get_client(self, parsed_args)
        opts = {}
        opts['container'] = parsed_args.container
        opts['network'] = parsed_args.network
        opts['port'] = parsed_args.port
        opts['fixed_ip'] = parsed_args.fixed_ip
        opts = zun_utils.remove_null_parms(**opts)
        try:
            client.containers.network_attach(**opts)
            print("Request to attach network to container %s "
                  "has been accepted." % parsed_args.container)
        except Exception as e:
            print("Attach network to container %(container)s failed: "
                  "%(e)s" % {'container': parsed_args.container, 'e': e})


class RebuildContainer(command.Command):
    """Rebuild one or more running container(s)"""
    log = logging.getLogger(__name__ + ".RebuildContainer")

    def get_parser(self, prog_name):
        parser = super(RebuildContainer, self).get_parser(prog_name)
        parser.add_argument(
            'containers',
            metavar='<container>',
            nargs='+',
            help='ID or name of the (container)s to rebuild.')
        parser.add_argument(
            '--image',
            metavar='<image>',
            help='The image for specified container to update.')
        parser.add_argument(
            '--image-driver',
            metavar='<image_driver>',
            help='The image driver to use to update container image. '
                 'It can have following values: '
                 '"docker": update the image from Docker Hub. '
                 '"glance": update the image from Glance. '
                 'The default value is source container\'s image driver ')
        parser.add_argument(
            '--wait',
            action='store_true',
            help='Wait for rebuild to complete')
        return parser

    def take_action(self, parsed_args):
        client = _get_client(self, parsed_args)
        for container in parsed_args.containers:
            opts = {}
            opts['id'] = container
            if parsed_args.image:
                opts['image'] = parsed_args.image
            if parsed_args.image_driver:
                opts['image_driver'] = parsed_args.image_driver
            try:
                client.containers.rebuild(**opts)
                print(_('Request to rebuild container %s has '
                        'been accepted') % container)
                if parsed_args.wait:
                    if utils.wait_for_status(
                        client.containers.get,
                        container,
                        success_status=['created', 'running'],
                    ):
                        print("rebuild container %(container)s success." %
                              {'container': container})
                    else:
                        print("rebuild container %(container)s failed." %
                              {'container': container})
                        raise SystemExit
            except Exception as e:
                print("rebuild container %(container)s failed: %(e)s" %
                      {'container': container, 'e': e})


class NetworkList(command.Lister):
    """List networks on a container"""
    log = logging.getLogger(__name__ + ".ListNetworks")

    def get_parser(self, prog_name):
        parser = super(NetworkList, self).get_parser(prog_name)
        parser.add_argument(
            'container',
            metavar='<container>',
            help='ID or name of the container to list networks.'
        )
        return parser

    def take_action(self, parsed_args):
        client = _get_client(self, parsed_args)
        opts = {}
        opts['container'] = parsed_args.container
        opts = zun_utils.remove_null_parms(**opts)
        networks = client.containers.network_list(**opts)
        columns = ('net_id', 'port_id', 'fixed_ips')
        return (columns, (utils.get_item_properties(
            network, columns, formatters={
                'fixed_ips': zun_utils.format_fixed_ips})
            for network in networks))


class ActionList(command.Lister):
    """List actions on a container"""
    log = logging.getLogger(__name__ + ".ListActions")

    def get_parser(self, prog_name):
        parser = super(ActionList, self).get_parser(prog_name)
        parser.add_argument(
            'container',
            metavar='<container>',
            help='ID or name of the container to list actions.'
        )
        return parser

    def take_action(self, parsed_args):
        client = _get_client(self, parsed_args)
        container = parsed_args.container
        actions = client.actions.list(container)
        columns = ('user_id', 'container_uuid', 'request_id', 'action',
                   'message', 'start_time')
        return (columns, (utils.get_item_properties(action, columns)
                          for action in actions))


class ActionShow(command.ShowOne):
    """Show a action"""

    log = logging.getLogger(__name__ + ".ShowAction")

    def get_parser(self, prog_name):
        parser = super(ActionShow, self).get_parser(prog_name)
        parser.add_argument(
            'container',
            metavar='<container>',
            help='ID or name of the container to show.')
        parser.add_argument(
            'request_id',
            metavar='<request_id>',
            help='request ID of action to describe.')
        return parser

    def take_action(self, parsed_args):
        client = _get_client(self, parsed_args)
        container = parsed_args.container
        request_id = parsed_args.request_id
        action = client.actions.get(container, request_id)
        columns = _action_columns(action)
        return columns, utils.get_item_properties(action, columns)
