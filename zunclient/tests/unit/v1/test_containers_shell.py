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

from zunclient.common.apiclient import exceptions as apiexec
from zunclient.common import utils as zun_utils
from zunclient.common.websocketclient import exceptions
from zunclient.tests.unit.v1 import shell_test_base
from zunclient.v1 import containers_shell


def _get_container_args(**kwargs):
    default_args = {
        'auto_remove': False,
        'environment': {},
        'hints': {},
        'labels': {},
        'mounts': [],
        'nets': [],
        'command': [],
    }
    default_args.update(kwargs)
    return default_args


class ShellTest(shell_test_base.TestCommandLineArgument):

    @mock.patch('zunclient.v1.containers_shell._show_container')
    @mock.patch('zunclient.v1.containers.ContainerManager.create')
    def test_zun_container_create_success(self, mock_create,
                                          mock_show_container):
        mock_create.return_value = 'container'
        self._test_arg_success('create x')
        mock_show_container.assert_called_once_with('container')

    @mock.patch('zunclient.common.utils.list_containers')
    @mock.patch('zunclient.v1.containers.ContainerManager.list')
    def test_zun_container_list_success(self, mock_list, mock_list_containers):
        mock_list.return_value = ['container']
        self._test_arg_success('list')
        mock_list_containers.assert_called_once_with(['container'])

    @mock.patch('zunclient.v1.containers_shell._show_container')
    @mock.patch('zunclient.v1.containers.ContainerManager.get')
    def test_zun_container_show_success(self, mock_get, mock_show_container):
        mock_get.return_value = 'container'
        self._test_arg_success('show x')
        mock_show_container.assert_called_once_with('container')

    @mock.patch('zunclient.v1.containers.ContainerManager.list')
    def test_zun_container_command_failure(self, mock_list):
        self._test_arg_failure('list --wrong',
                               self._unrecognized_arg_error)
        self.assertFalse(mock_list.called)

    @mock.patch('zunclient.common.cliutils.print_dict')
    def test_show_container(self, mock_print_dict):
        fake_container = mock.MagicMock()
        fake_container._info = {}
        fake_container.addresses = {'private': [{'addr': '10.0.0.1'}]}
        containers_shell._show_container(fake_container)
        mock_print_dict.assert_called_once_with({'networks': 'private',
                                                 'addresses': '10.0.0.1'})

    @mock.patch('zunclient.common.cliutils.print_list')
    def test_list_container(self, mock_print_list):
        fake_container = mock.MagicMock()
        fake_container._info = {}
        fake_container.addresses = {'private': [{'addr': '10.0.0.1'}]}
        zun_utils.list_containers([fake_container])
        self.assertTrue(mock_print_list.called)
        self.assertEqual(fake_container.addresses, '10.0.0.1')

    @mock.patch('zunclient.v1.containers_shell._show_container')
    @mock.patch('zunclient.v1.containers.ContainerManager.create')
    def test_zun_container_create_success_with_pull_policy(
            self, mock_create, mock_show_container):
        mock_create.return_value = 'container-never'
        self._test_arg_success(
            'create --image-pull-policy never x')
        mock_show_container.assert_called_with('container-never')
        mock_create.assert_called_with(
            **_get_container_args(image='x', image_pull_policy='never'))

        mock_create.return_value = 'container-always'
        self._test_arg_success(
            'create --image-pull-policy always x')
        mock_show_container.assert_called_with('container-always')
        mock_create.assert_called_with(
            **_get_container_args(image='x', image_pull_policy='always'))

        mock_create.return_value = 'container-ifnotpresent'
        self._test_arg_success(
            'create --image-pull-policy ifnotpresent x')
        mock_show_container.assert_called_with('container-ifnotpresent')
        mock_create.assert_called_with(
            **_get_container_args(image='x', image_pull_policy='ifnotpresent'))

    @mock.patch('zunclient.v1.containers_shell._show_container')
    @mock.patch('zunclient.v1.containers.ContainerManager.create')
    def test_zun_container_create_success_without_pull_policy(
            self, mock_create, mock_show_container):
        mock_create.return_value = 'container'
        self._test_arg_success('create x')
        mock_show_container.assert_called_once_with('container')
        mock_create.assert_called_with(**_get_container_args(image='x'))

    @mock.patch('zunclient.v1.containers.ContainerManager.create')
    def test_zun_container_create_failure_with_wrong_pull_policy(
            self, mock_create):
        self._test_arg_failure(
            'create --image-pull-policy wrong x ',
            self._invalid_choice_error)
        self.assertFalse(mock_create.called)
        mock_create.assert_not_called()

    @mock.patch('zunclient.v1.containers_shell._show_container')
    @mock.patch('zunclient.v1.containers.ContainerManager.run')
    def test_zun_container_run_success_with_pull_policy(
            self, mock_run, mock_show_container):
        mock_run.return_value = 'container-never'
        self._test_arg_success(
            'run --image-pull-policy never x')
        mock_show_container.assert_called_with('container-never')
        mock_run.assert_called_with(
            **_get_container_args(image='x', image_pull_policy='never'))

        mock_run.return_value = 'container-always'
        self._test_arg_success(
            'run --image-pull-policy always x ')
        mock_show_container.assert_called_with('container-always')
        mock_run.assert_called_with(
            **_get_container_args(image='x', image_pull_policy='always'))

        mock_run.return_value = 'container-ifnotpresent'
        self._test_arg_success(
            'run --image-pull-policy ifnotpresent x')
        mock_show_container.assert_called_with('container-ifnotpresent')
        mock_run.assert_called_with(
            **_get_container_args(image='x', image_pull_policy='ifnotpresent'))

    @mock.patch('zunclient.v1.containers_shell._show_container')
    @mock.patch('zunclient.v1.containers.ContainerManager.run')
    def test_zun_container_run_success_without_pull_policy(
            self, mock_run, mock_show_container):
        mock_run.return_value = 'container'
        self._test_arg_success('run x')
        mock_show_container.assert_called_once_with('container')
        mock_run.assert_called_with(**_get_container_args(image='x'))

    @mock.patch('zunclient.v1.containers.ContainerManager.run')
    def test_zun_container_run_failure_with_wrong_pull_policy(
            self, mock_run):
        self._test_arg_failure(
            'run --image-pull-policy wrong x',
            self._invalid_choice_error)
        self.assertFalse(mock_run.called)
        mock_run.assert_not_called()

    @mock.patch('zunclient.v1.containers.ContainerManager.get')
    @mock.patch('zunclient.v1.containers_shell._show_container')
    @mock.patch('zunclient.v1.containers.ContainerManager.run')
    def test_zun_container_run_interactive(self, mock_run,
                                           mock_show_container,
                                           mock_get_container):
        fake_container = mock.MagicMock()
        fake_container.uuid = 'fake_uuid'
        mock_run.return_value = fake_container
        fake_container.status = 'Error'
        mock_get_container.return_value = fake_container
        self.assertRaises(exceptions.ContainerStateError,
                          self.shell,
                          'run -i x ')

    @mock.patch('zunclient.v1.containers_shell._show_container')
    @mock.patch('zunclient.v1.containers.ContainerManager.run')
    def test_zun_container_run_success_with_runtime(
            self, mock_run, mock_show_container):
        mock_run.return_value = 'container'
        self._test_arg_success('run --runtime runc x')
        mock_show_container.assert_called_once_with('container')
        mock_run.assert_called_with(
            **_get_container_args(image='x', runtime='runc'))

    @mock.patch('zunclient.v1.containers_shell._show_container')
    @mock.patch('zunclient.v1.containers.ContainerManager.run')
    def test_zun_container_run_success_with_availability_zone(
            self, mock_run, mock_show_container):
        mock_run.return_value = 'container'
        self._test_arg_success('run --availability-zone nova x')
        mock_show_container.assert_called_once_with('container')

    @mock.patch('zunclient.v1.containers_shell._show_container')
    @mock.patch('zunclient.v1.containers.ContainerManager.run')
    def test_zun_container_run_with_mount(
            self, mock_run, mock_show_container):
        mock_run.return_value = 'container'
        self._test_arg_success(
            'run --mount source=s,destination=d x')
        mock_show_container.assert_called_once_with('container')
        mounts = [{'source': 's', 'destination': 'd'}]
        mock_run.assert_called_with(
            **_get_container_args(image='x', mounts=mounts))

    def test_zun_container_run_with_mount_invalid_format(self):
        self.assertRaisesRegex(
            apiexec.CommandError, 'Invalid mounts argument',
            self.shell,
            'run --mount source,destination=d x')

    def test_zun_container_run_with_mount_missed_key(self):
        self.assertRaisesRegex(
            apiexec.CommandError, 'Invalid mounts argument',
            self.shell,
            'run --mount source=s x')

    def test_zun_container_run_with_mount_duplicated_key(self):
        self.assertRaisesRegex(
            apiexec.CommandError, 'Invalid mounts argument',
            self.shell,
            'run --mount source=s,source=s,destination=d x')

    def test_zun_container_run_with_mount_invalid_key(self):
        self.assertRaisesRegex(
            apiexec.CommandError, 'Invalid mounts argument',
            self.shell,
            'run --mount invalid=s,destination=d x')

    @mock.patch('zunclient.v1.containers_shell._show_container')
    @mock.patch('zunclient.v1.containers.ContainerManager.run')
    def test_zun_container_run_success_with_hostname(
        self, mock_run, mock_show):
        mock_run.return_value = 'container'
        self._test_arg_success('run --hostname testhost x')
        mock_show.assert_called_once_with('container')
        mock_run.assert_called_with(
            **_get_container_args(image='x', hostname='testhost'))
