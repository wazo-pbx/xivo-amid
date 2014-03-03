# -*- coding: utf-8 -*-

# Copyright (C) 2012-2013 Avencall
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>

from hamcrest import assert_that, equal_to
from mock import Mock
import unittest

from xivo_ami.ami.client import Message
from xivo_ami.bus.client import BusClient, BusConnectionError
from xivo_bus.ctl.client import BusCtlClient


class TestBusClient(unittest.TestCase):

    def setUp(self):
        self.mock_bus_ctl_client = Mock(BusCtlClient, connected=False)
        self.bus_client = BusClient(self.mock_bus_ctl_client)

    def test_when_connect_then_connect_and_declare(self):
        self.bus_client.connect()

        self.mock_bus_ctl_client.connect.assert_called_once_with()
        self.mock_bus_ctl_client.declare_exchange.assert_called_once_with('xivo-ami', 'topic', durable=True)

    def test_given_amqperror_when_connect_then_raise_busconnectionerror(self):
        self.mock_bus_ctl_client.connect.side_effect = IOError()

        self.assertRaises(BusConnectionError, self.bus_client.connect)

    def test_given_connected_when_connect_then_nothing(self):
        self.mock_bus_ctl_client.connected = True
        self.bus_client.connect()

        assert_that(self.mock_bus_ctl_client.connect.call_count, equal_to(0))
        assert_that(self.mock_bus_ctl_client.declare_exchange.call_count, equal_to(0))

    def test_when_disconnect_then_close(self):
        self.bus_client.disconnect()

        self.mock_bus_ctl_client.close.assert_called_once_with()

    def test_when_publish_then_publish_event(self):
        name = 'EventName'
        headers = {'foo': 'bar', 'meaning of the universe': '42'}
        message = Message(name, headers)

        self.bus_client.publish(message)

        assert_that(self.mock_bus_ctl_client.publish_event.call_count, equal_to(1))
        resulting_args = self.mock_bus_ctl_client.publish_event.call_args[0]
        resulting_exchange, resulting_key, resulting_event = resulting_args
        assert_that(resulting_event.name, equal_to(name))
        assert_that(resulting_event.variables, equal_to(headers))
        assert_that(resulting_exchange, equal_to('xivo-ami'))
        assert_that(resulting_key, equal_to(resulting_event.name))

    def test_given_amqperror_when_publish_then_raise_busconnectionerror(self):
        name = 'EventName'
        headers = {'foo': 'bar', 'meaning of the universe': '42'}
        message = Message(name, headers)
        self.mock_bus_ctl_client.publish_event.side_effect = IOError()

        self.assertRaises(BusConnectionError, self.bus_client.publish, message)