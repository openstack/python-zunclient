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

import copy

import testtools
from testtools import matchers
from zunclient import exceptions
from zunclient.tests.unit import utils
from zunclient.v1 import registries

REGISTRY1 = {'uuid': 'cb9d9848-6c12-411b-a915-6eadc7bd2871',
             'name': 'test1',
             'domain': 'testdomain.io',
             'username': 'testuser1',
             'password': 'testpassword1',
             }

REGISTRY2 = {'uuid': 'c2d923ef-e9b5-4e6b-a8aa-7c54a715b370',
             'name': 'test2',
             'domain': 'otherdomain.io',
             'username': 'testuser2',
             'password': 'testpassword2',
             }


CREATE_REGISTRY1 = copy.deepcopy(REGISTRY1)
del CREATE_REGISTRY1['uuid']

UPDATE_REGISTRY1 = copy.deepcopy(REGISTRY1)
del UPDATE_REGISTRY1['uuid']
UPDATE_REGISTRY1['name'] = 'newname'

fake_responses = {
    '/v1/registries':
    {
        'GET': (
            {},
            {'registries': [REGISTRY1, REGISTRY2]},
        ),
        'POST': (
            {},
            {'registry': CREATE_REGISTRY1},
        ),
    },
    '/v1/registries/?limit=2':
    {
        'GET': (
            {},
            {'registries': [REGISTRY1, REGISTRY2]},
        ),
    },
    '/v1/registries/?marker=%s' % REGISTRY2['uuid']:
    {
        'GET': (
            {},
            {'registries': [REGISTRY1, REGISTRY2]},
        ),
    },
    '/v1/registries/?limit=2&marker=%s' % REGISTRY2['uuid']:
    {
        'GET': (
            {},
            {'registries': [REGISTRY1, REGISTRY2]},
        ),
    },
    '/v1/registries/?sort_dir=asc':
    {
        'GET': (
            {},
            {'registries': [REGISTRY1, REGISTRY2]},
        ),
    },
    '/v1/registries/?sort_key=uuid':
    {
        'GET': (
            {},
            {'registries': [REGISTRY1, REGISTRY2]},
        ),
    },
    '/v1/registries/?sort_key=uuid&sort_dir=desc':
    {
        'GET': (
            {},
            {'registries': [REGISTRY1, REGISTRY2]},
        ),
    },
    '/v1/registries/%s' % REGISTRY1['uuid']:
    {
        'GET': (
            {},
            {'registry': REGISTRY1}
        ),
        'DELETE': (
            {},
            None,
        ),
        'PATCH': (
            {},
            {'registry': UPDATE_REGISTRY1},
        ),
    },
}


class RegistryManagerTest(testtools.TestCase):

    def setUp(self):
        super(RegistryManagerTest, self).setUp()
        self.api = utils.FakeAPI(fake_responses)
        self.mgr = registries.RegistryManager(self.api)

    def test_registry_create(self):
        registries = self.mgr.create(**CREATE_REGISTRY1)
        expect = [
            ('POST', '/v1/registries', {}, {'registry': CREATE_REGISTRY1})
        ]
        self.assertEqual(expect, self.api.calls)
        self.assertTrue(registries)

    def test_registry_create_fail(self):
        create_registry_fail = copy.deepcopy(CREATE_REGISTRY1)
        create_registry_fail["wrong_key"] = "wrong"
        self.assertRaisesRegex(exceptions.InvalidAttribute,
                               ("Key must be in %s" %
                                ','.join(registries.CREATION_ATTRIBUTES)),
                               self.mgr.create, **create_registry_fail)
        self.assertEqual([], self.api.calls)

    def test_registries_list(self):
        registries = self.mgr.list()
        expect = [
            ('GET', '/v1/registries', {}, None),
        ]
        self.assertEqual(expect, self.api.calls)
        self.assertThat(registries, matchers.HasLength(2))

    def _test_registries_list_with_filters(self, limit=None, marker=None,
                                           sort_key=None, sort_dir=None,
                                           expect=[]):
        registries_filter = self.mgr.list(limit=limit, marker=marker,
                                          sort_key=sort_key,
                                          sort_dir=sort_dir)
        self.assertEqual(expect, self.api.calls)
        self.assertThat(registries_filter, matchers.HasLength(2))

    def test_registries_list_with_limit(self):
        expect = [
            ('GET', '/v1/registries/?limit=2', {}, None),
        ]
        self._test_registries_list_with_filters(
            limit=2,
            expect=expect)

    def test_registries_list_with_marker(self):
        expect = [
            ('GET', '/v1/registries/?marker=%s' % REGISTRY2['uuid'],
             {}, None),
        ]
        self._test_registries_list_with_filters(
            marker=REGISTRY2['uuid'],
            expect=expect)

    def test_registries_list_with_marker_limit(self):
        expect = [
            ('GET', '/v1/registries/?limit=2&marker=%s' % REGISTRY2['uuid'],
             {}, None),
        ]
        self._test_registries_list_with_filters(
            limit=2, marker=REGISTRY2['uuid'],
            expect=expect)

    def test_coontainer_list_with_sort_dir(self):
        expect = [
            ('GET', '/v1/registries/?sort_dir=asc', {}, None),
        ]
        self._test_registries_list_with_filters(
            sort_dir='asc',
            expect=expect)

    def test_registry_list_with_sort_key(self):
        expect = [
            ('GET', '/v1/registries/?sort_key=uuid', {}, None),
        ]
        self._test_registries_list_with_filters(
            sort_key='uuid',
            expect=expect)

    def test_registry_list_with_sort_key_dir(self):
        expect = [
            ('GET', '/v1/registries/?sort_key=uuid&sort_dir=desc', {}, None),
        ]
        self._test_registries_list_with_filters(
            sort_key='uuid', sort_dir='desc',
            expect=expect)

    def test_registry_show(self):
        registry = self.mgr.get(REGISTRY1['uuid'])
        expect = [
            ('GET', '/v1/registries/%s' % REGISTRY1['uuid'], {}, None)
        ]
        self.assertEqual(expect, self.api.calls)
        self.assertEqual(REGISTRY1['name'], registry._info['registry']['name'])
        self.assertEqual(REGISTRY1['uuid'], registry._info['registry']['uuid'])

    def test_registry_update(self):
        registry = self.mgr.update(REGISTRY1['uuid'], **UPDATE_REGISTRY1)
        expect = [
            ('PATCH', '/v1/registries/%s' % REGISTRY1['uuid'],
             {},
             {'registry': UPDATE_REGISTRY1})
        ]
        self.assertEqual(expect, self.api.calls)
        self.assertEqual(UPDATE_REGISTRY1['name'],
                         registry._info['registry']['name'])

    def test_registries_delete(self):
        registries = self.mgr.delete(REGISTRY1['uuid'])
        expect = [
            ('DELETE', '/v1/registries/%s' % (REGISTRY1['uuid']),
             {}, None)
        ]
        self.assertEqual(expect, self.api.calls)
        self.assertIsNone(registries)
