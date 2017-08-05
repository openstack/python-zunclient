# Copyright 2013 OpenStack Foundation
# Copyright 2013 Spanish National Research Council.
# All Rights Reserved.
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

# E0202: An attribute inherited from %s hide this method
# pylint: disable=E0202

import abc
import argparse
import os
import six

from zunclient.common.apiclient import exceptions


_discovered_plugins = {}


def load_auth_system_opts(parser):
    """Load options needed by the available auth-systems into a parser.

    This function will try to populate the parser with options from the
    available plugins.
    """
    group = parser.add_argument_group("Common auth options")
    BaseAuthPlugin.add_common_opts(group)
    for name, auth_plugin in _discovered_plugins.items():
        group = parser.add_argument_group(
            "Auth-system '%s' options" % name,
            conflict_handler="resolve")
        auth_plugin.add_opts(group)


def load_plugin(auth_system):
    try:
        plugin_class = _discovered_plugins[auth_system]
    except KeyError:
        raise exceptions.AuthSystemNotFound(auth_system)
    return plugin_class(auth_system=auth_system)


@six.add_metaclass(abc.ABCMeta)
class BaseAuthPlugin(object):
    """Base class for authentication plugins.

    An authentication plugin needs to override at least the authenticate
    method to be a valid plugin.
    """

    auth_system = None
    opt_names = []
    common_opt_names = [
        "auth_system",
        "username",
        "password",
        "auth_url",
    ]

    def __init__(self, auth_system=None, **kwargs):
        self.auth_system = auth_system or self.auth_system
        self.opts = dict((name, kwargs.get(name))
                         for name in self.opt_names)

    @staticmethod
    def _parser_add_opt(parser, opt):
        """Add an option to parser in two variants.

        :param opt: option name (with underscores)
        """
        dashed_opt = opt.replace("_", "-")
        env_var = "OS_%s" % opt.upper()
        arg_default = os.environ.get(env_var, "")
        arg_help = "Defaults to env[%s]." % env_var
        parser.add_argument(
            "--os-%s" % dashed_opt,
            metavar="<%s>" % dashed_opt,
            default=arg_default,
            help=arg_help)
        parser.add_argument(
            "--os_%s" % opt,
            metavar="<%s>" % dashed_opt,
            help=argparse.SUPPRESS)

    @classmethod
    def add_opts(cls, parser):
        """Populate the parser with the options for this plugin."""
        for opt in cls.opt_names:
            # use `BaseAuthPlugin.common_opt_names` since it is never
            # changed in child classes
            if opt not in BaseAuthPlugin.common_opt_names:
                cls._parser_add_opt(parser, opt)

    @classmethod
    def add_common_opts(cls, parser):
        """Add options that are common for several plugins."""
        for opt in cls.common_opt_names:
            cls._parser_add_opt(parser, opt)

    @staticmethod
    def get_opt(opt_name, args):
        """Return option name and value.

        :param opt_name: name of the option, e.g., "username"
        :param args: parsed arguments
        """
        return (opt_name, getattr(args, "os_%s" % opt_name, None))

    def parse_opts(self, args):
        """Parse the actual auth-system options if any.

        This method is expected to populate the attribute `self.opts` with a
        dict containing the options and values needed to make authentication.
        """
        self.opts.update(dict(self.get_opt(opt_name, args)
                              for opt_name in self.opt_names))

    def authenticate(self, http_client):
        """Authenticate using plugin defined method.

        The method usually analyses `self.opts` and performs
        a request to authentication server.

        :param http_client: client object that needs authentication
        :type http_client: HTTPClient
        :raises: AuthorizationFailure
        """
        self.sufficient_options()
        self._do_authenticate(http_client)

    @abc.abstractmethod
    def _do_authenticate(self, http_client):
        """Protected method for authentication."""

    def sufficient_options(self):
        """Check if all required options are present.

        :raises: AuthPluginOptionsMissing
        """
        missing = [opt
                   for opt in self.opt_names
                   if not self.opts.get(opt)]
        if missing:
            raise exceptions.AuthPluginOptionsMissing(missing)
