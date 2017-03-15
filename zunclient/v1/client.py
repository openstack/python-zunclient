# Copyright 2014
# The Cloudscaling Group, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy
# of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from keystoneauth1 import loading
from keystoneauth1 import session as ksa_session
from oslo_utils import importutils

from zunclient.common import httpclient
from zunclient.v1 import containers
from zunclient.v1 import images
from zunclient.v1 import services

profiler = importutils.try_import("osprofiler.profiler")


class Client(object):
    def __init__(self, username=None, api_key=None, project_id=None,
                 project_name=None, auth_url=None, zun_url=None,
                 endpoint_type=None, endpoint_override=None,
                 service_type='container',
                 region_name=None, input_auth_token=None,
                 session=None, password=None, auth_type='password',
                 interface='public', service_name=None, insecure=False,
                 user_domain_id=None, user_domain_name=None,
                 project_domain_id=None, project_domain_name=None,
                 **kwargs):

        # We have to keep the api_key are for backwards compat, but let's
        # remove it from the rest of our code since it's not a keystone
        # concept
        if not password:
            password = api_key
        # Backwards compat for people assing in endpoint_type
        if endpoint_type:
            interface = endpoint_type

        # fix (yolanda): os-cloud-config is using endpoint_override
        # instead of zun_url
        if endpoint_override and not zun_url:
            zun_url = endpoint_override

        if zun_url and input_auth_token:
            auth_type = 'admin_token'
            session = None
            loader_kwargs = dict(
                token=input_auth_token,
                endpoint=zun_url)
        elif input_auth_token and not session:
            auth_type = 'token'
            loader_kwargs = dict(
                token=input_auth_token,
                auth_url=auth_url,
                project_id=project_id,
                project_name=project_name,
                user_domain_id=user_domain_id,
                user_domain_name=user_domain_name,
                project_domain_id=project_domain_id,
                project_domain_name=project_domain_name)
        else:
            loader_kwargs = dict(
                username=username,
                password=password,
                auth_url=auth_url,
                project_id=project_id,
                project_name=project_name,
                user_domain_id=user_domain_id,
                user_domain_name=user_domain_name,
                project_domain_id=project_domain_id,
                project_domain_name=project_domain_name)

        # Backwards compatibility for people not passing in Session
        if session is None:
            loader = loading.get_plugin_loader(auth_type)

            # This should be able to handle v2 and v3 Keystone Auth
            auth_plugin = loader.load_from_options(**loader_kwargs)
            session = ksa_session.Session(
                auth=auth_plugin, verify=(not insecure))

        client_kwargs = {}
        if zun_url:
            client_kwargs['endpoint_override'] = zun_url

        if not zun_url:
            try:
                # Trigger an auth error so that we can throw the exception
                # we always have
                session.get_endpoint(
                    service_type=service_type,
                    service_name=service_name,
                    interface=interface,
                    region_name=region_name)
            except Exception:
                raise RuntimeError("Not Authorized")

        self.http_client = httpclient.SessionClient(
            service_type=service_type,
            service_name=service_name,
            interface=interface,
            region_name=region_name,
            session=session,
            **client_kwargs)
        self.containers = containers.ContainerManager(self.http_client)
        self.images = images.ImageManager(self.http_client)
        self.services = services.ServiceManager(self.http_client)

        profile = kwargs.pop("profile", None)
        if profiler and profile:
            # Initialize the root of the future trace: the created trace ID
            # will be used as the very first parent to which all related
            # traces will be bound to. The given HMAC key must correspond to
            # the one set in zun-api zun.conf, otherwise the latter
            # will fail to check the request signature and will skip
            # initialization of osprofiler on the server side.
            profiler.init(profile)
