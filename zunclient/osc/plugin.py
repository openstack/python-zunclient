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

import argparse
from oslo_log import log as logging

from osc_lib import utils

from zunclient import api_versions

LOG = logging.getLogger(__name__)

DEFAULT_CONTAINER_API_VERSION = api_versions.DEFAULT_API_VERSION
API_VERSION_OPTION = "os_container_api_version"
API_NAME = "container"
LAST_KNOWN_API_VERSION = int(DEFAULT_CONTAINER_API_VERSION.split('.')[1])
API_VERSIONS = {
    '1.%d' % i: 'zunclient.v1.client.Client'
    for i in range(1, LAST_KNOWN_API_VERSION + 1)
}
API_VERSIONS['1'] = API_VERSIONS[DEFAULT_CONTAINER_API_VERSION]


def make_client(instance):
    """Returns a zun service client"""
    zun_client = utils.get_client_class(
        API_NAME,
        instance._api_version[API_NAME],
        API_VERSIONS)
    LOG.debug("Instantiating zun client: {0}".format(
              zun_client))

    # TODO(hongbin): Instead of hard-coding api-version to 'latest', it is
    # better to read micro-version from CLI (bug #1701939).
    api_version = api_versions.get_api_version(instance._api_version[API_NAME])
    client = zun_client(
        region_name=instance._region_name,
        session=instance.session,
        service_type='container',
        api_version=api_version,
    )
    return client


def build_option_parser(parser):
    """Hook to add global options"""
    parser.add_argument(
        '--os-container-api-version',
        metavar='<container-api-version>',
        default=utils.env(
            'OS_CONTAINER_API_VERSION',
            default=DEFAULT_CONTAINER_API_VERSION),
        action=ReplaceLatestVersion,
        choices=sorted(
            API_VERSIONS,
            key=lambda k: [int(x) for x in k.split('.')]) + ['latest'],
        help=("Container API version, default={0}"
              "(Env:OS_CONTAINER_API_VERSION)").format(
                  DEFAULT_CONTAINER_API_VERSION))
    return parser


class ReplaceLatestVersion(argparse.Action):
    """Replaces `latest` keyword by last known version."""

    def __call__(self, parser, namespace, values, option_string=None):
        latest = values == 'latest'
        if latest:
            values = '1.%d' % LAST_KNOWN_API_VERSION
        LOG.debug("Replacing 'latest' API version with the "
                  "latest known version '%s'", values)
        setattr(namespace, self.dest, values)
