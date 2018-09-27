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

from zunclient.i18n import _


def _quota_columns(quota):
    return quota._info.keys()


def _get_client(obj, parsed_args):
    obj.log.debug("take_action(%s)" % parsed_args)
    return obj.app.client_manager.container


class UpdateQuota(command.ShowOne):
    """Update the quotas of the project"""

    log = logging.getLogger(__name__ + ".UpdateQuota")

    def get_parser(self, prog_name):
        parser = super(UpdateQuota, self).get_parser(prog_name)
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
        return parser

    def take_action(self, parsed_args):
        client = _get_client(self, parsed_args)
        opts = {}
        opts['containers'] = parsed_args.containers
        opts['memory'] = parsed_args.memory
        opts['cpu'] = parsed_args.cpu
        opts['disk'] = parsed_args.disk
        quota = client.quotas.update(**opts)
        columns = _quota_columns(quota)
        return columns, utils.get_item_properties(quota, columns)


class GetQuota(command.ShowOne):
    """Get quota of the project"""

    log = logging.getLogger(__name__ + '.GetQuota')

    def get_parser(self, prog_name):
        parser = super(GetQuota, self).get_parser(prog_name)
        parser.add_argument(
            '--usages',
            action='store_true',
            help='Whether show quota usage statistic or not')
        return parser

    def take_action(self, parsed_args):
        client = _get_client(self, parsed_args)
        quota = client.quotas.get(usages=parsed_args.usages)
        columns = _quota_columns(quota)
        return columns, utils.get_item_properties(quota, columns)


class GetDefaultQuota(command.ShowOne):
    """Get default quota of the project"""

    log = logging.getLogger(__name__ + '.GetDefeaultQuota')

    def take_action(self, parsed_args):
        client = _get_client(self, parsed_args)
        default_quota = client.quotas.defaults()
        columns = _quota_columns(default_quota)
        return columns, utils.get_item_properties(
            default_quota, columns)


class DeleteQuota(command.Command):
    """Delete quota of the project"""

    log = logging.getLogger(__name__ + '.DeleteQuota')

    def take_action(self, parsed_args):
        client = _get_client(self, parsed_args)
        try:
            client.quotas.delete()
            print(_('Request to delete quotas has been accepted.'))
        except Exception as e:
            print("Delete for quotas failed: %(e)s" % {'e': e})
