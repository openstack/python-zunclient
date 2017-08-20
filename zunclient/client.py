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

from oslo_utils import importutils

from zunclient import api_versions
from zunclient import exceptions
from zunclient.i18n import _


def _get_client_class_and_version(version):
    if not isinstance(version, api_versions.APIVersion):
        version = api_versions.get_api_version(version)
    else:
        api_versions.check_major_version(version)
    if version.is_latest():
        raise exceptions.UnsupportedVersion(
            _('The version should be explicit, not latest.'))
    return version, importutils.import_class(
        'zunclient.v%s.client.Client' % version.ver_major)


def Client(version='1', username=None, auth_url=None, **kwargs):
    """Initialize client objects based on given version"""
    api_version, client_class = _get_client_class_and_version(version)
    return client_class(api_version=api_version,
                        auth_url=auth_url,
                        username=username,
                        **kwargs)
