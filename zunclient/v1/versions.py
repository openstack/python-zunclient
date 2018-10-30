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

from six.moves import urllib

from zunclient.common import base


class Version(base.Resource):
    def __repr__(self):
        return "<Version>"


class VersionManager(base.Manager):
    resource_class = Version

    def list(self):
        endpoint = self.api.get_endpoint()
        url = urllib.parse.urlparse(endpoint)
        # NOTE(hongbin): endpoint URL has at least 2 formats:
        #   1. the classic (legacy) endpoint:
        #       http://{host}:{optional_port}/v1/
        #   2. under wsgi:
        #       http://{host}:{optional_port}/container/v1
        if url.path.endswith("v1") or "/v1/" in url.path:
            # this way should handle all 2 possible formats
            path = url.path[:url.path.rfind("/v1")]
            version_url = '%s://%s%s' % (url.scheme, url.netloc, path)
        else:
            # NOTE(hongbin): probably, it is one of the next cases:
            #  * https://container.example.com/
            #  * https://example.com/container
            # leave as is without cropping.
            version_url = endpoint

        return self._list(version_url, "versions")

    def get_current(self):
        for version in self.list():
            if version.status == "CURRENT":
                return version
        return None
