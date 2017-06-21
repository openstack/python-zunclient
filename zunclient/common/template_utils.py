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

from oslo_serialization import jsonutils
import six
from six.moves.urllib import parse
from six.moves.urllib import request

from zunclient.common import template_format
from zunclient.common import utils
from zunclient import exceptions
from zunclient.i18n import _


def get_template_contents(template_file=None, template_url=None,
                          files=None):

    # Transform a bare file path to a file:// URL.
    if template_file:  # nosec
        template_url = utils.normalise_file_path_to_url(template_file)
        tpl = request.urlopen(template_url).read()
    else:
        raise exceptions.CommandErrorException(_('Need to specify exactly '
                                                 'one of %(arg1)s, %(arg2)s '
                                                 'or %(arg3)s') %
                                               {'arg1': '--template-file',
                                                'arg2': '--template-url'})

    if not tpl:
        raise exceptions.CommandErrorException(_('Could not fetch '
                                                 'template from %s') %
                                               template_url)

    try:
        if isinstance(tpl, six.binary_type):
            tpl = tpl.decode('utf-8')
        template = template_format.parse(tpl)
    except ValueError as e:
        raise exceptions.CommandErrorException(_('Error parsing template '
                                                 '%(url)s %(error)s') %
                                               {'url': template_url,
                                                'error': e})
    return template


def is_template(file_content):
    try:
        if isinstance(file_content, six.binary_type):
            file_content = file_content.decode('utf-8')
        template_format.parse(file_content)
    except (ValueError, TypeError):
        return False
    return True


def get_file_contents(from_data, files, base_url=None,
                      ignore_if=None):

    if isinstance(from_data, dict):
        for key, value in from_data.items():
            if ignore_if and ignore_if(key, value):
                continue

            if base_url and not base_url.endswith('/'):
                base_url = base_url + '/'

            str_url = parse.urljoin(base_url, value)
            if str_url not in files:
                file_content = utils.read_url_content(str_url)
                if is_template(file_content):
                    template = get_template_contents(
                        template_url=str_url, files=files)[1]
                    file_content = jsonutils.dumps(template)
                files[str_url] = file_content
            # replace the data value with the normalised absolute URL
            from_data[key] = str_url
