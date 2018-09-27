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


class QuotaClass(base.Resource):
    def __repr__(self):
        return "<QuotaClass %s>" % self._info


class QuotaClassManager(base.Manager):
    resource_class = QuotaClass

    @staticmethod
    def _path(quota_class_name):
        return '/v1/quota_classes/{}' . format(quota_class_name)

    def get(self, quota_class_name):
        return self._list(self._path(quota_class_name))[0]

    def update(self, quota_class_name, containers=None,
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
        return self._update(self._path(quota_class_name),
                            resources, method='PUT')
