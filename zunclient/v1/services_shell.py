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


from zunclient.common import cliutils as utils
from zunclient.common import utils as zun_utils


def do_service_list(cs, args):
    """Print a list of zun services."""
    services = cs.services.list()
    columns = ('Id', 'Host', 'Binary', 'State', 'Disabled',
               'Disabled Reason', 'Updated At',
               'Availability Zone')
    utils.print_list(services, columns,
                     {'versions': zun_utils.print_list_field('versions')})


@utils.arg('host',
           metavar='<host>',
           help='Name of host.')
@utils.arg('binary',
           metavar='<binary>',
           help='Name of the binary to delete.')
def do_service_delete(cs, args):
    """Delete the Zun binaries/services."""
    try:
        cs.services.delete(args.host, args.binary)
        print("Request to delete binary %s on host %s has been accepted." %
              (args.binary, args.host))
    except Exception as e:
        print("Delete for binary %(binary)s on host %(host)s failed: %(e)s" %
              {'binary': args.binary, 'host': args.host, 'e': e})


@utils.arg('host', metavar='<host>', help='Name of host.')
@utils.arg('binary', metavar='<binary>', help='Service binary.')
def do_service_enable(cs, args):
    """Enable the Zun service."""
    res = cs.services.enable(args.host, args.binary)
    utils.print_dict(res[1]['service'])


@utils.arg('host', metavar='<host>', help='Name of host.')
@utils.arg('binary', metavar='<binary>', help='Service binary.')
@utils.arg(
    '--reason',
    metavar='<reason>',
    help='Reason for disabling service.')
def do_service_disable(cs, args):
    """Disable the Zun service."""
    res = cs.services.disable(args.host, args.binary, args.reason)
    utils.print_dict(res[1]['service'])


@utils.arg('host', metavar='<host>', help='Name of host.')
@utils.arg('binary', metavar='<binary>', help='Service binary.')
@utils.arg(
    '--unset',
    dest='force_down',
    help="Unset the force state down of service.",
    action='store_false',
    default=True)
def do_service_force_down(cs, args):
    """Force Zun service to down or unset the force state."""
    res = cs.services.force_down(args.host, args.binary, args.force_down)
    utils.print_dict(res[1]['service'])
