# Copyright 2015 NEC Corporation.  All rights reserved.
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

import mock

from zunclient.tests.unit.v1 import shell_test_base


class ShellTest(shell_test_base.TestCommandLineArgument):

    @mock.patch('zunclient.v1.images.ImageManager.list')
    def test_zun_image_list_success(self, mock_list):
        self._test_arg_success('image-list')
        self.assertTrue(mock_list.called)

    @mock.patch('zunclient.v1.images.ImageManager.list')
    def test_zun_image_list_failure(self, mock_list):
        self._test_arg_failure('image-list --wrong',
                               self._unrecognized_arg_error)
        self.assertFalse(mock_list.called)

    @mock.patch('zunclient.v1.images.ImageManager.get')
    def test_zun_image_show_success(self, mock_get):
        self._test_arg_success('image-show 111')
        self.assertTrue(mock_get.called)

    @mock.patch('zunclient.v1.images.ImageManager.get')
    def test_zun_image_show_failure(self, mock_get):
        self._test_arg_failure('image-show --wrong 1111',
                               self._unrecognized_arg_error)
        self.assertFalse(mock_get.called)

    @mock.patch('zunclient.v1.images.ImageManager.search_image')
    def test_zun_image_search_with_driver(self, mock_search_image):
        self._test_arg_success('image-search 111 --image_driver glance')
        self.assertTrue(mock_search_image.called)

    @mock.patch('zunclient.v1.images.ImageManager.search_image')
    def test_zun_image_search_default_driver(self, mock_search_image):
        self._test_arg_success('image-search 111')
        self.assertTrue(mock_search_image.called)

    @mock.patch('zunclient.v1.images.ImageManager.search_image')
    def test_zun_image_search_failure(self, mock_search_image):
        self._test_arg_failure('image-search --wrong 1111',
                               self._unrecognized_arg_error)
        self.assertFalse(mock_search_image.called)
