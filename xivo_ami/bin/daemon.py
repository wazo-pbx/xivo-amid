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

from xivo.daemonize import pidfile_context
from xivo.user_rights import change_user
from xivo.xivo_logging import setup_logging
from xivo_ami.config import load_config
from xivo_ami.controller import Controller

logger = logging.getLogger(__name__)


def main():
    config = load_config()

    setup_logging(config['logfile'], config['foreground'], config['debug'])

    if config.get('user'):
        change_user(config['user'])

    controller = Controller(config)

    with pidfile_context(config['pidfile'], config['foreground']):
        controller.run()


if __name__ == '__main__':
    main()
