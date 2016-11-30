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

import json

from zunclient.common import cliutils as utils
from zunclient.common import utils as zun_utils


def _show_container(container):
    utils.print_dict(container._info)


@utils.arg('-n', '--name',
           metavar='<name>',
           help='name of the container')
@utils.arg('-i', '--image',
           required=True,
           metavar='<image>',
           help='name or ID of the image')
@utils.arg('-c', '--command',
           metavar='<command>',
           help='Send command to the container')
@utils.arg('--cpu',
           metavar='<cpu>',
           help='The number of virtual cpus.')
@utils.arg('-m', '--memory',
           metavar='<memory>',
           help='The container memory size (format: <number><optional unit>, '
                'where unit = b, k, m or g)')
@utils.arg('-e', '--environment',
           metavar='<KEY=VALUE>',
           action='append', default=[],
           help='The environment variabled')
@utils.arg('--workdir',
           metavar='<workdir>',
           help='The working directory for commands to run in')
@utils.arg('--expose',
           metavar='<port>',
           action='append', default=[],
           help='A port or a list of ports to expose. '
                'May be used multiple times.')
@utils.arg('--hostname',
           metavar='<hostname>',
           help='The hostname to use for the container')
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
                '"always": Always pull the image from repositery.'
                '"never": never pull the image')
def do_create(cs, args):
    """Create a container."""
    opts = {}
    opts['name'] = args.name
    opts['image'] = args.image
    opts['command'] = args.command
    opts['memory'] = args.memory
    opts['cpu'] = args.cpu
    opts['environment'] = zun_utils.format_labels(args.environment)
    opts['workdir'] = args.workdir
    opts['ports'] = args.expose
    opts['hostname'] = args.hostname
    opts['labels'] = zun_utils.format_labels(args.label)
    opts['image_pull_policy'] = args.image_pull_policy
    _show_container(cs.containers.create(**opts))


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
def do_list(cs, args):
    """Print a list of available containers."""
    opts = {}
    opts['marker'] = args.marker
    opts['limit'] = args.limit
    opts['sort_key'] = args.sort_key
    opts['sort_dir'] = args.sort_dir
    containers = cs.containers.list(**opts)
    columns = ('uuid', 'name', 'status', 'task_state', 'image', 'command',
               'ports')
    utils.print_list(containers, columns,
                     {'versions': zun_utils.print_list_field('versions')},
                     sortby_index=None)


@utils.arg('containers',
           metavar='<container>',
           nargs='+',
           help='ID or name of the (container)s to delete.')
@utils.arg('-f', '--force',
           action='store_true',
           help='Force delete the container.')
def do_delete(cs, args):
    """Delete specified containers."""
    for container in args.containers:
        try:
            cs.containers.delete(container, args.force)
            print("Request to delete container %s has been accepted." %
                  container)
        except Exception as e:
            print("Delete for container %(container)s failed: %(e)s" %
                  {'container': container, 'e': e})


@utils.arg('container',
           metavar='<container>',
           help='ID or name of the container to show.')
@utils.arg('--json',
           action='store_true',
           default=False,
           help='Print JSON representation of the container.')
def do_show(cs, args):
    """Show details of a container."""
    container = cs.containers.get(args.container)
    if args.json:
        print(json.dumps(container._info))
    else:
        _show_container(container)


@utils.arg('containers',
           metavar='<container>',
           nargs='+',
           help='ID or name of the (container)s to reboot.')
def do_reboot(cs, args):
    """Reboot specified containers."""
    for container in args.containers:
        try:
            cs.containers.reboot(container)
            print("Request to reboot container %s has been accepted." %
                  container)
        except Exception as e:
            print("Reboot for container %(container)s failed: %(e)s" %
                  {'container': container, 'e': e})


@utils.arg('containers',
           metavar='<container>',
           nargs='+',
           help='ID or name of the (container)s to stop.')
def do_stop(cs, args):
    """Stop specified containers."""
    for container in args.containers:
        try:
            cs.containers.stop(container)
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
def do_logs(cs, args):
    """Get logs of a container."""
    logs = cs.containers.logs(args.container)
    print(logs)


@utils.arg('container',
           metavar='<container>',
           help='ID or name of the container to execute command in.')
@utils.arg('-c', '--command',
           required=True,
           metavar='<command>',
           help='The command to execute')
def do_exec(cs, args):
    """Execute command in a container."""
    output = cs.containers.execute(args.container, args.command)
    print(output)


@utils.arg('container',
           metavar='<container>',
           help='ID or name of the container to kill signal to.')
@utils.arg('-s', '--signal',
           metavar='<signal>',
           default=None,
           help='The signal to kill')
def do_kill(cs, args):
    """kill signal to a container."""
    opts = {}
    opts['id'] = args.container
    opts['signal'] = args.signal
    try:
        cs.containers.kill(**opts)
        print(
            "Request to kill signal to container %s has been accepted." %
            args.container)
    except Exception as e:
        print(
            "kill signal for container %(container)s failed: %(e)s" %
            {'container': args.container, 'e': e})


@utils.arg('-n', '--name',
           metavar='<name>',
           help='name of the container')
@utils.arg('-i', '--image',
           required=True,
           metavar='<image>',
           help='name or ID of the image')
@utils.arg('-c', '--command',
           metavar='<command>',
           help='Send command to the container')
@utils.arg('--cpu',
           metavar='<cpu>',
           help='The number of virtual cpus.')
@utils.arg('-m', '--memory',
           metavar='<memory>',
           help='The container memory size (format: <number><optional unit>, '
                'where unit = b, k, m or g)')
@utils.arg('-e', '--environment',
           metavar='<KEY=VALUE>',
           action='append', default=[],
           help='The environment variabled')
@utils.arg('--workdir',
           metavar='<workdir>',
           help='The working directory for commands to run in')
@utils.arg('--expose',
           metavar='<port>',
           action='append', default=[],
           help='A port or a list of ports to expose. '
                'May be used multiple times.')
@utils.arg('--hostname',
           metavar='<hostname>',
           help='The hostname to use for the container')
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
                '"always": Always pull the image from repositery.'
                '"never": never pull the image')
def do_run(cs, args):
    """Run a command in a new container"""
    opts = {}
    opts['name'] = args.name
    opts['image'] = args.image
    opts['command'] = args.command
    opts['memory'] = args.memory
    opts['cpu'] = args.cpu
    opts['environment'] = zun_utils.format_labels(args.environment)
    opts['workdir'] = args.workdir
    opts['ports'] = args.expose
    opts['hostname'] = args.hostname
    opts['labels'] = zun_utils.format_labels(args.label)
    opts['image_pull_policy'] = args.image_pull_policy
    _show_container(cs.containers.run(**opts))
