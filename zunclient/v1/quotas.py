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


class Quota(base.Resource):
    def __repr__(self):
        return "<Quota %s>" % self._info


class QuotaManager(base.Manager):
    resource_class = Quota

    @staticmethod
    def _path(project_id):
        if project_id is not None:
            return '/v1/quotas/{}'.format(project_id)
        return '/v1/quotas'

    def get(self, project_id, **kwargs):
        if not kwargs.get('usages'):
            kwargs = {}
        return self._list(self._path(project_id), qparams=kwargs)[0]

    def update(self, project_id, containers=None,
               memory=None, cpu=None, disk=None):
        resources = {}
        if cpu is not None:
            resources['cpu'] = cpu
        if memory is not None:
            resources['memory'] = memory
        if containers is not None:
            resources['containers'] = containers
        if disk is not None:
            resources['disk'] = disk
        return self._update(self._path(project_id), resources, method='PUT')

    def defaults(self, project_id):
        return self._list(self._path(project_id) + '/defaults')[0]

    def delete(self, project_id):
        return self._delete(self._path(project_id))
