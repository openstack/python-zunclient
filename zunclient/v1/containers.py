# Copyright 2014 NEC Corporation.  All rights reserved.
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

from six.moves.urllib import parse

from zunclient import api_versions
from zunclient.common import base
from zunclient.common import utils
from zunclient import exceptions


CREATION_ATTRIBUTES = ['name', 'image', 'command', 'cpu', 'memory',
                       'environment', 'workdir', 'labels', 'image_pull_policy',
                       'restart_policy', 'interactive', 'image_driver',
                       'security_groups', 'hints', 'nets', 'auto_remove',
                       'runtime', 'hostname', 'mounts', 'disk',
                       'availability_zone', 'auto_heal', 'privileged',
                       'exposed_ports', 'healthcheck', 'registry', 'tty']


class Container(base.Resource):
    def __repr__(self):
        return "<Container %s>" % self._info


class ContainerManager(base.Manager):
    resource_class = Container

    @staticmethod
    def _path(id=None):

        if id:
            return '/v1/containers/%s' % id
        else:
            return '/v1/containers'

    def list(self, marker=None, limit=None, sort_key=None,
             sort_dir=None, all_projects=False, **kwargs):
        """Retrieve a list of containers.

        :param all_projects: Optional, list containers in all projects

        :param marker: Optional, the UUID of a containers, eg the last
                       containers from a previous result set. Return
                       the next result set.
        :param limit: The maximum number of results to return per
                      request, if:

            1) limit > 0, the maximum number of containers to return.
            2) limit param is NOT specified (None), the number of items
               returned respect the maximum imposed by the ZUN API
               (see Zun's api.max_limit option).

        :param sort_key: Optional, field used for sorting.

        :param sort_dir: Optional, direction of sorting, either 'asc' (the
                         default) or 'desc'.

        :returns: A list of containers.

        """
        if limit is not None:
            limit = int(limit)

        filters = utils.common_filters(marker, limit, sort_key,
                                       sort_dir, all_projects)
        path = ''
        if filters:
            path += '?' + '&'.join(filters)

        if limit is None:
            return self._list(self._path(path),
                              "containers", qparams=kwargs)
        else:
            return self._list_pagination(self._path(path),
                                         "containers",
                                         limit=limit)

    def get(self, id, **kwargs):
        try:
            return self._list(self._path(id),
                              qparams=kwargs)[0]
        except IndexError:
            return None

    def create(self, **kwargs):
        self._process_command(kwargs)
        self._process_mounts(kwargs)
        self._process_tty(kwargs)

        new = {}
        for (key, value) in kwargs.items():
            if key in CREATION_ATTRIBUTES:
                new[key] = value
            else:
                raise exceptions.InvalidAttribute(
                    "Key must be in %s" % ','.join(CREATION_ATTRIBUTES))
        return self._create(self._path(), new)

    def _process_command(self, kwargs):
        cmd_microversion = api_versions.APIVersion("1.20")
        if self.api_version < cmd_microversion:
            command = kwargs.pop('command', None)
            if command:
                kwargs['command'] = utils.parse_command(command)

    def _process_mounts(self, kwargs):
        mounts = kwargs.get('mounts', None)
        if mounts:
            for mount in mounts:
                if mount.get('type') == 'bind':
                    mount['source'] = utils.encode_file_data(mount['source'])

    def _process_tty(self, kwargs):
        tty_microversion = api_versions.APIVersion("1.36")
        if self.api_version >= tty_microversion:
            if 'interactive' in kwargs and 'tty' not in kwargs:
                kwargs['tty'] = kwargs['interactive']

    def delete(self, id, **kwargs):
        return self._delete(self._path(id),
                            qparams=kwargs)

    def _action(self, id, action, method='POST', qparams=None, **kwargs):
        if qparams:
            action = "%s?%s" % (action,
                                parse.urlencode(qparams))
        kwargs.setdefault('headers', {})
        kwargs['headers'].setdefault('Content-Length', '0')
        resp, body = self.api.json_request(method,
                                           self._path(id) + action,
                                           **kwargs)
        return resp, body

    def start(self, id):
        return self._action(id, '/start')

    def stop(self, id, timeout):
        return self._action(id, '/stop',
                            qparams={'timeout': timeout})

    def rebuild(self, id, **kwargs):
        return self._action(id, '/rebuild',
                            qparams=kwargs)

    def restart(self, id, timeout):
        return self._action(id, '/reboot',
                            qparams={'timeout': timeout})

    def pause(self, id):
        return self._action(id, '/pause')

    def unpause(self, id):
        return self._action(id, '/unpause')

    def logs(self, id, **kwargs):
        if kwargs['stdout'] is False and kwargs['stderr'] is False:
            kwargs['stdout'] = True
            kwargs['stderr'] = True
        return self._action(id, '/logs', method='GET',
                            qparams=kwargs)[1]

    def execute(self, id, **kwargs):
        return self._action(id, '/execute',
                            qparams=kwargs)[1]

    def execute_resize(self, id, exec_id, width, height):
        self._action(id, '/execute_resize',
                     qparams={'exec_id': exec_id, 'w': width, 'h': height})[1]

    def kill(self, id, signal=None):
        return self._action(id, '/kill',
                            qparams={'signal': signal})[1]

    def run(self, **kwargs):
        self._process_command(kwargs)
        self._process_mounts(kwargs)
        self._process_tty(kwargs)

        if not set(kwargs).issubset(CREATION_ATTRIBUTES):
            raise exceptions.InvalidAttribute(
                "Key must be in %s" % ','.join(CREATION_ATTRIBUTES))
        else:
            return self._create(self._path() + '?run=true', kwargs)

    def rename(self, id, name):
        return self._action(id, '/rename',
                            qparams={'name': name})

    def update(self, id, **patch):
        return self._update(self._path(id), patch)

    def attach(self, id):
        return self._action(id, '/attach', method='GET')[1]

    def resize(self, id, width, height):
        return self._action(id, '/resize',
                            qparams={'w': width, 'h': height})[1]

    def top(self, id, ps_args=None):
        return self._action(id, '/top', method='GET',
                            qparams={'ps_args': ps_args})[1]

    def get_archive(self, id, path):
        res = self._action(id, '/get_archive', method='GET',
                           qparams={'path': path})[1]
        # API version 1.25 or later will return Base64-encoded data
        if self.api_version >= api_versions.APIVersion("1.25"):
            res['data'] = utils.decode_file_data(res['data'])
        else:
            res['data'] = res['data'].encode()
        return res

    def put_archive(self, id, path, data):
        # API version 1.25 or later will expect Base64-encoded data
        if self.api_version >= api_versions.APIVersion("1.25"):
            data = utils.encode_file_data(data)
        return self._action(id, '/put_archive',
                            qparams={'path': path},
                            body={'data': data})

    def stats(self, id):
        return self._action(id, '/stats', method='GET')[1]

    def commit(self, id, repository, tag=None):
        if tag is not None:
            return self._action(id, '/commit', qparams={
                                'repository': repository, 'tag': tag})[1]
        else:
            return self._action(id, '/commit', qparams={
                                'repository': repository})[1]

    def add_security_group(self, id, security_group):
        return self._action(id, '/add_security_group',
                            qparams={'name': security_group})

    def network_detach(self, container, **kwargs):
        return self._action(container, '/network_detach',
                            qparams=kwargs)

    def network_attach(self, container, **kwargs):
        return self._action(container, '/network_attach',
                            qparams=kwargs)

    def network_list(self, container):
        return self._list(self._path(container) + '/network_list',
                          "networks")

    def remove_security_group(self, id, security_group):
        return self._action(id, '/remove_security_group',
                            qparams={'name': security_group})
