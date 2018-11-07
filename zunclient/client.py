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

import warnings

from oslo_utils import importutils

from zunclient import api_versions

osprofiler_profiler = importutils.try_import("osprofiler.profiler")


def _get_client_class_and_version(version):
    if not isinstance(version, api_versions.APIVersion):
        version = api_versions.get_api_version(version)
    else:
        api_versions.check_major_version(version)
    return version, importutils.import_class(
        'zunclient.v%s.client.Client' % version.ver_major)


def _check_arguments(kwargs, release, deprecated_name, right_name=None):
    """Process deprecation of arguments.

    Check presence of deprecated argument in kwargs, prints proper warning
    message, renames key to right one it needed.
    """
    if deprecated_name in kwargs:
        if right_name:
            if right_name in kwargs:
                msg = ('The %(old)s argument is deprecated in %(release)s'
                       'and its use may result in errors in future releases.'
                       'As %(new)s is provided, the %(old)s argument will '
                       'be ignored.') % {'old': deprecated_name,
                                         'release': release,
                                         'new': right_name}
                kwargs.pop(deprecated_name)
            else:
                msg = ('The %(old)s argument is deprecated in %(release)s '
                       'and its use may result in errors in future releases. '
                       'Use %(new)s instead.') % {'old': deprecated_name,
                                                  'release': release,
                                                  'new': right_name}
                kwargs[right_name] = kwargs.pop(deprecated_name)
        else:
            msg = ('The %(old)s argument is deprecated in %(release)s '
                   'and its use may result in errors in future '
                   'releases') % {'old': deprecated_name,
                                  'release': release}
            # NOTE(kiennt): just ignore it
            kwargs.pop(deprecated_name)
        warnings.warn(msg)


def Client(version='1', username=None, auth_url=None, **kwargs):
    """Initialize client objects based on given version"""
    _check_arguments(kwargs, 'Queens', 'api_key', right_name='password')
    # NOTE: OpenStack projects use 2 vars with one meaning: `endpoint_type`
    #       and `interface`. `endpoint_type` is an old name which was used by
    #       most OpenStack clients. Later it was replaced by `interface` in
    #       keystone and later some other clients switched to new var name too.
    _check_arguments(kwargs, 'Queens', 'endpoint_type',
                     right_name='interface')
    _check_arguments(kwargs, 'Queens', 'zun_url',
                     right_name='endpoint_override')
    _check_arguments(kwargs, 'Queens', 'tenant_name',
                     right_name='project_name')
    _check_arguments(kwargs, 'Queens', 'tenant_id', right_name='project_id')

    profile = kwargs.pop('profile', None)
    if osprofiler_profiler and profile:
        # Initialize the root of the future trace: the created trace ID
        # will be used as the very first parent to which all related
        # traces will be bound to. The given HMAC key must correspond to
        # the one set in zun-api zun.conf, otherwise the latter
        # will fail to check the request signature and will skip
        # initialization of osprofiler on the server side.
        osprofiler_profiler.init(profile)

    api_version, client_class = _get_client_class_and_version(version)
    if api_version.is_latest():
        c = client_class(api_version=api_versions.APIVersion("1.1"),
                         auth_url=auth_url,
                         username=username,
                         **kwargs)
        api_version = api_versions.discover_version(c, api_version)

    return client_class(api_version=api_version,
                        auth_url=auth_url,
                        username=username,
                        **kwargs)
