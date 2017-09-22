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


class ContainerWebSocketException(Exception):
    """base for all ContainerWebSocket interactive generated exceptions"""
    def __init__(self, wrapped=None, message=None):
        self.wrapped = wrapped
        if message:
            self.message = message
        if wrapped:
            formatted_string = "%s:%s" % (self.message, str(self.wrapped))
        else:
            formatted_string = "%s" % self.message
        super(ContainerWebSocketException, self).__init__(formatted_string)


class UserExit(ContainerWebSocketException):
    message = "User requested disconnect the container"


class Disconnected(ContainerWebSocketException):
    message = "Remote host closed connection"


class ConnectionFailed(ContainerWebSocketException):
    message = "Failed to connect to remote host"


class InvalidWebSocketLink(ContainerWebSocketException):
    message = "Invalid websocket link when attach container"


class ContainerFailtoStart(ContainerWebSocketException):
    message = "Container fail to start"


class ContainerStateError(ContainerWebSocketException):
    message = "Container state is error, can not attach container"
