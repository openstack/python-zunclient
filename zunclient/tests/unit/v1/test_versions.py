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

import testtools
from testtools import matchers

from zunclient.tests.unit import utils
from zunclient.v1 import versions


VERSION1 = {'status': 'CURRENT',
            'min_version': '1.1',
            'max_version': '1.12',
            'id': 'v1',
            }

fake_responses = {
    '/':
    {
        'GET': (
            {},
            {'versions': [VERSION1]},
        ),
    },
}


class VersionManagerTest(testtools.TestCase):

    def setUp(self):
        super(VersionManagerTest, self).setUp()
        self.api = utils.FakeAPI(fake_responses)
        self.mgr = versions.VersionManager(self.api)

    def test_version_list(self):
        versions = self.mgr.list()
        expect = [
            ('GET', '/', {}, None),
        ]
        self.assertEqual(expect, self.api.calls)
        self.assertThat(versions, matchers.HasLength(1))
