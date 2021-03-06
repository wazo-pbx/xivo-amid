# Copyright 2016-2020 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

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

from .exceptions import ValidationError

VERSION = 1.0

app = Flask('wazo_amid')
logger = logging.getLogger(__name__)
api = Api(prefix='/{}'.format(VERSION))
auth_verifier = AuthVerifier()
wsgi_server = None


def configure(global_config):

    http_helpers.add_logger(app, logger)
    app.after_request(http_helpers.log_request)
    app.config.update(global_config)
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
    from wazo_amid.resources.action.actions import Actions
    from wazo_amid.resources.action.actions import Command
    from wazo_amid.resources.api.actions import SwaggerResource

    Actions.configure(global_config)
    Command.configure(global_config)
    api.add_resource(Actions, '/action/<action>')
    api.add_resource(Command, '/action/Command')

    SwaggerResource.add_resource(api)


def run(config):
    bind_addr = (config['listen'], config['port'])

    wsgi_app = ReverseProxied(ProxyFix(wsgi.WSGIPathInfoDispatcher({'/': app})))
    global wsgi_server
    wsgi_server = wsgi.WSGIServer(bind_addr=bind_addr, wsgi_app=wsgi_app)
    if config['certificate'] and config['private_key']:
        logger.warning(
            'Using service SSL configuration is deprecated. Please use NGINX instead.'
        )
        wsgi_server.ssl_adapter = http_helpers.ssl_adapter(
            config['certificate'], config['private_key']
        )

    logger.debug(
        'WSGIServer starting... uid: %s, listen: %s:%s',
        os.getuid(),
        bind_addr[0],
        bind_addr[1],
    )
    for route in http_helpers.list_routes(app):
        logger.debug(route)

    try:
        wsgi_server.start()
    except KeyboardInterrupt:
        wsgi_server.stop()


def stop():
    if wsgi_server:
        wsgi_server.stop()


def handle_validation_exception(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except marshmallow.ValidationError as e:
            raise ValidationError(e.messages)

    return wrapper


class ErrorCatchingResource(Resource):
    method_decorators = [
        handle_validation_exception,
        rest_api_helpers.handle_api_exception,
    ] + Resource.method_decorators


class AuthResource(ErrorCatchingResource):
    method_decorators = [
        auth_verifier.verify_tenant,
        auth_verifier.verify_token,
    ] + ErrorCatchingResource.method_decorators
