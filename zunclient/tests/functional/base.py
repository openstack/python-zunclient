# Copyright (c) 2016 Mirantis, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import os

import six
import six.moves.configparser as config_parser
from tempest.lib.cli import base

DEFAULT_CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'test.conf')


class FunctionalTestBase(base.ClientTestBase):
    """Container base class, calls to zunclient."""

    def setUp(self):
        super(FunctionalTestBase, self).setUp()
        self.client = self._get_clients()

    def _get_clients(self):
        # NOTE(aarefiev): {toxinidir} is a current working directory, so
        # the tox env path is {toxinidir}/.tox
        cli_dir = os.path.join(os.path.abspath('.'), '.tox/functional/bin')

        config = self._get_config()
        if config.get('os_auth_url'):
            client = base.CLIClient(cli_dir=cli_dir,
                                    username=config['os_username'],
                                    password=config['os_password'],
                                    tenant_name=config['os_project_name'],
                                    uri=config['os_auth_url'])
            for keystone_object in 'user', 'project':
                domain_attr = 'os_%s_domain_id' % keystone_object
                if config.get(domain_attr):
                    setattr(self, domain_attr, config[domain_attr])
        else:
            self.zun_url = config['zun_url']
            self.os_auth_token = config['os_auth_token']
            client = base.CLIClient(cli_dir=cli_dir,
                                    zun_url=self.zun_url,
                                    os_auth_token=self.os_auth_token)
        return client

    def _get_config(self):
        config_file = os.environ.get('ZUNCLIENT_TEST_CONFIG',
                                     DEFAULT_CONFIG_FILE)
        # SafeConfigParser was deprecated in Python 3.2
        if six.PY3:
            config = config_parser.ConfigParser()
        else:
            config = config_parser.SafeConfigParser()
        if not config.read(config_file):
            self.skipTest('Skipping, no test config found @ %s' % config_file)
        try:
            auth_strategy = config.get('functional', 'auth_strategy')
        except config_parser.NoOptionError:
            auth_strategy = 'keystone'
        if auth_strategy not in ['keystone', 'noauth']:
            raise self.fail(
                'Invalid auth type specified: %s in functional must be '
                'one of: [keystone, noauth]' % auth_strategy)

        conf_settings = []
        keystone_v3_conf_settings = []
        if auth_strategy == 'keystone':
            conf_settings += ['os_auth_url', 'os_username',
                              'os_password', 'os_project_name',
                              'os_identity_api_version']
            keystone_v3_conf_settings += ['os_user_domain_id',
                                          'os_project_domain_id']
        else:
            conf_settings += ['os_auth_token', 'zun_url']

        cli_flags = {}
        missing = []
        for c in conf_settings + keystone_v3_conf_settings:
            try:
                cli_flags[c] = config.get('functional', c)
            except config_parser.NoOptionError:
                # NOTE(vdrok): Here we ignore the absence of KS v3 options as
                # v2 may be used. Keystone client will do the actual check of
                # the parameters' correctness.
                if c not in keystone_v3_conf_settings:
                    missing.append(c)
        if missing:
            self.fail('Missing required setting in test.conf (%(conf)s) for '
                      'auth_strategy=%(auth)s: %(missing)s' %
                      {'conf': config_file,
                       'auth': auth_strategy,
                       'missing': ','.join(missing)})
        return cli_flags

    def _cmd_no_auth(self, cmd, action, flags='', params=''):
        """Execute given command with noauth attributes.

        :param cmd: command to be executed
        :type cmd: string
        :param action: command on cli to run
        :type action: string
        :param flags: optional cli flags to use
        :type flags: string
        :param params: optional positional args to use
        :type params: string
        """
        flags = ('--os_auth_token %(token)s --zun_url %(url)s %(flags)s'
                 %
                 {'token': self.os_auth_token,
                  'url': self.zun_url,
                  'flags': flags})
        return base.execute(cmd, action, flags, params,
                            cli_dir=self.client.cli_dir)

    def _zun(self, action, cmd='zun', flags='', params='', merge_stderr=False):
        """Execute Zun command for the given action.

        :param action: the cli command to run using Zun
        :type action: string
        :param cmd: the base of cli command to run
        :type action: string
        :param flags: any optional cli flags to use
        :type flags: string
        :param params: any optional positional args to use
        :type params: string
        :param merge_stderr: whether to merge stderr into the result
        :type merge_stderr: bool
        """
        if cmd == 'openstack':
            config = self._get_config()
            id_api_version = config['os_identity_api_version']
            flags += ' --os-identity-api-version {0}'.format(id_api_version)
        else:
            flags += ' --os-endpoint-type publicURL'

        if hasattr(self, 'os_auth_token'):
            return self._cmd_no_auth(cmd, action, flags, params)
        else:
            for keystone_object in 'user', 'project':
                domain_attr = 'os_%s_domain_id' % keystone_object
                if hasattr(self, domain_attr):
                    flags += ' --os-%(ks_obj)s-domain-id %(value)s' % {
                        'ks_obj': keystone_object,
                        'value': getattr(self, domain_attr)
                    }
            return self.client.cmd_with_auth(
                cmd, action, flags, params, merge_stderr=merge_stderr)

    def zun(self, action, flags='', params='', parse=True):
        """Return parsed list of dicts with basic item info.

        :param action: the cli command to run using Container
        :type action: string
        :param flags: any optional cli flags to use
        :type flags: string
        :param params: any optional positional args to use
        :type params: string
        :param parse: return parsed list or raw output
        :type parse: bool
        """
        output = self._zun(action=action, flags=flags, params=params)
        return self.parser.listing(output) if parse else output

    def get_table_headers(self, action, flags='', params=''):
        output = self._zun(action=action, flags=flags, params=params)
        table = self.parser.table(output)
        return table['headers']

    def assertTableHeaders(self, field_names, table_headers):
        """Assert that field_names and table_headers are equal.

        :param field_names: field names from the output table of the cmd
        :param table_headers: table headers output from cmd
        """
        self.assertEqual(sorted(field_names), sorted(table_headers))

    def list_containers(self, params=''):
        return self.zun('container-list', params=params)
