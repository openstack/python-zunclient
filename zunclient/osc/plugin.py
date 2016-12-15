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

import logging

from osc_lib import utils

LOG = logging.getLogger(__name__)

DEFAULT_CONTAINER_API_VERSION = "1"
API_VERSION_OPTION = "os_container_api_version"
API_NAME = "container"
API_VERSIONS = {
    '1': 'zunclient.v1.client.Client',
}


def make_client(instance):
    """Returns a zun service client"""
    zun_client = utils.get_client_class(
        API_NAME,
        instance._api_version[API_NAME],
        API_VERSIONS)
    LOG.debug("Instantiating zun client: {0}".format(
              zun_client))

    client = zun_client(
        region_name=instance._region_name,
        session=instance.session,
        service_type='container',
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
        help=("Container API version, default={0}"
              "(Env:OS_CONTAINER_API_VERSION)").format(
                  DEFAULT_CONTAINER_API_VERSION))
    return parser
