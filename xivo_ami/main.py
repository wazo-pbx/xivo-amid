# -*- coding: utf-8 -*-

# Copyright (C) 2012-2015 Avencall
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

import logging
import signal
import thread

from xivo.daemonize import pidfile_context
from xivo.user_rights import change_user
from xivo.xivo_logging import setup_logging
from xivo_ami import rest_api
from xivo_ami.ami.client import AMIClient
from xivo_ami.bus.client import BusClient
from xivo_ami.config import load_config
from xivo_ami.facade import EventHandlerFacade

logger = logging.getLogger(__name__)


def main():
    config = load_config()

    setup_logging(config['logfile'], config['foreground'], config['debug'])
    if config.get('user'):
        change_user(config['user'])

    with pidfile_context(config['pidfile'], config['foreground']):
        _run(config)


def _run(config):
    _init_signal()
    if config['publish_ami_events']:
        ami_client = AMIClient(**config['ami'])
        bus_client = BusClient(config)
        facade = EventHandlerFacade(ami_client, bus_client)
        thread.start_new_thread(facade.run, ())

    rest_api.configure_routes(config)
    rest_api.run(config['rest_api'])


def _init_signal():
    signal.signal(signal.SIGTERM, _handle_sigterm)


def _handle_sigterm(signum, frame):
    raise SystemExit()


if __name__ == '__main__':
    main()
