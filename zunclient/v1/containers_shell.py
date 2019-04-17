# Copyright 2015 NEC Corporation.  All rights reserved.
#
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

import argparse
from contextlib import closing
import io
import os
import tarfile
import time
import yaml

from oslo_serialization import jsonutils

from zunclient.common import cliutils as utils
from zunclient.common import utils as zun_utils
from zunclient.common.websocketclient import exceptions
from zunclient.common.websocketclient import websocketclient
from zunclient import exceptions as exc


RENAME_DEPRECATION_MESSAGE = (
    'WARNING: Rename container command deprecated and will be removed '
    'in a future release.\nUse Update container command to avoid '
    'seeing this message.')


SG_DEPRECATION_MESSAGE = (
    'WARNING: Security group related commands deprecated and will be removed '
    'in a future release.\nUse Neutron commands to manage security groups '
    'instead.')


def _show_container(container):
    zun_utils.format_container_addresses(container)
    utils.print_dict(container._info)


@utils.exclusive_arg(
    'restart_auto_remove',
    '--auto-remove',
    required=False, action='store_true',
    help='Automatically remove the container when it exits')
@utils.exclusive_arg(
    'restart_auto_remove',
    '--restart',
    required=False, metavar='<restart>',
    help='Restart policy to apply when a container exits'
         '(no, on-failure[:max-retry], always, unless-stopped)')
@utils.exclusive_arg(
    'secgroup_expose_port',
    '--security-group',
    metavar='<security-group>',
    action='append', default=[],
    help='The name of security group for the container. '
         'May be used multiple times.')
@utils.exclusive_arg(
    'secgroup_expose_port',
    '-p', '--expose-port',
    action='append',
    default=[],
    metavar='<port>',
    help='Expose container port(s) to outside (format: <port>[/<protocol>])')
@utils.arg('-n', '--name',
           metavar='<name>',
           help='name of the container')
@utils.arg('--cpu',
           metavar='<cpu>',
           help='The number of virtual cpus.')
@utils.arg('-m', '--memory',
           metavar='<memory>',
           help='The container memory size in MiB')
@utils.arg('-e', '--environment',
           metavar='<KEY=VALUE>',
           action='append', default=[],
           help='The environment variables')
@utils.arg('--workdir',
           metavar='<workdir>',
           help='The working directory for commands to run in')
@utils.arg('--label',
           metavar='<KEY=VALUE>',
           action='append', default=[],
           help='Adds a map of labels to a container. '
                'May be used multiple times.')
@utils.arg('--image-pull-policy',
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
@utils.arg('image', metavar='<image>', help='name or ID or repo of the image '
           '(e.g. cirros:latest)')
@utils.arg('-i', '--interactive',
           dest='interactive',
           action='store_true',
           default=False,
           help='Keep STDIN open even if not attached, allocate a pseudo-TTY')
@utils.arg('--image-driver',
           metavar='<image_driver>',
           help='The image driver to use to pull container image. '
                'It can have following values: '
                '"docker": pull the image from Docker Hub. '
                '"glance": pull the image from Glance. ')
@utils.arg('command',
           metavar='<command>',
           nargs=argparse.REMAINDER,
           help='Send command to the container')
@utils.arg('--hint',
           action='append',
           default=[],
           metavar='<key=value>',
           help='The key-value pair(s) for scheduler to select host. '
                'The format of this parameter is "key=value[,key=value]". '
                'May be used multiple times.')
@utils.arg('--net',
           action='append',
           default=[],
           metavar='<network=network, port=port-uuid,'
                   'v4-fixed-ip=ip-addr,v6-fixed-ip=ip-addr>',
           help='Create network enpoints for the container. '
                'network: attach container to the specified neturon networks. '
                'port: attach container to the neutron port with this UUID. '
                'v4-fixed-ip: IPv4 fixed address for container. '
                'v6-fixed-ip: IPv6 fixed address for container.')
@utils.arg('--mount',
           action='append',
           default=[],
           metavar='<mount>',
           help='A dictionary to configure volumes mounted inside the '
                'container.')
@utils.arg('--runtime',
           metavar='<runtime>',
           help='The runtime to use for this container. '
                'It can have value "runc" or any other custom runtime.')
@utils.arg('--hostname',
           metavar='<hostname>',
           default=None,
           help='Container host name')
@utils.arg('--disk',
           metavar='<disk>',
           type=int,
           default=None,
           help='The disk size in GiB for per container.')
@utils.arg('--availability-zone',
           metavar='<availability_zone>',
           default=None,
           help='The availability zone of the container.')
@utils.arg('--auto-heal',
           action='store_true',
           default=False,
           help='The flag of healing non-existent container in docker.')
@utils.arg('--privileged',
           dest='privileged',
           action='store_true',
           default=False,
           help='Give extended privileges to this container')
@utils.arg('--healthcheck',
           action='append',
           default=[],
           metavar='<cmd=command,interval=time,retries=integer,timeout=time>',
           help='Specify a test cmd to perform to check that the container'
                'is healthy. '
                'cmd: Command to run to check health. '
                'interval: Time between running the check (s|m|h)'
                '          (default 0s). '
                'retries: Consecutive failures needed to report unhealthy. '
                'timeout: Maximum time to allow one check to run (s|m|h)'
                '         (default 0s).')
@utils.arg('--registry',
           metavar='<registry>',
           help='The container image registry ID or name')
def do_create(cs, args):
    """Create a container."""
    opts = {}
    opts['name'] = args.name
    opts['image'] = args.image
    opts['memory'] = args.memory
    opts['cpu'] = args.cpu
    opts['environment'] = zun_utils.format_args(args.environment)
    opts['auto_remove'] = args.auto_remove
    opts['workdir'] = args.workdir
    opts['labels'] = zun_utils.format_args(args.label)
    opts['image_pull_policy'] = args.image_pull_policy
    opts['image_driver'] = args.image_driver
    opts['hints'] = zun_utils.format_args(args.hint)
    opts['nets'] = zun_utils.parse_nets(args.net)
    opts['mounts'] = zun_utils.parse_mounts(args.mount)
    opts['runtime'] = args.runtime
    opts['hostname'] = args.hostname
    opts['disk'] = args.disk
    opts['availability_zone'] = args.availability_zone
    opts['command'] = args.command
    opts['registry'] = args.registry
    if args.healthcheck:
        opts['healthcheck'] = zun_utils.parse_health(args.healthcheck)

    if args.auto_heal:
        opts['auto_heal'] = args.auto_heal
    if args.security_group:
        opts['security_groups'] = args.security_group
    if args.expose_port:
        opts['exposed_ports'] = zun_utils.parse_exposed_ports(args.expose_port)
    if args.restart:
        opts['restart_policy'] = zun_utils.check_restart_policy(args.restart)
    if args.interactive:
        opts['interactive'] = True
    if args.privileged:
        opts['privileged'] = True
    opts = zun_utils.remove_null_parms(**opts)
    _show_container(cs.containers.create(**opts))


@utils.arg('--all-projects',
           action="store_true",
           default=False,
           help='List containers in all projects')
@utils.arg('--marker',
           metavar='<marker>',
           default=None,
           help='The last container UUID of the previous page; '
                'displays list of containers after "marker".')
@utils.arg('--limit',
           metavar='<limit>',
           type=int,
           help='Maximum number of containers to return')
@utils.arg('--sort-key',
           metavar='<sort-key>',
           help='Column to sort results by')
@utils.arg('--sort-dir',
           metavar='<sort-dir>',
           choices=['desc', 'asc'],
           help='Direction to sort. "asc" or "desc".')
@utils.arg('--name',
           metavar='<name>',
           help='List containers according to their name.')
@utils.arg('--image',
           metavar='<image>',
           help='List containers according to their image.')
@utils.arg('--project-id',
           metavar='<project-id>',
           help='List containers according to their Project_id')
@utils.arg('--user-id',
           metavar='<user-id>',
           help='List containers according to their user_id')
@utils.arg('--task-state',
           metavar='<task-state>',
           help='List containers according to their task-state')
@utils.arg('--status',
           metavar='<status>',
           help='List containers according to their status')
@utils.arg('--memory',
           metavar='<memory>',
           help='List containers according to their memory size in MiB')
@utils.arg('--host',
           metavar='<host>',
           help='List containers according to their hostname')
@utils.arg('--auto-remove',
           metavar='<auto-remove>',
           help='List containers according to whether they are '
                'auto-removed on exiting')
def do_list(cs, args):
    """Print a list of available containers."""
    opts = {}
    opts['all_projects'] = args.all_projects
    opts['marker'] = args.marker
    opts['limit'] = args.limit
    opts['sort_key'] = args.sort_key
    opts['sort_dir'] = args.sort_dir
    opts['image'] = args.image
    opts['name'] = args.name
    opts['project_id'] = args.project_id
    opts['user_id'] = args.user_id
    opts['host'] = args.host
    opts['task_state'] = args.task_state
    opts['memory'] = args.memory
    opts['auto_remove'] = args.auto_remove
    opts['status'] = args.status
    opts = zun_utils.remove_null_parms(**opts)
    containers = cs.containers.list(**opts)
    zun_utils.list_containers(containers)


@utils.arg('containers',
           metavar='<container>',
           nargs='+',
           help='ID or name of the (container)s to delete.')
@utils.arg('-f', '--force',
           action='store_true',
           help='Force delete the container.')
@utils.arg('-s', '--stop',
           action='store_true',
           help='Stop the running container first before delete.')
@utils.arg('--all-projects',
           action="store_true",
           default=False,
           help='Delete container(s) in all projects by name.')
def do_delete(cs, args):
    """Delete specified containers."""
    for container in args.containers:
        opts = {}
        opts['id'] = container
        opts['force'] = args.force
        opts['stop'] = args.stop
        opts['all_projects'] = args.all_projects
        opts = zun_utils.remove_null_parms(**opts)
        try:
            cs.containers.delete(**opts)
            print("Request to delete container %s has been accepted." %
                  container)
        except Exception as e:
            print("Delete for container %(container)s failed: %(e)s" %
                  {'container': container, 'e': e})


@utils.arg('container',
           metavar='<container>',
           help='ID or name of the container to show.')
@utils.arg('-f', '--format',
           metavar='<format>',
           action='store',
           choices=['json', 'yaml', 'table'],
           default='table',
           help='Print representation of the container.'
                'The choices of the output format is json,table,yaml.'
                'Defaults to table.')
@utils.arg('--all-projects',
           action="store_true",
           default=False,
           help='Show container(s) in all projects by name.')
def do_show(cs, args):
    """Show details of a container."""
    opts = {}
    opts['id'] = args.container
    opts['all_projects'] = args.all_projects
    opts = zun_utils.remove_null_parms(**opts)
    container = cs.containers.get(**opts)
    if args.format == 'json':
        print(jsonutils.dumps(container._info, indent=4, sort_keys=True))
    elif args.format == 'yaml':
        print(yaml.safe_dump(container._info, default_flow_style=False))
    elif args.format == 'table':
        _show_container(container)


@utils.arg('containers',
           metavar='<container>',
           nargs='+',
           help='ID of the (container)s to rebuild.')
@utils.arg('--image',
           metavar='<image>',
           help='The image for specified container to update.')
@utils.arg('--image-driver',
           metavar='<image_driver>',
           help='The image driver to use to pull container image. '
                'It can have following values: '
                '"docker": pull the image from Docker Hub. '
                '"glance": pull the image from Glance. '
                'The default value is source container\'s image driver ')
def do_rebuild(cs, args):
    """Rebuild specified containers."""
    for container in args.containers:
        opts = {}
        opts['id'] = container
        if args.image:
            opts['image'] = args.image
        if args.image_driver:
            opts['image_driver'] = args.image_driver
        try:
            cs.containers.rebuild(**opts)
            print("Request to rebuild container %s has been accepted." %
                  container)
        except Exception as e:
            print("Rebuild for container %(container)s failed: %(e)s" %
                  {'container': container, 'e': e})


@utils.arg('containers',
           metavar='<container>',
           nargs='+',
           help='ID or name of the (container)s to restart.')
@utils.arg('-t', '--timeout',
           metavar='<timeout>',
           default=10,
           help='Seconds to wait for stop before restarting (container)s')
def do_restart(cs, args):
    """Restart specified containers."""
    for container in args.containers:
        try:
            cs.containers.restart(container, args.timeout)
            print("Request to restart container %s has been accepted." %
                  container)
        except Exception as e:
            print("Restart for container %(container)s failed: %(e)s" %
                  {'container': container, 'e': e})


@utils.arg('containers',
           metavar='<container>',
           nargs='+',
           help='ID or name of the (container)s to stop.')
@utils.arg('-t', '--timeout',
           metavar='<timeout>',
           default=10,
           help='Seconds to wait for stop before killing (container)s')
def do_stop(cs, args):
    """Stop specified containers."""
    for container in args.containers:
        try:
            cs.containers.stop(container, args.timeout)
            print("Request to stop container %s has been accepted." %
                  container)
        except Exception as e:
            print("Stop for container %(container)s failed: %(e)s" %
                  {'container': container, 'e': e})


@utils.arg('containers',
           metavar='<container>',
           nargs='+',
           help='ID of the (container)s to start.')
def do_start(cs, args):
    """Start specified containers."""
    for container in args.containers:
        try:
            cs.containers.start(container)
            print("Request to start container %s has been accepted." %
                  container)
        except Exception as e:
            print("Start for container %(container)s failed: %(e)s" %
                  {'container': container, 'e': e})


@utils.arg('containers',
           metavar='<container>',
           nargs='+',
           help='ID or name of the (container)s to pause.')
def do_pause(cs, args):
    """Pause specified containers."""
    for container in args.containers:
        try:
            cs.containers.pause(container)
            print("Request to pause container %s has been accepted." %
                  container)
        except Exception as e:
            print("Pause for container %(container)s failed: %(e)s" %
                  {'container': container, 'e': e})


@utils.arg('containers',
           metavar='<container>',
           nargs='+',
           help='ID or name of the (container)s to unpause.')
def do_unpause(cs, args):
    """Unpause specified containers."""
    for container in args.containers:
        try:
            cs.containers.unpause(container)
            print("Request to unpause container %s has been accepted." %
                  container)
        except Exception as e:
            print("Unpause for container %(container)s failed: %(e)s" %
                  {'container': container, 'e': e})


@utils.arg('container',
           metavar='<container>',
           help='ID or name of the container to get logs for.')
@utils.arg('--stdout',
           action='store_true',
           help='Only stdout logs of container.')
@utils.arg('--stderr',
           action='store_true',
           help='Only stderr logs of container.')
@utils.arg('--since',
           metavar='<since>',
           default=None,
           help='Show logs since a given datetime or integer '
                'epoch (in seconds).')
@utils.arg('-t', '--timestamps',
           dest='timestamps',
           action='store_true',
           default=False,
           help='Show timestamps.')
@utils.arg('--tail',
           metavar='<tail>',
           default='all',
           help='Number of lines to show from the end of the logs.')
def do_logs(cs, args):
    """Get logs of a container."""
    opts = {}
    opts['id'] = args.container
    opts['stdout'] = args.stdout
    opts['stderr'] = args.stderr
    opts['since'] = args.since
    opts['timestamps'] = args.timestamps
    opts['tail'] = args.tail
    opts = zun_utils.remove_null_parms(**opts)
    logs = cs.containers.logs(**opts)
    print(logs)


@utils.arg('container',
           metavar='<container>',
           help='ID or name of the container to execute command in.')
@utils.arg('command',
           metavar='<command>',
           nargs=argparse.REMAINDER,
           help='The command to execute in a container')
@utils.arg('-i', '--interactive',
           dest='interactive',
           action='store_true',
           default=False,
           help='Keep STDIN open and allocate a pseudo-TTY for interactive')
def do_exec(cs, args):
    """Execute command in a running container."""
    opts = {}
    opts['command'] = zun_utils.parse_command(args.command)
    if args.interactive:
        opts['interactive'] = True
        opts['run'] = False
    response = cs.containers.execute(args.container, **opts)
    if args.interactive:
        exec_id = response['exec_id']
        url = response['proxy_url']
        websocketclient.do_exec(cs, url, args.container, exec_id, "~", 0.5)
    else:
        output = response['output']
        exit_code = response['exit_code']
        print(output)
        return exit_code


@utils.arg('containers',
           metavar='<container>',
           nargs='+',
           help='ID or name of the (container)s to kill signal to.')
@utils.arg('-s', '--signal',
           metavar='<signal>',
           default=None,
           help='The signal to kill')
def do_kill(cs, args):
    """Kill one or more running container(s)."""
    for container in args.containers:
        opts = {}
        opts['id'] = container
        opts['signal'] = args.signal
        opts = zun_utils.remove_null_parms(**opts)
        try:
            cs.containers.kill(**opts)
            print(
                "Request to kill signal to container %s has been accepted." %
                container)
        except Exception as e:
            print(
                "kill signal for container %(container)s failed: %(e)s" %
                {'container': container, 'e': e})


@utils.exclusive_arg(
    'restart_auto_remove',
    '--auto-remove',
    required=False, action='store_true',
    help='Automatically remove the container when it exits')
@utils.exclusive_arg(
    'restart_auto_remove',
    '--restart',
    required=False, metavar='<restart>',
    help='Restart policy to apply when a container exits'
         '(no, on-failure[:max-retry], always, unless-stopped)')
@utils.exclusive_arg(
    'secgroup_expose_port',
    '--security-group',
    metavar='<security-group>',
    action='append', default=[],
    help='The name of security group for the container. '
         'May be used multiple times.')
@utils.exclusive_arg(
    'secgroup_expose_port',
    '-p', '--expose-port',
    action='append',
    default=[],
    metavar='<port>',
    help='Expose container port(s) to outside (format: <port>[/<protocol>])')
@utils.arg('-n', '--name',
           metavar='<name>',
           help='name of the container')
@utils.arg('--cpu',
           metavar='<cpu>',
           help='The number of virtual cpus.')
@utils.arg('-m', '--memory',
           metavar='<memory>',
           help='The container memory size in MiB')
@utils.arg('-e', '--environment',
           metavar='<KEY=VALUE>',
           action='append', default=[],
           help='The environment variables')
@utils.arg('--workdir',
           metavar='<workdir>',
           help='The working directory for commands to run in')
@utils.arg('--label',
           metavar='<KEY=VALUE>',
           action='append', default=[],
           help='Adds a map of labels to a container. '
                'May be used multiple times.')
@utils.arg('--image-pull-policy',
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
@utils.arg('image', metavar='<image>', help='name or ID of the image')
@utils.arg('-i', '--interactive',
           dest='interactive',
           action='store_true',
           default=False,
           help='Keep STDIN open even if not attached, allocate a pseudo-TTY')
@utils.arg('--image-driver',
           metavar='<image_driver>',
           help='The image driver to use to pull container image. '
                'It can have following values: '
                '"docker": pull the image from Docker Hub. '
                '"glance": pull the image from Glance. ')
@utils.arg('command',
           metavar='<command>',
           nargs=argparse.REMAINDER,
           help='Send command to the container')
@utils.arg('--hint',
           action='append',
           default=[],
           metavar='<key=value>',
           help='The key-value pair(s) for scheduler to select host. '
                'The format of this parameter is "key=value[,key=value]". '
                'May be used multiple times.')
@utils.arg('--net',
           action='append',
           default=[],
           metavar='<network=network, port=port-uuid,'
                   'v4-fixed-ip=ip-addr,v6-fixed-ip=ip-addr>',
           help='Create network enpoints for the container. '
                'network: attach container to the specified neutron networks. '
                'port: attach container to the neutron port with this UUID. '
                'v4-fixed-ip: IPv4 fixed address for container. '
                'v6-fixed-ip: IPv6 fixed address for container.')
@utils.arg('--mount',
           action='append',
           default=[],
           metavar='<mount>',
           help='A dictionary to configure volumes mounted inside the '
                'container.')
@utils.arg('--runtime',
           metavar='<runtime>',
           help='The runtime to use for this container. '
                'It can have value "runc" or any other custom runtime.')
@utils.arg('--hostname',
           metavar='<hostname>',
           default=None,
           help='Container hostname')
@utils.arg('--disk',
           metavar='<disk>',
           type=int,
           default=None,
           help='The disk size in GiB for per container.')
@utils.arg('--availability-zone',
           metavar='<availability_zone>',
           default=None,
           help='The availability zone of the container.')
@utils.arg('--auto-heal',
           action='store_true',
           default=False,
           help='The flag of healing non-existent container in docker.')
@utils.arg('--privileged',
           dest='privileged',
           action='store_true',
           default=False,
           help='Give extended privileges to this container')
@utils.arg('--healthcheck',
           action='append',
           default=[],
           metavar='<cmd=command,interval=time,retries=integer,timeout=time>',
           help='Specify a test cmd to perform to check that the container'
                'is healthy. '
                'cmd: Command to run to check health. '
                'interval: Time between running the check (s|m|h)'
                '          (default 0s). '
                'retries: Consecutive failures needed to report unhealthy. '
                'timeout: Maximum time to allow one check to run (s|m|h)'
                '         (default 0s).')
@utils.arg('--registry',
           metavar='<registry>',
           help='The container image registry ID or name')
def do_run(cs, args):
    """Run a command in a new container."""
    opts = {}
    opts['name'] = args.name
    opts['image'] = args.image
    opts['memory'] = args.memory
    opts['cpu'] = args.cpu
    opts['environment'] = zun_utils.format_args(args.environment)
    opts['workdir'] = args.workdir
    opts['auto_remove'] = args.auto_remove
    opts['labels'] = zun_utils.format_args(args.label)
    opts['image_pull_policy'] = args.image_pull_policy
    opts['image_driver'] = args.image_driver
    opts['hints'] = zun_utils.format_args(args.hint)
    opts['nets'] = zun_utils.parse_nets(args.net)
    opts['mounts'] = zun_utils.parse_mounts(args.mount)
    opts['runtime'] = args.runtime
    opts['hostname'] = args.hostname
    opts['disk'] = args.disk
    opts['availability_zone'] = args.availability_zone
    opts['command'] = args.command
    opts['registry'] = args.registry
    if args.healthcheck:
        opts['healthcheck'] = zun_utils.parse_health(args.healthcheck)

    if args.auto_heal:
        opts['auto_heal'] = args.auto_heal
    if args.security_group:
        opts['security_groups'] = args.security_group
    if args.expose_port:
        opts['exposed_ports'] = zun_utils.parse_exposed_ports(args.expose_port)
    if args.restart:
        opts['restart_policy'] = zun_utils.check_restart_policy(args.restart)
    if args.interactive:
        opts['interactive'] = True
    if args.privileged:
        opts['privileged'] = True
    opts = zun_utils.remove_null_parms(**opts)
    container = cs.containers.run(**opts)
    _show_container(container)
    container_uuid = getattr(container, 'uuid', None)
    if args.interactive:
        ready_for_attach = False
        while True:
            container = cs.containers.get(container_uuid)
            if zun_utils.check_container_status(container, 'Running'):
                ready_for_attach = True
                break
            if zun_utils.check_container_status(container, 'Error'):
                raise exceptions.ContainerStateError(container_uuid)
            print("Waiting for container start")
            time.sleep(1)
        if ready_for_attach is True:
            response = cs.containers.attach(container_uuid)
            websocketclient.do_attach(cs, response, container_uuid, "~", 0.5)
        else:
            raise exceptions.InvalidWebSocketLink(container_uuid)


@utils.arg('container',
           metavar='<container>',
           help="ID or name of the container to update.")
@utils.arg('--cpu',
           metavar='<cpu>',
           help='The number of virtual cpus.')
@utils.arg('-m', '--memory',
           metavar='<memory>',
           help='The container memory size in MiB')
@utils.arg('--name',
           metavar='<name>',
           help='The new name for the container')
@utils.exclusive_arg(
    'auto_heal_value',
    '--auto-heal',
    required=False, action='store_true',
    help='Automatic recovery the status of contaier')
@utils.exclusive_arg(
    'auto_heal_value',
    '--no-auto-heal',
    required=False, action='store_true',
    help='Needless recovery the status of contaier')
def do_update(cs, args):
    """Update one or more attributes of the container."""
    opts = {}
    opts['memory'] = args.memory
    opts['cpu'] = args.cpu
    opts['name'] = args.name
    if 'auto_heal' in args and args.auto_heal:
        opts['auto_heal'] = True
    if 'no_auto_heal' in args and args.no_auto_heal:
        opts['auto_heal'] = False
    opts = zun_utils.remove_null_parms(**opts)
    if not opts:
        raise exc.CommandError("You must update at least one property")
    container = cs.containers.update(args.container, **opts)
    _show_container(container)


@utils.deprecated(RENAME_DEPRECATION_MESSAGE)
@utils.arg('container',
           metavar='<container>',
           help='ID or name of the container to rename.')
@utils.arg('name',
           metavar='<name>',
           help='The new name for the container')
def do_rename(cs, args):
    """Rename a container."""
    cs.containers.rename(args.container, args.name)


@utils.arg('container',
           metavar='<container>',
           help='ID or name of the container to be attached to.')
def do_attach(cs, args):
    """Attach to a running container."""
    response = cs.containers.attach(args.container)
    websocketclient.do_attach(cs, response, args.container, "~", 0.5)


@utils.arg('container',
           metavar='<container>',
           help='ID or name of the container to display processes.')
@utils.arg('--pid',
           metavar='<pid>',
           action='append', default=[],
           help='The args of the ps id.')
def do_top(cs, args):
    """Display the running processes inside the container."""

    if args.pid:
        # List container single ps id top result
        output = cs.containers.top(args.container, ' '.join(args.pid))
    else:
        # List container all processes top result
        output = cs.containers.top(args.container)
    for titles in output['Titles']:
        print("%-20s") % titles,
    if output['Processes']:
        for process in output['Processes']:
            print("")
            for info in process:
                print("%-20s") % info,
    else:
        print("")


@utils.arg('source',
           metavar='<source>',
           help='The source should be copied to the container or localhost. '
                'The format of this parameter is [container:]src_path.')
@utils.arg('destination',
           metavar='<destination>',
           help='The directory destination where save the source. '
                'The format of this parameter is [container:]dest_path.')
def do_cp(cs, args):
    """Copy files/tars between a container and the local filesystem."""
    if ':' in args.source:
        source_parts = args.source.split(':', 1)
        container_id = source_parts[0]
        container_path = source_parts[1]
        opts = {}
        opts['id'] = container_id
        opts['path'] = container_path

        res = cs.containers.get_archive(**opts)
        dest_path = args.destination
        tardata = io.BytesIO(res['data'])
        with closing(tarfile.open(fileobj=tardata)) as tar:
            tar.extractall(dest_path)

    elif ':' in args.destination:
        dest_parts = args.destination.split(':', 1)
        container_id = dest_parts[0]
        container_path = dest_parts[1]
        filename = os.path.split(args.source)[1]
        opts = {}
        opts['id'] = container_id
        opts['path'] = container_path
        tardata = io.BytesIO()
        with closing(tarfile.open(fileobj=tardata, mode='w')) as tar:
            tar.add(args.source, arcname=filename)
        opts['data'] = tardata.getvalue()
        cs.containers.put_archive(**opts)

    else:
        print("Please check the parameters for zun copy!")
        print("Usage:")
        print("zun cp container:src_path dest_path|-")
        print("zun cp src_path|- container:dest_path")


@utils.arg('container',
           metavar='<container>',
           help='ID or name of the container to display stats.')
def do_stats(cs, args):
    """Display stats of the container."""
    stats_info = cs.containers.stats(args.container)
    utils.print_dict(stats_info)


@utils.arg('container',
           metavar='<container>',
           help='ID or name of the container to commit.')
@utils.arg('repository',
           metavar='<repository>[:<tag>]',
           help='The repository and tag of the image.')
def do_commit(cs, args):
    """Create a new image from a container's changes."""
    opts = zun_utils.check_commit_container_args(args)
    opts = zun_utils.remove_null_parms(**opts)
    try:
        image = cs.containers.commit(args.container, **opts)
        print("Request to commit container %s has been accepted. "
              "The image is %s." % (args.container, image['uuid']))
    except Exception as e:
        print("Commit for container %(container)s failed: %(e)s" %
              {'container': args.container, 'e': e})


@utils.deprecated(SG_DEPRECATION_MESSAGE)
@utils.arg('container',
           metavar='<container>',
           help='ID or name of the container to add security group.')
@utils.arg('security_group',
           metavar='<security_group>',
           help='Security group ID or name for specified container.')
def do_add_security_group(cs, args):
    """Add security group for specified container."""
    opts = {}
    opts['id'] = args.container
    opts['security_group'] = args.security_group
    opts = zun_utils.remove_null_parms(**opts)
    try:
        cs.containers.add_security_group(**opts)
        print("Request to add security group for container %s "
              "has been accepted." % args.container)
    except Exception as e:
        print("Add security group for container %(container)s "
              "failed: %(e)s" % {'container': args.container, 'e': e})


@utils.exclusive_arg(
    'detach_network_port',
    '--network',
    metavar='<network>',
    help='The neutron network that container will detach from.')
@utils.exclusive_arg(
    'detach_network_port',
    '--port',
    metavar='<port>',
    help='The neutron port that container will detach from.')
@utils.arg('container',
           metavar='<container>',
           help='ID or name of the container to detach the network.')
def do_network_detach(cs, args):
    """Detach a network from the container."""
    opts = {}
    opts['container'] = args.container
    opts['network'] = args.network
    opts['port'] = args.port
    opts = zun_utils.remove_null_parms(**opts)
    try:
        cs.containers.network_detach(**opts)
        print("Request to detach network from container %s "
              "has been accepted." % args.container)
    except Exception as e:
        print("Detach network from container %(container)s "
              "failed: %(e)s" % {'container': args.container, 'e': e})


@utils.arg('container',
           metavar='<container>',
           help='ID or name of the container to attach network.')
@utils.arg('--network',
           metavar='<network>',
           help='The neutron network that container will attach to.')
@utils.arg('--port',
           metavar='<port>',
           help='The neutron port that container will attach to.')
@utils.arg('--fixed-ip',
           metavar='<fixed_ip>',
           help='The fixed-ip that container will attach to.')
def do_network_attach(cs, args):
    """Attach a network to the container."""
    opts = {}
    opts['container'] = args.container
    opts['network'] = args.network
    opts['port'] = args.port
    opts['fixed_ip'] = args.fixed_ip
    opts = zun_utils.remove_null_parms(**opts)
    try:
        cs.containers.network_attach(**opts)
        print("Request to attach network to container %s "
              "has been accepted." % args.container)
    except Exception as e:
        print("Attach network to container %(container)s "
              "failed: %(e)s" % {'container': args.container, 'e': e})


@utils.arg('container',
           metavar='<container>',
           help='ID or name of the container to display network info.')
def do_network_list(cs, args):
    """List networks on a container"""
    opts = {}
    opts['container'] = args.container
    opts = zun_utils.remove_null_parms(**opts)
    networks = cs.containers.network_list(**opts)
    zun_utils.list_container_networks(networks)


@utils.deprecated(SG_DEPRECATION_MESSAGE)
@utils.arg('container',
           metavar='<container>',
           help='ID or name of the container to remove security group.')
@utils.arg('security_group',
           metavar='<security_group>',
           help='The security group to remove from specified container.')
def do_remove_security_group(cs, args):
    """Remove security group for specified container."""
    opts = {}
    opts['id'] = args.container
    opts['security_group'] = args.security_group
    opts = zun_utils.remove_null_parms(**opts)
    try:
        cs.containers.remove_security_group(**opts)
        print("Request to remove security group for container %s "
              "has been accepted." % args.container)
    except Exception as e:
        print("Remove security group for container %(container)s "
              "failed: %(e)s" % {'container': args.container, 'e': e})
