# Copyright 2010 Jacob Kaplan-Moss
# Copyright 2011 OpenStack Foundation
# Copyright 2012 Grid Dynamics
# Copyright 2013 OpenStack Foundation
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

import errno
import fcntl
import logging
import os
import select
import signal
import six
import socket
import struct
import sys
import termios
import time
import tty
import websocket

from zunclient.common.websocketclient import exceptions
from zunclient.v1 import client

LOG = logging.getLogger(__name__)

DEFAULT_API_VERSION = '1'
DEFAULT_ENDPOINT_TYPE = 'publicURL'
DEFAULT_SERVICE_TYPE = 'container'


class WebSocketClient(object):

    def __init__(self, host_url, id, escape='~',
                 close_wait=0.5):
        self.id = id
        self.escape = escape
        self.close_wait = close_wait
        self.host_url = host_url
        self.cs = None

    def init_httpclient(self):
        """Initialize the httpclient

        Websocket client need to call httpclient to send the resize
        command to Zun API server
        """
        os_username = os.environ.get('OS_USERNAME')
        os_password = os.environ.get('OS_PASSWORD')
        os_project_name = os.environ.get('OS_PROJECT_NAME')
        os_project_id = os.environ.get('OS_PROJECT_ID')
        os_user_domain_id = os.environ.get('OS_USER_DOMAIN_ID')
        os_user_domain_name = os.environ.get('OS_USER_DOMAIN_NAME')
        os_project_domain_id = os.environ.get('OS_PROJECT_DOMAIN_ID')
        os_project_domain_name = os.environ.get('OS_PROJECT_DOMAIN_NAME')
        os_auth_url = os.environ.get('OS_AUTH_URL')
        endpoint_type = os.environ.get('ENDPOINT_TYPE')
        service_type = os.environ.get('SERVICE_TYPE')
        os_region_name = os.environ.get('OS_REGION_NAME')
        bypass_url = os.environ.get('BYPASS_URL')
        insecure = os.environ.get('INSECURE')
        if not endpoint_type:
            endpoint_type = DEFAULT_ENDPOINT_TYPE

        if not service_type:
            service_type = DEFAULT_SERVICE_TYPE

        self.cs = client.Client(username=os_username,
                                api_key=os_password,
                                project_id=os_project_id,
                                project_name=os_project_name,
                                user_domain_id=os_user_domain_id,
                                user_domain_name=os_user_domain_name,
                                project_domain_id=os_project_domain_id,
                                project_domain_name=os_project_domain_name,
                                auth_url=os_auth_url,
                                service_type=service_type,
                                region_name=os_region_name,
                                zun_url=bypass_url,
                                endpoint_type=endpoint_type,
                                insecure=insecure)

    def connect(self):
        url = self.host_url
        LOG.debug('connecting to: %s', url)
        try:
            self.ws = websocket.create_connection(url,
                                                  skip_utf8_validation=True)
            print('connected to %s ,press Enter to continue' % self.id)
            print('type %s. to disconnect' % self.escape)
        except socket.error as e:
            raise exceptions.ConnectionFailed(e)
        except websocket.WebSocketConnectionClosedException as e:
            raise exceptions.ConnectionFailed(e)
        except websocket.WebSocketBadStatusException as e:
            raise exceptions.ConnectionFailed(e)

    def start_loop(self):
        self.poll = select.poll()
        self.poll.register(sys.stdin,
                           select.POLLIN | select.POLLHUP | select.POLLPRI)
        self.poll.register(self.ws,
                           select.POLLIN | select.POLLHUP | select.POLLPRI)

        self.start_of_line = False
        self.read_escape = False
        with WINCHHandler(self):
            try:
                self.setup_tty()
                self.run_forever()
            except socket.error as e:
                raise exceptions.ConnectionFailed(e)
            except websocket.WebSocketConnectionClosedException as e:
                raise exceptions.Disconnected(e)
            finally:
                self.restore_tty()

    def run_forever(self):
        LOG.debug('starting main loop in client')
        self.quit = False
        quitting = False
        when = None

        while True:
            try:
                for fd, event in self.poll.poll(500):
                    if fd == self.ws.fileno():
                        self.handle_websocket(event)
                    elif fd == sys.stdin.fileno():
                        self.handle_stdin(event)
            except select.error as e:
                # POSIX signals interrupt select()
                no = e.errno if six.PY3 else e[0]
                if no == errno.EINTR:
                    continue
                else:
                    raise e

            if self.quit and not quitting:
                self.log.debug('entering close_wait')
                quitting = True
                when = time.time() + self.close_wait

            if quitting and time.time() > when:
                self.log.debug('quitting')
                break

    def setup_tty(self):
        if os.isatty(sys.stdin.fileno()):
            LOG.debug('putting tty into raw mode')
            self.old_settings = termios.tcgetattr(sys.stdin)
            tty.setraw(sys.stdin)

    def restore_tty(self):
        if os.isatty(sys.stdin.fileno()):
            LOG.debug('restoring tty configuration')
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN,
                              self.old_settings)

    def handle_stdin(self, event):
        if event in (select.POLLHUP, select.POLLNVAL):
            LOG.debug('event %d on stdin', event)

            LOG.debug('eof on stdin')
            self.poll.unregister(sys.stdin)
            self.quit = True

        data = os.read(sys.stdin.fileno(), 1024)
        LOG.debug('read %s (%d bytes) from stdin', repr(data), len(data))

        if not data:
            return

        if self.start_of_line and data == self.escape:
            self.read_escape = True
            return

        if self.read_escape and data == '.':
            LOG.debug('exit by local escape code')
            raise exceptions.UserExit()
        elif self.read_escape:
            self.read_escape = False
            self.ws.send(self.escape)

        self.ws.send(data)

        if data == '\r':
            self.start_of_line = True
        else:
            self.start_of_line = False

    def handle_websocket(self, event):
        if event in (select.POLLHUP, select.POLLNVAL):
            LOG.debug('event %d on websocket', event)

            LOG.debug('eof on websocket')
            self.poll.unregister(self.ws)
            self.quit = True

        data = self.ws.recv()
        LOG.debug('read %s (%d bytes) from websocket from container',
                  repr(data), len(data))
        if not data:
            return

        sys.stdout.write(data)
        sys.stdout.flush()

    def handle_resize(self):
        """send the POST to resize the tty session size in container.

        Resize the container's PTY.
        If `size` is not None, it must be a tuple of (height,width), otherwise
        it will be determined by the size of the current TTY.
        """
        size = self.tty_size(sys.stdout)

        if size is not None:
            rows, cols = size
            try:
                self.tty_resize(height=rows, width=cols)
            except IOError:  # Container already exited
                pass

    def tty_size(self, fd):
        """Get the tty size

        Return a tuple (rows,cols) representing the size of the TTY `fd`.

        The provided file descriptor should be the stdout stream of the TTY.

        If the TTY size cannot be determined, returns None.
        """

        if not os.isatty(fd.fileno()):
            return None

        try:
            dims = struct.unpack('hh', fcntl.ioctl(fd,
                                                   termios.TIOCGWINSZ,
                                                   'hhhh'))
        except Exception:
            try:
                dims = (os.environ['LINES'], os.environ['COLUMNS'])
            except Exception:
                return None

        return dims

    def tty_resize(self, height, width):
        """Resize the tty session

            Get the client and send the tty size data to zun api server
            The environment variables need to get when implement sending
            operation.
        """
        height = str(height)
        width = str(width)

        self.cs.containers.resize(self.id, width, height)


class WINCHHandler(object):
    """WINCH Signal handler

    WINCH Signal handler to keep the PTY correctly sized.
    """

    def __init__(self, client):
        """Initialize a new WINCH handler for the given PTY.

        Initializing a handler has no immediate side-effects. The `start()`
        method must be invoked for the signals to be trapped.
        """

        self.client = client
        self.original_handler = None

    def __enter__(self):
        """Enter

        Invoked on entering a `with` block.
        """

        self.start()
        return self

    def __exit__(self, *_):
        """Exit

        Invoked on exiting a `with` block.
        """

        self.stop()

    def start(self):
        """Start

        Start trapping WINCH signals and resizing the PTY.
        This method saves the previous WINCH handler so it can be restored on
        `stop()`.
        """

        def handle(signum, frame):
            if signum == signal.SIGWINCH:
                LOG.debug("Send command to resize the tty session")
                self.client.handle_resize()

        self.original_handler = signal.signal(signal.SIGWINCH, handle)

    def stop(self):
        """stop

        Stop trapping WINCH signals and restore the previous WINCH handler.
        """

        if self.original_handler is not None:
            signal.signal(signal.SIGWINCH, self.original_handler)
