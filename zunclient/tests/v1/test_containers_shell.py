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

from zunclient.tests.v1 import shell_test_base


class ShellTest(shell_test_base.TestCommandLineArgument):

    @mock.patch('zunclient.v1.containers_shell._show_container')
    @mock.patch('zunclient.v1.containers.ContainerManager.create')
    def test_zun_container_create_success_with_pull_policy(
            self, mock_create, mock_show_container):
        mock_create.return_value = 'container-never'
        self._test_arg_success(
            'create --image x --image-pull-policy never')
        mock_show_container.assert_called_with('container-never')

        mock_create.return_value = 'container-always'
        self._test_arg_success(
            'create --image x --image-pull-policy always')
        mock_show_container.assert_called_with('container-always')

        mock_create.return_value = 'container-ifnotpresent'
        self._test_arg_success(
            'create --image x --image-pull-policy ifnotpresent')
        mock_show_container.assert_called_with('container-ifnotpresent')

    @mock.patch('zunclient.v1.containers_shell._show_container')
    @mock.patch('zunclient.v1.containers.ContainerManager.create')
    def test_zun_container_create_success_without_pull_policy(
            self, mock_create, mock_show_container):
        mock_create.return_value = 'container'
        self._test_arg_success('create --image x')
        mock_show_container.assert_called_once_with('container')

    @mock.patch('zunclient.v1.containers.ContainerManager.create')
    def test_zun_container_create_failure_with_wrong_pull_policy(
            self, mock_create):
        self._test_arg_failure(
            'create --image x --image-pull-policy wrong',
            self._invalid_choice_error)
        self.assertFalse(mock_create.called)

    @mock.patch('zunclient.v1.containers_shell._show_container')
    @mock.patch('zunclient.v1.containers.ContainerManager.run')
    def test_zun_container_run_success_with_pull_policy(
            self, mock_run, mock_show_container):
        mock_run.return_value = 'container-never'
        self._test_arg_success(
            'run --image x --image-pull-policy never')
        mock_show_container.assert_called_with('container-never')

        mock_run.return_value = 'container-always'
        self._test_arg_success(
            'run --image x --image-pull-policy always')
        mock_show_container.assert_called_with('container-always')

        mock_run.return_value = 'container-ifnotpresent'
        self._test_arg_success(
            'run --image x --image-pull-policy ifnotpresent')
        mock_show_container.assert_called_with('container-ifnotpresent')

    @mock.patch('zunclient.v1.containers_shell._show_container')
    @mock.patch('zunclient.v1.containers.ContainerManager.run')
    def test_zun_container_run_success_without_pull_policy(
            self, mock_run, mock_show_container):
        mock_run.return_value = 'container'
        self._test_arg_success('run --image x')
        mock_show_container.assert_called_once_with('container')

    @mock.patch('zunclient.v1.containers.ContainerManager.run')
    def test_zun_container_run_failure_with_wrong_pull_policy(
            self, mock_run):
        self._test_arg_failure(
            'run --image x --image-pull-policy wrong',
            self._invalid_choice_error)
        self.assertFalse(mock_run.called)
