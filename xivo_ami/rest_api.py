# -*- coding: utf-8 -*-
# Copyright 2016-2017 The Wazo Authors  (see the AUTHORS file)
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
import marshmallow
import os

from cheroot import wsgi
from datetime import timedelta
from flask import Flask
from flask_cors import CORS
from flask_restful import Api
from flask_restful import Resource
from functools import wraps
from werkzeug.contrib.fixers import ProxyFix
from xivo import http_helpers
from xivo import rest_api_helpers
from xivo.http_helpers import ReverseProxied
from xivo.auth_verifier import AuthVerifier
from xivo.auth_verifier import required_acl as required_acl_

from .exceptions import ValidationError

VERSION = 1.0

app = Flask('xivo_amid')
logger = logging.getLogger(__name__)
api = Api(prefix='/{}'.format(VERSION))
auth_verifier = AuthVerifier()
required_acl = required_acl_


def configure(global_config):

    http_helpers.add_logger(app, logger)
    app.after_request(http_helpers.log_request)
    app.secret_key = os.urandom(24)
    app.permanent_session_lifetime = timedelta(minutes=5)

    cors_config = dict(global_config['rest_api']['cors'])
    enabled = cors_config.pop('enabled', False)
    if enabled:
        CORS(app, **cors_config)

    load_resources(global_config)
    api.init_app(app)

    auth_verifier.set_config(global_config['auth'])


def load_resources(global_config):
    from xivo_ami.resources.action.actions import Actions
    from xivo_ami.resources.action.actions import Command
    from xivo_ami.resources.api.actions import SwaggerResource

    Actions.configure(global_config)
    Command.configure(global_config)
    api.add_resource(Actions, '/action/<action>')
    api.add_resource(Command, '/action/Command')

    SwaggerResource.add_resource(api)


def run(config):
    https_config = config['https']
    bind_addr = (https_config['listen'], https_config['port'])

    wsgi_app = ReverseProxied(ProxyFix(wsgi.WSGIPathInfoDispatcher({'/': app})))
    server = wsgi.WSGIServer(bind_addr=bind_addr, wsgi_app=wsgi_app)
    server.ssl_adapter = http_helpers.ssl_adapter(https_config['certificate'],
                                                  https_config['private_key'])

    logger.debug('WSGIServer starting... uid: %s, listen: %s:%s', os.getuid(), bind_addr[0], bind_addr[1])
    for route in http_helpers.list_routes(app):
        logger.debug(route)

    try:
        server.start()
    except KeyboardInterrupt:
        server.stop()


def handle_validation_exception(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except marshmallow.ValidationError as e:
            raise ValidationError(e.messages)
    return wrapper


class ErrorCatchingResource(Resource):
    method_decorators = [handle_validation_exception, rest_api_helpers.handle_api_exception] + Resource.method_decorators


class AuthResource(ErrorCatchingResource):
    method_decorators = [auth_verifier.verify_token] + ErrorCatchingResource.method_decorators