# Copyright 2014 NEC Corporation.  All rights reserved.
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

from six.moves.urllib import parse

from zunclient.common import base
from zunclient.common import utils
from zunclient import exceptions


CREATION_ATTRIBUTES = ['name', 'image', 'command', 'cpu', 'memory',
                       'environment', 'workdir', 'labels', 'image_pull_policy']


class Container(base.Resource):
    def __repr__(self):
        return "<Container %s>" % self._info


class ContainerManager(base.Manager):
    resource_class = Container

    @staticmethod
    def _path(id=None):

        if id:
            return '/v1/containers/%s' % id
        else:
            return '/v1/containers'

    def list(self, marker=None, limit=None, sort_key=None,
             sort_dir=None, detail=False):
        """Retrieve a list of containers.

        :param marker: Optional, the UUID of a containers, eg the last
                       containers from a previous result set. Return
                       the next result set.
        :param limit: The maximum number of results to return per
                      request, if:

            1) limit > 0, the maximum number of containers to return.
            2) limit == 0, return the entire list of containers.
            3) limit param is NOT specified (None), the number of items
               returned respect the maximum imposed by the ZUN API
               (see Zun's api.max_limit option).

        :param sort_key: Optional, field used for sorting.

        :param sort_dir: Optional, direction of sorting, either 'asc' (the
                         default) or 'desc'.

        :param detail: Optional, boolean whether to return detailed information
                       about containers.

        :returns: A list of containers.

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
                              "containers")
        else:
            return self._list_pagination(self._path(path),
                                         "containers",
                                         limit=limit)

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

    def delete(self, id, force):
        return self._delete(self._path(id),
                            qparams={'force': force})

    def _action(self, id, action, method='POST', qparams=None, **kwargs):
        if qparams:
            action = "%s?%s" % (action,
                                parse.urlencode(qparams))
        kwargs.setdefault('headers', {})
        kwargs['headers'].setdefault('Content-Length', '0')
        resp, body = self.api.json_request(method,
                                           self._path(id) + action,
                                           **kwargs)
        return resp, body

    def start(self, id):
        return self._action(id, '/start')

    def stop(self, id, timeout):
        return self._action(id, '/stop',
                            qparams={'timeout': timeout})

    def reboot(self, id, timeout):
        return self._action(id, '/reboot',
                            qparams={'timeout': timeout})

    def pause(self, id):
        return self._action(id, '/pause')

    def unpause(self, id):
        return self._action(id, '/unpause')

    def logs(self, id):
        return self._action(id, '/logs', method='GET')[1]

    def execute(self, id, command):
        return self._action(id, '/execute',
                            qparams={'command': command})[1]

    def kill(self, id, signal=None):
        return self._action(id, '/kill',
                            qparams={'signal': signal})[1]

    def run(self, **kwargs):
        if not set(kwargs).issubset(CREATION_ATTRIBUTES):
            raise exceptions.InvalidAttribute(
                "Key must be in %s" % ','.join(CREATION_ATTRIBUTES))
        else:
            return self._create(self._path() + '?run=true', kwargs)

    def rename(self, id, name):
        return self._action(id, '/rename',
                            qparams={'name': name})
