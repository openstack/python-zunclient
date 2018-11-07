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


def _show_action(action):
    utils.print_dict(action._info)


@utils.arg('container',
           metavar='<container>',
           help='ID or name of a container.')
def do_action_list(cs, args):
    """Print a list of actions done on a container."""
    container = args.container
    actions = cs.actions.list(container)
    columns = ('user_id', 'container_uuid', 'request_id', 'action',
               'message', 'start_time')
    utils.print_list(actions, columns,
                     {'versions': zun_utils.print_list_field('versions')},
                     sortby_index=None)


@utils.arg('container',
           metavar='<container>',
           help='ID or name of the container whose actions are showed.')
@utils.arg('request_id',
           metavar='<request_id>',
           help='request ID of action to describe.')
def do_action_show(cs, args):
    """Describe a specific action."""
    action = cs.actions.get(args.container, args.request_id)
    _show_action(action)
