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

import re

import mock
from testtools import matchers

from zunclient import api_versions
from zunclient.tests.unit import utils

FAKE_ENV = {'OS_USERNAME': 'username',
            'OS_PASSWORD': 'password',
            'OS_PROJECT_NAME': 'project_name',
            'OS_AUTH_URL': 'http://no.where/v2.0',
            'BYPASS_URL': 'http://zun'}


class TestCommandLineArgument(utils.TestCase):
    _unrecognized_arg_error = [
        '.*?^usage: ',
        '.*?^error: unrecognized arguments:',
        ".*?^Try 'zun help ' for more information.",
        ]

    _mandatory_arg_error = [
        '.*?^usage: ',
        '.*?^error: (the following arguments|argument)',
        ".*?^Try 'zun help ",
        ]

    _few_argument_error = [
        '.*?^usage: zun ',
        '.*?^error: (the following arguments|too few arguments)',
        ".*?^Try 'zun help ",
        ]

    _invalid_value_error = [
        '.*?^usage: ',
        '.*?^error: argument .*: invalid .* value:',
        ".*?^Try 'zun help ",
        ]

    _invalid_choice_error = [
        '.*?^usage: ',
        '.*?^error: argument .*: invalid choice:',
        ".*?^Try 'zun help ",
        ]

    def setUp(self):
        super(TestCommandLineArgument, self).setUp()
        self.make_env(fake_env=FAKE_ENV)
        session_client = mock.patch(
            'zunclient.common.httpclient.SessionClient')
        session_client.start()
        loader = mock.patch('keystoneauth1.loading.get_plugin_loader')
        loader.start()
        session = mock.patch('keystoneauth1.session.Session')
        session.start()
        discover = mock.patch('zunclient.api_versions.discover_version',
                              return_value=api_versions.APIVersion('1.1'))
        discover.start()

        self.addCleanup(session_client.stop)
        self.addCleanup(loader.stop)
        self.addCleanup(session.stop)
        self.addCleanup(discover.stop)

    def _test_arg_success(self, command):
        stdout, stderr = self.shell(command)

    def _test_arg_failure(self, command, error_msg):
        stdout, stderr = self.shell(command, (2,))
        for line in error_msg:
            self.assertThat((stdout + stderr),
                            matchers.MatchesRegex(line,
                            re.DOTALL | re.MULTILINE))
