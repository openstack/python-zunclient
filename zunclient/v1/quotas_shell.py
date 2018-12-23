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
    'project_id',
    metavar='<project_id>',
    help='The UUID of project in a multi-project cloud')
def do_quota_update(cs, args):
    """Print an updated quotas for a project"""
    utils.print_dict(cs.quotas.update(args.project_id,
                                      containers=args.containers,
                                      memory=args.memory,
                                      cpu=args.cpu,
                                      disk=args.disk)._info)


@utils.arg(
    '--usages',
    default=False,
    action='store_true',
    help='Whether show quota usage statistic or not')
@utils.arg(
    'project_id',
    metavar='<project_id>',
    help='The UUID of project in a multi-project cloud')
def do_quota_get(cs, args):
    """Print a quotas for a project with usages (optional)"""
    if args.usages:
        utils.print_dict(
            cs.quotas.get(args.project_id, usages=args.usages)._info,
            value_fields=('limit', 'in_use'))
    else:
        utils.print_dict(
            cs.quotas.get(args.project_id, usages=args.usages)._info)


@utils.arg(
    'project_id',
    metavar='<project_id>',
    help='The UUID of project in a multi-project cloud')
def do_quota_defaults(cs, args):
    """Print a  default quotas for a project"""
    utils.print_dict(cs.quotas.defaults(args.project_id)._info)


@utils.arg(
    'project_id',
    metavar='<project_id>',
    help='The UUID of project in a multi-project cloud')
def do_quota_delete(cs, args):
    """Delete quotas for a project"""
    cs.quotas.delete(args.project_id)
