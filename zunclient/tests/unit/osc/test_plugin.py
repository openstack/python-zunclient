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

from zunclient import api_versions
from zunclient.osc import plugin
from zunclient.tests.unit import base


class TestContainerPlugin(base.TestCase):

    @mock.patch("zunclient.api_versions.get_api_version")
    @mock.patch("zunclient.v1.client.Client")
    def test_make_client(self, p_client, mock_get_api_version):

        instance = mock.Mock()
        instance._api_version = {"container": '1'}
        instance._region_name = 'zun_region'
        instance.session = 'zun_session'
        mock_get_api_version.return_value = api_versions.APIVersion('1.2')

        plugin.make_client(instance)
        p_client.assert_called_with(region_name='zun_region',
                                    session='zun_session',
                                    service_type='container',
                                    api_version=api_versions.APIVersion('1.2'))
