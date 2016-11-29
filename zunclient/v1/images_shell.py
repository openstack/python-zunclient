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


def _show_image(image):
    utils.print_dict(image._info)


@utils.arg('-r', '--repo',
           required=True,
           metavar='<repo>',
           help='image repo')
def do_pull(cs, args):
    """Pull an image."""
    opts = {}
    opts['repo'] = args.repo
    _show_image(cs.images.create(**opts))


@utils.arg('--marker',
           metavar='<marker>',
           default=None,
           help='The last image UUID of the previous page; '
                'displays list of images after "marker".')
@utils.arg('--limit',
           metavar='<limit>',
           type=int,
           help='Maximum number of images to return')
@utils.arg('--sort-key',
           metavar='<sort-key>',
           help='Column to sort results by')
@utils.arg('--sort-dir',
           metavar='<sort-dir>',
           choices=['desc', 'asc'],
           help='Direction to sort. "asc" or "desc".')
def do_image_list(cs, args):
    """Print a list of available images."""
    opts = {}
    opts['marker'] = args.marker
    opts['limit'] = args.limit
    opts['sort_key'] = args.sort_key
    opts['sort_dir'] = args.sort_dir
    images = cs.images.list(**opts)
    columns = ('uuid', 'image_id', 'repo', 'tag', 'size')
    utils.print_list(images, columns,
                     {'versions': zun_utils.print_list_field('versions')},
                     sortby_index=None)
