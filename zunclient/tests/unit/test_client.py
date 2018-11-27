# Copyright (c) 2015 IBM Corp.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import mock
import testtools

from zunclient import api_versions
from zunclient import client
from zunclient import exceptions


class ClientTest(testtools.TestCase):

    @mock.patch('zunclient.api_versions.discover_version',
                return_value=api_versions.APIVersion('1.1'))
    @mock.patch('zunclient.v1.client.Client')
    def test_no_version_argument(self, mock_zun_client_v1,
                                 mock_discover_version):
        client.Client(auth_url='http://example/identity',
                      username='admin')
        mock_zun_client_v1.assert_called_with(
            api_version=api_versions.APIVersion('1.1'),
            auth_url='http://example/identity',
            username='admin')

    @mock.patch('zunclient.api_versions.discover_version',
                return_value=api_versions.APIVersion('1.1'))
    @mock.patch('zunclient.v1.client.Client')
    def test_valid_version_argument(self, mock_zun_client_v1,
                                    mock_discover_version):
        client.Client(version='1',
                      auth_url='http://example/identity',
                      username='admin')
        mock_zun_client_v1.assert_called_with(
            api_version=api_versions.APIVersion('1.1'),
            auth_url='http://example/identity',
            username='admin')

    def test_invalid_version_argument(self):
        self.assertRaises(
            exceptions.UnsupportedVersion,
            client.Client, version='2')
