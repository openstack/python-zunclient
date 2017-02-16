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
from six.moves.urllib import parse
import testtools
from testtools import matchers
from zunclient import exceptions
from zunclient.tests.unit import utils
from zunclient.v1 import containers

CONTAINER1 = {'id': '1234',
              'uuid': '36e527e4-6d03-4eda-9443-904424043741',
              'name': 'test1',
              'image_pull_policy': 'never',
              'image': 'cirros',
              'command': 'sleep 100000000',
              'cpu': '1',
              'memory': '256',
              'environment': 'hostname=zunsystem',
              'workdir': '/',
              'labels': 'faketest',
              'restart_policy': 'no',
              }

CONTAINER2 = {'id': '1235',
              'uuid': 'c7f9da0f-581b-4586-8d0d-a6c894822165',
              'name': 'test2',
              'image_pull_policy': 'ifnotpresent',
              'image': 'cirros',
              'command': 'sleep 100000000',
              'cpu': '1',
              'memory': '256',
              'environment': 'hostname=zunsystem',
              'workdir': '/',
              'labels': 'faketest',
              'restart_policy': 'on-failure:5',
              }

CREATE_CONTAINER1 = copy.deepcopy(CONTAINER1)
del CREATE_CONTAINER1['id']
del CREATE_CONTAINER1['uuid']

force_delete1 = False
force_delete2 = True
signal = "SIGTERM"
name = "new-name"
timeout = 10
tty_height = "56"
tty_width = "121"

fake_responses = {
    '/v1/containers':
    {
        'GET': (
            {},
            {'containers': [CONTAINER1, CONTAINER2]},
        ),
        'POST': (
            {},
            CREATE_CONTAINER1,
        ),
    },
    '/v1/containers/?limit=2':
    {
        'GET': (
            {},
            {'containers': [CONTAINER1, CONTAINER2]},
        ),
    },
    '/v1/containers/?marker=%s' % CONTAINER2['uuid']:
    {
        'GET': (
            {},
            {'containers': [CONTAINER1, CONTAINER2]},
        ),
    },
    '/v1/containers/?limit=2&marker=%s' % CONTAINER2['uuid']:
    {
        'GET': (
            {},
            {'containers': [CONTAINER1, CONTAINER2]},
        ),
    },
    '/v1/containers/?sort_dir=asc':
    {
        'GET': (
            {},
            {'containers': [CONTAINER1, CONTAINER2]},
        ),
    },
    '/v1/containers/?sort_key=uuid':
    {
        'GET': (
            {},
            {'containers': [CONTAINER1, CONTAINER2]},
        ),
    },
    '/v1/containers/?sort_key=uuid&sort_dir=desc':
    {
        'GET': (
            {},
            {'containers': [CONTAINER1, CONTAINER2]},
        ),
    },
    '/v1/containers/%s' % CONTAINER1['id']:
    {
        'GET': (
            {},
            CONTAINER1
        ),
    },
    '/v1/containers/%s' % CONTAINER1['name']:
    {
        'GET': (
            {},
            CONTAINER1
        ),
    },
    '/v1/containers/%s/start' % CONTAINER1['id']:
    {
        'POST': (
            {},
            None,
        ),
    },
    '/v1/containers/%s?force=%s' % (CONTAINER1['id'], force_delete1):
    {
        'DELETE': (
            {},
            None,
        ),
    },
    '/v1/containers/%s?force=%s' % (CONTAINER1['id'], force_delete2):
    {
        'DELETE': (
            {},
            None,
        ),
    },
    '/v1/containers/%s/stop?timeout=10' % CONTAINER1['id']:
    {
        'POST': (
            {},
            None,
        ),
    },
    '/v1/containers/%s/reboot?timeout=10' % CONTAINER1['id']:
    {
        'POST': (
            {},
            None,
        ),
    },
    '/v1/containers/%s/pause' % CONTAINER1['id']:
    {
        'POST': (
            {},
            None,
        ),
    },
    '/v1/containers/%s/unpause' % CONTAINER1['id']:
    {
        'POST': (
            {},
            None,
        ),
    },
    '/v1/containers/%s/logs?%s'
    % (CONTAINER1['id'], parse.urlencode({'stdout': True, 'stderr': True})):
    {
        'GET': (
            {},
            None,
        ),
    },
    '/v1/containers/%s/execute?%s'
    % (CONTAINER1['id'], parse.urlencode({'command': CONTAINER1['command']})):
    {
        'POST': (
            {},
            None,
        ),
    },
    '/v1/containers/%s/kill?%s' % (CONTAINER1['id'],
                                   parse.urlencode({'signal': signal})):
    {
        'POST': (
            {},
            None,
        ),
    },
    '/v1/containers?run=true':
    {
        'POST': (
            {},
            CREATE_CONTAINER1,
        ),
    },
    '/v1/containers/%s/rename?%s' % (CONTAINER1['id'],
                                     parse.urlencode({'name': name})):
    {
        'POST': (
            {},
            None,
        ),
    },
    '/v1/containers/%s/attach' % CONTAINER1['id']:
    {
        'GET': (
            {},
            None,
        ),
    },
    '/v1/containers/%s/resize?w=%s&h=%s'
    % (CONTAINER1['id'], tty_width, tty_height):
    {
        'POST': (
            {},
            None,
        ),
    },
    '/v1/containers/%s/resize?h=%s&w=%s'
    % (CONTAINER1['id'], tty_height, tty_width):
    {
        'POST': (
            {},
            None,
        ),
    },
    '/v1/containers/%s/top?ps_args=None' % (CONTAINER1['id']):
    {
        'GET': (
            {},
            None,
        ),
    },
}


class ContainerManagerTest(testtools.TestCase):

    def setUp(self):
        super(ContainerManagerTest, self).setUp()
        self.api = utils.FakeAPI(fake_responses)
        self.mgr = containers.ContainerManager(self.api)

    def test_container_create(self):
        containers = self.mgr.create(**CREATE_CONTAINER1)
        expect = [
            ('POST', '/v1/containers', {}, CREATE_CONTAINER1)
        ]
        self.assertEqual(expect, self.api.calls)
        self.assertTrue(containers)

    def test_container_create_fail(self):
        create_container_fail = copy.deepcopy(CREATE_CONTAINER1)
        create_container_fail["wrong_key"] = "wrong"
        self.assertRaisesRegexp(exceptions.InvalidAttribute,
                                ("Key must be in %s" %
                                 ','.join(containers.CREATION_ATTRIBUTES)),
                                self.mgr.create, **create_container_fail)
        self.assertEqual([], self.api.calls)

    def test_containers_list(self):
        containers = self.mgr.list()
        expect = [
            ('GET', '/v1/containers', {}, None),
        ]
        self.assertEqual(expect, self.api.calls)
        self.assertThat(containers, matchers.HasLength(2))

    def _test_containers_list_with_filters(self, limit=None, marker=None,
                                           sort_key=None, sort_dir=None,
                                           detail=False, expect=[]):
        containers_filter = self.mgr.list(limit=limit, marker=marker,
                                          sort_key=sort_key,
                                          sort_dir=sort_dir,
                                          detail=detail)
        self.assertEqual(expect, self.api.calls)
        self.assertThat(containers_filter, matchers.HasLength(2))

    def test_containers_list_with_limit(self):
        expect = [
            ('GET', '/v1/containers/?limit=2', {}, None),
        ]
        self._test_containers_list_with_filters(
            limit=2,
            expect=expect)

    def test_containers_list_with_marker(self):
        expect = [
            ('GET', '/v1/containers/?marker=%s' % CONTAINER2['uuid'],
             {}, None),
        ]
        self._test_containers_list_with_filters(
            marker=CONTAINER2['uuid'],
            expect=expect)

    def test_containers_list_with_marker_limit(self):
        expect = [
            ('GET', '/v1/containers/?limit=2&marker=%s' % CONTAINER2['uuid'],
             {}, None),
        ]
        self._test_containers_list_with_filters(
            limit=2, marker=CONTAINER2['uuid'],
            expect=expect)

    def test_coontainer_list_with_sort_dir(self):
        expect = [
            ('GET', '/v1/containers/?sort_dir=asc', {}, None),
        ]
        self._test_containers_list_with_filters(
            sort_dir='asc',
            expect=expect)

    def test_container_list_with_sort_key(self):
        expect = [
            ('GET', '/v1/containers/?sort_key=uuid', {}, None),
        ]
        self._test_containers_list_with_filters(
            sort_key='uuid',
            expect=expect)

    def test_container_list_with_sort_key_dir(self):
        expect = [
            ('GET', '/v1/containers/?sort_key=uuid&sort_dir=desc', {}, None),
        ]
        self._test_containers_list_with_filters(
            sort_key='uuid', sort_dir='desc',
            expect=expect)

    def test_container_show_by_id(self):
        container = self.mgr.get(CONTAINER1['id'])
        expect = [
            ('GET', '/v1/containers/%s' % CONTAINER1['id'], {}, None)
        ]
        self.assertEqual(expect, self.api.calls)
        self.assertEqual(CONTAINER1['name'], container.name)
        self.assertEqual(CONTAINER1['uuid'], container.uuid)

    def test_container_show_by_name(self):
        container = self.mgr.get(CONTAINER1['name'])
        expect = [
            ('GET', '/v1/containers/%s' % CONTAINER1['name'], {}, None)
        ]
        self.assertEqual(expect, self.api.calls)
        self.assertEqual(CONTAINER1['name'], container.name)
        self.assertEqual(CONTAINER1['uuid'], container.uuid)

    def test_containers_start(self):
        containers = self.mgr.start(CONTAINER1['id'])
        expect = [
            ('POST', '/v1/containers/%s/start' % CONTAINER1['id'],
             {'Content-Length': '0'}, None)
        ]
        self.assertEqual(expect, self.api.calls)
        self.assertTrue(containers)

    def test_containers_delete(self):
        containers = self.mgr.delete(CONTAINER1['id'], force_delete1)
        expect = [
            ('DELETE', '/v1/containers/%s?force=%s' % (CONTAINER1['id'],
                                                       force_delete1),
             {}, None)
        ]
        self.assertEqual(expect, self.api.calls)
        self.assertIsNone(containers)

    def test_containers_delete_with_force(self):
        containers = self.mgr.delete(CONTAINER1['id'], force_delete2)
        expect = [
            ('DELETE', '/v1/containers/%s?force=%s' % (CONTAINER1['id'],
                                                       force_delete2),
             {}, None)
        ]
        self.assertEqual(expect, self.api.calls)
        self.assertIsNone(containers)

    def test_containers_stop(self):
        containers = self.mgr.stop(CONTAINER1['id'], timeout)
        expect = [
            ('POST', '/v1/containers/%s/stop?timeout=10' % CONTAINER1['id'],
             {'Content-Length': '0'}, None)
        ]
        self.assertEqual(expect, self.api.calls)
        self.assertTrue(containers)

    def test_containers_reboot(self):
        containers = self.mgr.reboot(CONTAINER1['id'], timeout)
        expect = [
            ('POST', '/v1/containers/%s/reboot?timeout=10' % CONTAINER1['id'],
             {'Content-Length': '0'}, None)
        ]
        self.assertEqual(expect, self.api.calls)
        self.assertTrue(containers)

    def test_containers_pause(self):
        containers = self.mgr.pause(CONTAINER1['id'])
        expect = [
            ('POST', '/v1/containers/%s/pause' % CONTAINER1['id'],
             {'Content-Length': '0'}, None)
        ]
        self.assertEqual(expect, self.api.calls)
        self.assertTrue(containers)

    def test_containers_unpause(self):
        containers = self.mgr.unpause(CONTAINER1['id'])
        expect = [
            ('POST', '/v1/containers/%s/unpause' % CONTAINER1['id'],
             {'Content-Length': '0'}, None)
        ]
        self.assertEqual(expect, self.api.calls)
        self.assertTrue(containers)

    def test_containers_logs(self):
        containers = self.mgr.logs(CONTAINER1['id'], stdout=True, stderr=True)
        expect = [
            ('GET', '/v1/containers/%s/logs?%s'
             % (CONTAINER1['id'], parse.urlencode({'stdout': True,
                                                   'stderr': True})),
             {'Content-Length': '0'}, None)
        ]
        self.assertEqual(expect, self.api.calls)
        self.assertIsNone(containers)

    def test_containers_execute(self):
        containers = self.mgr.execute(CONTAINER1['id'], CONTAINER1['command'])
        expect = [
            ('POST', '/v1/containers/%s/execute?%s'
             % (CONTAINER1['id'], parse.urlencode({'command':
                                                   CONTAINER1['command']})),
             {'Content-Length': '0'}, None)
        ]
        self.assertEqual(expect, self.api.calls)
        self.assertIsNone(containers)

    def test_containers_kill(self):
        containers = self.mgr.kill(CONTAINER1['id'], signal)
        expect = [
            ('POST', '/v1/containers/%s/kill?%s'
             % (CONTAINER1['id'], parse.urlencode({'signal': signal})),
             {'Content-Length': '0'}, None)
        ]
        self.assertEqual(expect, self.api.calls)
        self.assertIsNone(containers)

    def test_container_run(self):
        containers = self.mgr.run(**CREATE_CONTAINER1)
        expect = [
            ('POST', '/v1/containers?run=true', {}, CREATE_CONTAINER1)
        ]
        self.assertEqual(expect, self.api.calls)
        self.assertTrue(containers)

    def test_container_run_fail(self):
        run_container_fail = copy.deepcopy(CREATE_CONTAINER1)
        run_container_fail["wrong_key"] = "wrong"
        self.assertRaisesRegexp(exceptions.InvalidAttribute,
                                ("Key must be in %s" %
                                 ','.join(containers.CREATION_ATTRIBUTES)),
                                self.mgr.run, **run_container_fail)
        self.assertEqual([], self.api.calls)

    def test_containers_rename(self):
        containers = self.mgr.rename(CONTAINER1['id'], name)
        expect = [
            ('POST', '/v1/containers/%s/rename?%s'
             % (CONTAINER1['id'], parse.urlencode({'name': name})),
             {'Content-Length': '0'}, None)
        ]
        self.assertEqual(expect, self.api.calls)
        self.assertTrue(containers)

    def test_containers_attach(self):
        containers = self.mgr.attach(CONTAINER1['id'])
        expect = [
            ('GET', '/v1/containers/%s/attach' % CONTAINER1['id'],
             {'Content-Length': '0'}, None)
        ]
        self.assertEqual(expect, self.api.calls)
        self.assertIsNone(containers)

    def test_containers_resize(self):
        containers = self.mgr.resize(CONTAINER1['id'], tty_width, tty_height)
        expects = []
        expects.append([
            ('POST', '/v1/containers/%s/resize?w=%s&h=%s'
             % (CONTAINER1['id'], tty_width, tty_height),
             {'Content-Length': '0'}, None)
        ])
        expects.append([
            ('POST', '/v1/containers/%s/resize?h=%s&w=%s'
             % (CONTAINER1['id'], tty_height, tty_width),
             {'Content-Length': '0'}, None)
        ])
        self.assertTrue(self.api.calls in expects)
        self.assertIsNone(containers)

    def test_containers_top(self):
        containers = self.mgr.top(CONTAINER1['id'])
        expect = [
            ('GET', '/v1/containers/%s/top?ps_args=None' % CONTAINER1['id'],
             {'Content-Length': '0'}, None)
        ]
        self.assertEqual(expect, self.api.calls)
        self.assertIsNone(containers)
