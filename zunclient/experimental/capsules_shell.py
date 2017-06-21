#    Copyright 2017 Arm Limited.
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
from zunclient.common import template_utils
from zunclient.common import utils as zun_utils
from zunclient.i18n import _


def _show_capsule(capsule):
    utils.print_dict(capsule._info)


@utils.arg('-f', '--template-file', metavar='<file>',
           required=True, help=_('Path to the template.'))
def do_capsule_create(cs, args):
    """Create a capsule.

    Add '--experimental-api' due to capsule now is the experimental API
    """
    opts = {}
    if args.template_file:
        template = template_utils.get_template_contents(
            args.template_file)
        opts['spec'] = template
        cs.capsules.create(**opts)


@utils.arg('--all-tenants',
           action="store_true",
           default=False,
           help='List containers in all tenants')
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
def do_capsule_list(cs, args):
    """Print a list of available capsules.

    Add '--experimental-api' due to capsule now is the experimental API
    """
    opts = {}
    opts['all_tenants'] = args.all_tenants
    opts['marker'] = args.marker
    opts['limit'] = args.limit
    opts['sort_key'] = args.sort_key
    opts['sort_dir'] = args.sort_dir
    opts = zun_utils.remove_null_parms(**opts)
    capsules = cs.capsules.list(**opts)
    zun_utils.list_capsules(capsules)


@utils.arg('capsules',
           metavar='<capsule>',
           nargs='+',
           help='ID or name of the (capsule)s to delete.')
@utils.arg('-f', '--force',
           action='store_true',
           help='Force delete the capsule.')
def do_capsule_delete(cs, args):
    """Delete specified capsules.

    Add '--experimental-api' due to capsule now is the experimental API
    """
    for capsule in args.capsules:
        try:
            cs.capsules.delete(capsule, args.force)
            print("Request to delete capsule %s has been accepted." %
                  capsule)
        except Exception as e:
            print("Delete for capsule %(capsule)s failed: %(e)s" %
                  {'capsule': capsule, 'e': e})
