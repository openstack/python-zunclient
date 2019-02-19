# Copyright 2014
# The Cloudscaling Group, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy
# of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from zunclient.v1 import actions_shell
from zunclient.v1 import availability_zones_shell
from zunclient.v1 import capsules_shell
from zunclient.v1 import containers_shell
from zunclient.v1 import hosts_shell
from zunclient.v1 import images_shell
from zunclient.v1 import quota_classes_shell
from zunclient.v1 import quotas_shell
from zunclient.v1 import registries_shell
from zunclient.v1 import services_shell
from zunclient.v1 import versions_shell

COMMAND_MODULES = [
    availability_zones_shell,
    containers_shell,
    images_shell,
    services_shell,
    hosts_shell,
    versions_shell,
    capsules_shell,
    actions_shell,
    quotas_shell,
    quota_classes_shell,
    registries_shell,
]
