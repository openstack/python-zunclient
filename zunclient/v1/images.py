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

from zunclient.common import base
from zunclient.common import utils
from zunclient import exceptions


PULL_ATTRIBUTES = ['repo']


class Image(base.Resource):
    def __repr__(self):
        return "<Image %s>" % self._info


class ImageManager(base.Manager):
    resource_class = Image

    @staticmethod
    def _path(id=None):

        if id:
            return '/v1/images/%s' % id
        else:
            return '/v1/images/'

    def list(self, marker=None, limit=None, sort_key=None,
             sort_dir=None, detail=False):
        """Retrieve a list of images.

        :param marker: Optional, the UUID of an image, eg the last
                       image from a previous result set. Return
                       the next result set.
        :param limit: The maximum number of results to return per
                      request, if:

            1) limit > 0, the maximum number of images to return.
            2) limit == 0, return the entire list of images.
            3) limit param is NOT specified (None), the number of items
               returned respect the maximum imposed by the Zun api

        :param sort_key: Optional, field used for sorting.

        :param sort_dir: Optional, direction of sorting, either 'asc' (the
                         default) or 'desc'.

        :param detail: Optional, boolean whether to return detailed information
                       about images.

        :returns: A list of images.

        """
        if limit is not None:
            limit = int(limit)

        filters = utils.common_filters(marker, limit, sort_key, sort_dir)

        path = ''
        if detail:
            path += 'detail'
        if filters:
            path += '?' + '&'.join(filters)

        if limit is None:
            return self._list(self._path(path),
                              "images")
        else:
            return self._list_pagination(self._path(path),
                                         "images",
                                         limit=limit)

    def get(self, id):
        try:
            return self._list(self._path(id))[0]
        except IndexError:
            return None

    def create(self, **kwargs):
        new = {}
        for (key, value) in kwargs.items():
            if key in PULL_ATTRIBUTES:
                new[key] = value
            else:
                raise exceptions.InvalidAttribute(
                    "Key must be in %s" % ','.join(PULL_ATTRIBUTES))
        return self._create(self._path(), new)
