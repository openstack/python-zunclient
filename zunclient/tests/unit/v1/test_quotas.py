#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain a
#    copy of the License at
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import testtools

from zunclient.tests.unit import utils
from zunclient.v1 import quotas


DEFAULT_QUOTAS = {
    'containers': '40',
    'memory': '51200',
    'cpu': '20',
    'disk': '100'
}

MODIFIED_QUOTAS = {
    'containers': '50',
    'memory': '51200',
    'cpu': '20',
    'disk': '100'
}

MODIFIED_USAGE_QUOTAS = {
    'containers': {
        'limit': '50',
        'in_use': '30'
    },
    'memory': {},
    'cpu': {},
    'disk': {}
}

fake_responses = {
    '/v1/quotas/test_project_id':
    {
        'GET': (
            {},
            MODIFIED_QUOTAS
        ),
        'PUT': (
            {},
            MODIFIED_QUOTAS
        ),
        'DELETE': (
            {},
            None
        )
    },
    '/v1/quotas/test_project_id/defaults':
    {
        'GET': (
            {},
            DEFAULT_QUOTAS
        )
    },
    '/v1/quotas/test_project_id?usages=True':
    {
        'GET': (
            {},
            MODIFIED_USAGE_QUOTAS
        )
    }
}


class QuotaManagerTest(testtools.TestCase):

    def setUp(self):
        super(QuotaManagerTest, self).setUp()
        self.api = utils.FakeAPI(fake_responses)
        self.mgr = quotas.QuotaManager(self.api)

    def test_quotas_get_defaults(self):
        quotas = self.mgr.defaults('test_project_id')
        expect = [
            ('GET', '/v1/quotas/test_project_id/defaults', {}, None)
        ]
        self.assertEqual(expect, self.api.calls)
        self.assertEqual(quotas.containers, DEFAULT_QUOTAS['containers'])
        self.assertEqual(quotas.memory, DEFAULT_QUOTAS['memory'])
        self.assertEqual(quotas.cpu, DEFAULT_QUOTAS['cpu'])
        self.assertEqual(quotas.disk, DEFAULT_QUOTAS['disk'])
