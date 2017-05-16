# Copyright 2015 OpenStack LLC.
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

import mock
import testtools

from zunclient.common.websocketclient import websocketclient

CONTAINER_ID = "0f96db5a-26dc-4550-b1a8-b110bd9247cb"
ESCAPE_FLAG = "~"
URL = "ws://localhost:2375/v1.17/containers/201e4e22c5b2/" \
      "attach/ws?logs=0&stream=1&stdin=1&stdout=1&stderr=1"
URL1 = "ws://10.10.10.10:2375/v1.17/containers/***********/" \
       "attach/ws?logs=0&stream=1&stdin=1&stdout=1&stderr=1"
WAIT_TIME = 0.5


class WebSocketClientTest(testtools.TestCase):

    def test_websocketclient_variables(self):
        mock_client = mock.Mock()
        wsclient = websocketclient.WebSocketClient(zunclient=mock_client,
                                                   url=URL,
                                                   id=CONTAINER_ID,
                                                   escape=ESCAPE_FLAG,
                                                   close_wait=WAIT_TIME)
        self.assertEqual(wsclient.url, URL)
        self.assertEqual(wsclient.id, CONTAINER_ID)
        self.assertEqual(wsclient.escape, ESCAPE_FLAG)
        self.assertEqual(wsclient.close_wait, WAIT_TIME)
