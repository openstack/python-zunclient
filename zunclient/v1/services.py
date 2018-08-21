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


class Service(base.Resource):
    def __repr__(self):
        return "<Service %s>" % self._info


class ServiceManager(base.Manager):
    resource_class = Service

    @staticmethod
    def _path(id=None):
        return '/v1/services/%s' % id if id else '/v1/services'

    def list(self, marker=None, limit=None, sort_key=None,
             sort_dir=None):
        """Retrieve list of zun services.

        :param marker: Optional, the ID of a zun service, eg the last
                       services from a previous result set. Return
                       the next result set.
        :param limit: The maximum number of results to return per
                      request, if:

            1) limit > 0, the maximum number of services to return.
            2) limit param is NOT specified (None), the number of items
               returned respect the maximum imposed by the Zun API
               (see Zun's api.max_limit option).

        :param sort_key: Optional, field used for sorting.

        :param sort_dir: Optional, direction of sorting, either 'asc' (the
                         default) or 'desc'.

        :returns: A list of services.
        """

        if limit is not None:
            limit = int(limit)

        filters = utils.common_filters(marker, limit, sort_key, sort_dir)

        path = ''
        if filters:
            path += '?' + '&'.join(filters)

        if limit is None:
            return self._list(self._path(path), "services")
        else:
            return self._list_pagination(self._path(path), "services",
                                         limit=limit)

    def delete(self, host, binary):
        """Delete a service."""
        return self._delete(self._path(),
                            qparams={'host': host,
                                     'binary': binary})

    def _action(self, action, method='PUT', qparams=None, **kwargs):
        if qparams:
            action = "%s?%s" % (action,
                                parse.urlencode(qparams))
        kwargs.setdefault('headers', {})
        kwargs['headers'].setdefault('Content-Length', '0')
        resp, body = self.api.json_request(method,
                                           self._path() + action,
                                           **kwargs)
        return resp, body

    def _update_body(self, host, binary, disabled_reason=None,
                     force_down=None):
        body = {"host": host,
                "binary": binary}
        if disabled_reason is not None:
            body["disabled_reason"] = disabled_reason
        if force_down is not None:
            body["forced_down"] = force_down
        return body

    def enable(self, host, binary):
        """Enable the service specified by hostname and binary."""
        body = self._update_body(host, binary)
        return self._action("/enable", qparams=body)

    def disable(self, host, binary, reason=None):
        """Disable the service specified by hostname and binary."""
        body = self._update_body(host, binary, reason)
        return self._action("/disable", qparams=body)

    def force_down(self, host, binary, force_down=None):
        """Force service state to down specified by hostname and binary."""
        body = self._update_body(host, binary, force_down=force_down)
        return self._action("/force_down", qparams=body)
