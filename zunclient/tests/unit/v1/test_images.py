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
from zunclient.v1 import images


IMAGE1 = {'uuid': '092e2ed7-af11-4fa7-8ffa-c3ee9d5b451a',
          'image_id': 'b8ff79200466',
          'repo': 'fake-repo1',
          'tag': 'latest',
          'size': '1024',
          }
IMAGE2 = {'uuid': '1996ba70-b074-454b-a8fc-0895ae26c7c6',
          'image_id': '21c16b6787c6',
          'repo': 'fake-repo2',
          'tag': 'latest',
          'size': '1024',
          }
IMAGE3 = {'uuid': '1267gf34-34e4-tf4b-b84c-1345avf6c7c6',
          'image_id': '24r5tt6y87c6',
          'image': 'fake-name3',
          'tag': 'latest',
          'size': '1024',
          'image_driver': 'fake-driver',
          }
SEARCH_IMAGE = {'image': 'fake-name3',
                'image_driver': 'fake-driver',
                }


fake_responses = {
    '/v1/images/':
    {
        'GET': (
            {},
            {'images': [IMAGE1, IMAGE2]},
        ),
    },
    '/v1/images/?limit=2':
    {
        'GET': (
            {},
            {'images': [IMAGE1, IMAGE2]},
        ),
    },
    '/v1/images/?marker=%s' % IMAGE2['image_id']:
    {
        'GET': (
            {},
            {'images': [IMAGE1, IMAGE2]},
        ),
    },
    '/v1/images/?limit=2&marker=%s' % IMAGE2['image_id']:
    {
        'GET': (
            {},
            {'images': [IMAGE2, IMAGE1]},
        ),
    },
    '/v1/images/?sort_dir=asc':
    {
        'GET': (
            {},
            {'images': [IMAGE1, IMAGE2]},
        ),
    },
    '/v1/images/?sort_key=image_id':
    {
        'GET': (
            {},
            {'images': [IMAGE1, IMAGE2]},
        ),
    },
    '/v1/images/?sort_key=image_id&sort_dir=desc':
    {
        'GET': (
            {},
            {'images': [IMAGE2, IMAGE1]},
        ),
    },
    '/v1/images/%s/search?image_driver=%s' % (IMAGE3['image'],
                                              IMAGE3['image_driver']):
    {
        'GET': (
            {},
            {'images': [IMAGE3]},
        ),
    },
}


class ImageManagerTest(testtools.TestCase):

    def setUp(self):
        super(ImageManagerTest, self).setUp()
        self.api = utils.FakeAPI(fake_responses)
        self.mgr = images.ImageManager(self.api)

    def test_image_list(self):
        images = self.mgr.list()
        expect = [
            ('GET', '/v1/images/', {}, None),
        ]
        self.assertEqual(expect, self.api.calls)
        self.assertThat(images, matchers.HasLength(2))

    def _test_image_list_with_filters(
            self, limit=None, marker=None,
            sort_key=None, sort_dir=None,
            expect=[]):
        images_filter = self.mgr.list(limit=limit, marker=marker,
                                      sort_key=sort_key,
                                      sort_dir=sort_dir)
        self.assertEqual(expect, self.api.calls)
        self.assertThat(images_filter, matchers.HasLength(2))

    def test_image_list_with_limit(self):
        expect = [
            ('GET', '/v1/images/?limit=2', {}, None),
        ]
        self._test_image_list_with_filters(
            limit=2,
            expect=expect)

    def test_image_list_with_marker(self):
        expect = [
            ('GET', '/v1/images/?marker=%s' % IMAGE2['image_id'],
             {}, None),
        ]
        self._test_image_list_with_filters(
            marker=IMAGE2['image_id'],
            expect=expect)

    def test_image_list_with_marker_limit(self):
        expect = [
            ('GET', '/v1/images/?limit=2&marker=%s' % IMAGE2['image_id'],
             {}, None),
        ]
        self._test_image_list_with_filters(
            limit=2, marker=IMAGE2['image_id'],
            expect=expect)

    def test_image_list_with_sort_dir(self):
        expect = [
            ('GET', '/v1/images/?sort_dir=asc',
             {}, None),
        ]
        self._test_image_list_with_filters(
            sort_dir='asc',
            expect=expect)

    def test_image_list_with_sort_key(self):
        expect = [
            ('GET', '/v1/images/?sort_key=image_id',
             {}, None),
        ]
        self._test_image_list_with_filters(
            sort_key='image_id',
            expect=expect)

    def test_image_list_with_sort_key_dir(self):
        expect = [
            ('GET', '/v1/images/?sort_key=image_id&sort_dir=desc',
             {}, None),
        ]
        self._test_image_list_with_filters(
            sort_key='image_id', sort_dir='desc',
            expect=expect)

    def test_image_search(self):
        images = self.mgr.search_image(**SEARCH_IMAGE)
        url = '/v1/images/%s/search?image_driver=%s' \
              % (IMAGE3['image'], IMAGE3['image_driver'])
        expect = [
            ('GET', url, {}, None),
        ]
        self.assertEqual(expect, self.api.calls)
        self.assertThat(images, matchers.HasLength(1))
