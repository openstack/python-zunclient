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

from zunclient.common import base
from zunclient.common import utils
from zunclient import exceptions


CREATION_ATTRIBUTES = ['template']


class Capsule(base.Resource):
    def __repr__(self):
        return "<Capsule %s>" % self._info


class CapsuleManager(base.Manager):
    resource_class = Capsule

    @staticmethod
    def _path(id=None):

        if id:
            return '/capsules/%s' % id
        else:
            return '/capsules/'

    def get(self, id):
        try:
            return self._list(self._path(id))[0]
        except IndexError:
            return None

    def create(self, **kwargs):
        new = {}
        for (key, value) in kwargs.items():
            if key in CREATION_ATTRIBUTES:
                new[key] = value
            else:
                raise exceptions.InvalidAttribute(
                    "Key must be in %s" % ','.join(CREATION_ATTRIBUTES))
        return self._create(self._path(), new)

    def list(self, marker=None, limit=None, sort_key=None,
             sort_dir=None, all_projects=False):
        """Retrieve a list of capsules.

        :param all_projects: Optional, list containers in all projects

        :param marker: Optional, the UUID of a containers, eg the last
                       containers from a previous result set. Return
                       the next result set.
        :param limit: The maximum number of results to return per
                      request, if:

            1) limit > 0, the maximum number of containers to return.
            2) limit param is NOT specified (None), the number of items
               returned respect the maximum imposed by the ZUN API
               (see Zun's api.max_limit option).

        :param sort_key: Optional, field used for sorting.

        :param sort_dir: Optional, direction of sorting, either 'asc' (the
                         default) or 'desc'.

        :returns: A list of containers.

        """
        if limit is not None:
            limit = int(limit)

        filters = utils.common_filters(marker, limit, sort_key,
                                       sort_dir, all_projects)

        path = ''
        if filters:
            path += '?' + '&'.join(filters)

        if limit is None:
            return self._list(self._path(path),
                              "capsules")
        else:
            return self._list_pagination(self._path(path),
                                         "capsules",
                                         limit=limit)

    def delete(self, id):
        return self._delete(self._path(id))

    def describe(self, id):
        try:
            return self._list(self._path(id))[0]
        except IndexError:
            return None
