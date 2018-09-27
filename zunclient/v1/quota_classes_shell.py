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

from zunclient.common import cliutils as utils


@utils.arg(
    '--containers',
    metavar='<containers>',
    type=int,
    help='The number of containers allowed per project')
@utils.arg(
    '--cpu',
    metavar='<cpu>',
    type=int,
    help='The number of container cores or vCPUs allowed per project')
@utils.arg(
    '--memory',
    metavar='<memory>',
    type=int,
    help='The number of megabytes of container RAM allowed per project')
@utils.arg(
    '--disk',
    metavar='<disk>',
    type=int,
    help='The number of gigabytes of container Disk allowed per project')
@utils.arg(
    'quota_class_name',
    metavar='<quota_class_name>',
    help='The name of quota class')
def do_quota_class_update(cs, args):
    """Print an updated quotas for a quota class"""
    utils.print_dict(cs.quota_classes.update(
        args.quota_class_name,
        containers=args.containers,
        memory=args.memory,
        cpu=args.cpu,
        disk=args.disk)._info)


@utils.arg(
    'quota_class_name',
    metavar='<quota_class_name>',
    help='The name of quota class')
def do_quota_class_get(cs, args):
    """Print a quotas for a quota class"""
    utils.print_dict(cs.quota_classes.get(args.quota_class_name)._info)
