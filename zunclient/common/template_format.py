#    Copyright 2017 Arm Limited.
#
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

import yaml

from oslo_serialization import jsonutils


if hasattr(yaml, 'CSafeDumper'):
    yaml_dumper_base = yaml.CSafeDumper
else:
    yaml_dumper_base = yaml.SafeDumper


# We create custom class to not overriden the default yaml behavior
class yaml_loader(yaml.SafeLoader):
    pass


class yaml_dumper(yaml_dumper_base):
    pass


def _construct_yaml_str(self, node):
    # Override the default string handling function
    # to always return unicode objects
    return self.construct_scalar(node)
yaml_loader.add_constructor(u'tag:yaml.org,2002:str', _construct_yaml_str)
# Unquoted dates like 2013-05-23 in yaml files get loaded as objects of type
# datetime.data which causes problems in API layer when being processed by
# openstack.common.jsonutils. Therefore, make unicode string out of timestamps
# until jsonutils can handle dates.
yaml_loader.add_constructor(u'tag:yaml.org,2002:timestamp',
                            _construct_yaml_str)


def parse(tmpl_str):
    """Takes a string and returns a dict containing the parsed structure.

    This includes determination of whether the string is using the
    JSON or YAML format.
    """
    # strip any whitespace before the check
    tmpl_str = tmpl_str.strip()
    if tmpl_str.startswith('{'):
        tpl = jsonutils.loads(tmpl_str)
    else:
        try:
            tpl = yaml.safe_load(tmpl_str)
        except yaml.YAMLError as yea:
            raise ValueError(yea)
        else:
            if tpl is None:
                tpl = {}

    return tpl
