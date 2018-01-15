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

from zunclient import api_versions
from zunclient.common import cliutils as utils


def do_version_list(cs, args):
    """List all API versions."""
    print("Client supported API versions:")
    print("Minimum version %(v)s" %
          {'v': api_versions.MIN_API_VERSION})
    print("Maximum version %(v)s" %
          {'v': api_versions.MAX_API_VERSION})

    print("\nServer supported API versions:")
    result = cs.versions.list()
    columns = ["Id", "Status", "Min Version", "Max Version"]
    utils.print_list(result, columns)
