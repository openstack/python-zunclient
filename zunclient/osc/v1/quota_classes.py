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

from osc_lib.command import command
from osc_lib import utils
from oslo_log import log as logging


def _quota_class_columns(quota_class):
    return quota_class._info.keys()


def _get_client(obj, parsed_args):
    obj.log.debug("take_action(%s)" % parsed_args)
    return obj.app.client_manager.container


class UpdateQuotaClass(command.ShowOne):
    """Update the quotas for a quota class"""

    log = logging.getLogger(__name__ + ".UpdateQuotaClass")

    def get_parser(self, prog_name):
        parser = super(UpdateQuotaClass, self).get_parser(prog_name)
        parser.add_argument(
            '--containers',
            metavar='<containers>',
            help='The number of containers allowed per project')
        parser.add_argument(
            '--memory',
            metavar='<memory>',
            help='The number of megabytes of container RAM '
                 'allowed per project')
        parser.add_argument(
            '--cpu',
            metavar='<cpu>',
            help='The number of container cores or vCPUs '
                 'allowed per project')
        parser.add_argument(
            '--disk',
            metavar='<disk>',
            help='The number of gigabytes of container Disk '
                 'allowed per project')
        parser.add_argument(
            'quota_class_name',
            metavar='<quota_class_name>',
            help='The name of quota class')
        return parser

    def take_action(self, parsed_args):
        client = _get_client(self, parsed_args)
        opts = {}
        opts['containers'] = parsed_args.containers
        opts['memory'] = parsed_args.memory
        opts['cpu'] = parsed_args.cpu
        opts['disk'] = parsed_args.disk
        quota_class_name = parsed_args.quota_class_name
        quota_class = client.quota_classes.update(
            quota_class_name, **opts)
        columns = _quota_class_columns(quota_class)
        return columns, utils.get_item_properties(quota_class, columns)


class GetQuotaClass(command.ShowOne):
    """List the quotas for a quota class"""

    log = logging.getLogger(__name__ + '.GetQuotaClass')

    def get_parser(self, prog_name):
        parser = super(GetQuotaClass, self).get_parser(prog_name)
        parser.add_argument(
            'quota_class_name',
            metavar='<quota_class_name>',
            help='The name of quota class')
        return parser

    def take_action(self, parsed_args):
        client = _get_client(self, parsed_args)
        quota_class_name = parsed_args.quota_class_name
        quota_class = client.quota_classes.get(quota_class_name)
        columns = _quota_class_columns(quota_class)
        return columns, utils.get_item_properties(quota_class, columns)
