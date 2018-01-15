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

    @mock.patch('zunclient.v1.versions.VersionManager.list')
    def test_zun_version_list_success(self, mock_list):
        self._test_arg_success('version-list')
        self.assertTrue(mock_list.called)

    @mock.patch('zunclient.v1.versions.VersionManager.list')
    def test_zun_version_list_failure(self, mock_list):
        self._test_arg_failure('version-list --wrong',
                               self._unrecognized_arg_error)
        self.assertFalse(mock_list.called)
