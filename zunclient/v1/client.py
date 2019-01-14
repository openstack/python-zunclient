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

from zunclient.common import httpclient
from zunclient.v1 import actions
from zunclient.v1 import availability_zones as az
from zunclient.v1 import capsules
from zunclient.v1 import containers
from zunclient.v1 import hosts
from zunclient.v1 import images
from zunclient.v1 import quota_classes
from zunclient.v1 import quotas
from zunclient.v1 import registries
from zunclient.v1 import services
from zunclient.v1 import versions


class Client(object):
    """Top-level object to access the OpenStack Container API."""

    def __init__(self, api_version=None, auth_token=None,
                 auth_type='password', auth_url=None, endpoint_override=None,
                 interface='public', insecure=False, password=None,
                 project_domain_id=None, project_domain_name=None,
                 project_id=None, project_name=None, region_name=None,
                 service_name=None, service_type='container', session=None,
                 user_domain_id=None, user_domain_name=None,
                 username=None, cacert=None, cert=None, key=None, **kwargs):
        """Initialization of Client object.

        :param api_version: Container API version
        :type api_version: zunclient.api_version.APIVersion
        :param str auth_token: Auth token
        :param str auth_url: Auth URL
        :param str auth_type: Auth Type
        :param str endpoint_override: Bypass URL
        :param str interface: Interface
        :param str insecure: Allow insecure
        :param str password: User password
        :param str project_domain_id: ID of project domain
        :param str project_domain_name: Nam of project domain
        :param str project_id: Project/Tenant ID
        :param str project_name: Project/Tenant Name
        :param str region_name: Region Name
        :param str service_name: Service Name
        :param str service_type: Service Type
        :param str session: Session
        :param str user_domain_id: ID of user domain
        :param str user_id: User ID
        :param str username: Username
        :param str cacert: CA certificate
        """
        if endpoint_override and auth_token:
            auth_type = 'admin_token'
            session = None
            loader_kwargs = {
                'token': auth_token,
                'endpoint': endpoint_override
            }
        elif auth_token and not session:
            auth_type = 'token'
            loader_kwargs = {
                'token': auth_token,
                'auth_url': auth_url,
                'project_domain_id': project_domain_id,
                'project_domain_name': project_domain_name,
                'project_id': project_id,
                'project_name': project_name,
                'user_domain_id': user_domain_id,
                'user_domain_name': user_domain_name
            }
        else:
            loader_kwargs = {
                'auth_url': auth_url,
                'password': password,
                'project_domain_id': project_domain_id,
                'project_domain_name': project_domain_name,
                'project_id': project_id,
                'project_name': project_name,
                'user_domain_id': user_domain_id,
                'user_domain_name': user_domain_name,
                'username': username,
            }

        # Backwards compatibility for people not passing in Session
        if session is None:
            loader = loading.get_plugin_loader(auth_type)
            # This should be able to handle v2 and v3 Keystone Auth
            auth_plugin = loader.load_from_options(**loader_kwargs)
            if cert and key:
                cert = cert, key
            session = ksa_session.Session(auth=auth_plugin,
                                          verify=(cacert or not insecure),
                                          cert=cert)
        client_kwargs = {}
        if not endpoint_override:
            try:
                # Trigger an auth error so that we can throw the exception
                # we always have
                session.get_endpoint(
                    service_name=service_name,
                    service_type=service_type,
                    interface=interface,
                    region_name=region_name
                )
            except Exception:
                raise RuntimeError('Not authorized')
        else:
            client_kwargs = {'endpoint_override': endpoint_override}

        self.http_client = httpclient.SessionClient(service_type=service_type,
                                                    service_name=service_name,
                                                    interface=interface,
                                                    region_name=region_name,
                                                    session=session,
                                                    api_version=api_version,
                                                    **client_kwargs)
        self.containers = containers.ContainerManager(self.http_client)
        self.images = images.ImageManager(self.http_client)
        self.services = services.ServiceManager(self.http_client)
        self.hosts = hosts.HostManager(self.http_client)
        self.versions = versions.VersionManager(self.http_client)
        self.capsules = capsules.CapsuleManager(self.http_client)
        self.availability_zones = az.AvailabilityZoneManager(self.http_client)
        self.actions = actions.ActionManager(self.http_client)
        self.quotas = quotas.QuotaManager(self.http_client)
        self.quota_classes = quota_classes.QuotaClassManager(self.http_client)
        self.registries = registries.RegistryManager(self.http_client)

    @property
    def api_version(self):
        return self.http_client.api_version
