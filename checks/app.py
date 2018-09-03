# -*- coding:utf-8 -*-

import os
import logging

import tornado.web
import tornado.ioloop
import tornado.options
import tornado.httpserver
import tornado.gen

from motor import MotorClient

from ServiceDiscovery.discovery import ServiceDiscovery, Service
from signal import signal, SIGINT, SIGTERM, SIGQUIT

from checks.config import make_config

from checks.controllers import CheckHandler, NotFoundHandler
from checks.controllers import BulkHandler, CsvBulkHandler
from checks.controllers import GroupChecksHandler, CheckExecHandler
from checks.controllers import GroupChecksExecController

from ServiceDiscovery.controllers import HealthHandler

log = logging.getLogger(__name__)


def build_routes():
    routes = []
    routes.extend(GroupChecksExecController.routes())
    routes.extend(CheckExecHandler.routes())
    routes.extend(CheckHandler.routes())
    routes.extend(GroupChecksHandler.routes())
    routes.extend(CsvBulkHandler.routes())
    routes.extend(BulkHandler.routes())
    routes.extend(HealthHandler.routes())

    return routes


def get_app():
    """Factory for tornado.web.Application"""
    config = make_config()
    settings = {
        "cookie_secret": os.environ.get('SECRET') or 'secret',
        "xsrf_cookies": False,
        "debug": config.getboolean('WebServer', 'debug'),
        'default_handler_class': NotFoundHandler
    }

    app = tornado.web.Application(build_routes(), **settings)
    app.config = config

    mongodb_host = app.config.get('MongoDB', 'host')
    mongodb_port = app.config.get('MongoDB', 'port')
    app.db = MotorClient('mongodb://%s:%s' % (mongodb_host, mongodb_port))
    app.sd = ServiceDiscovery(endpoint=config.get('ServiceDiscovery', 'sd'))
    return app


def on_shutdown(app):
    """shutdown callback"""
    log.info("Shutdown started")
    if app.service.registered:
        try:
            app.sd.unregister(app.service)
        except Exception as e:
            log.error("Cannot de-register on Consul: %s", str(e))

    app.db.close()
    tornado.ioloop.IOLoop.instance().stop()
    log.info("Shutdown completed")


def build_ssl_options(config):
    ssl_options = {
        "certfile": config.get('WebServer', 'servercert'),
        "keyfile": config.get('WebServer', 'serverkey')
    }

    if os.path.isfile(ssl_options['certfile']) and \
       os.path.isfile(ssl_options['keyfile']):
        return ssl_options
    else:
        return None

    return ssl_options


def startWebServer():
    app = get_app()
    server = tornado.httpserver.HTTPServer(app)

    protocol = app.config.get('WebServer', 'protocol')
    addr = app.config.get('WebServer', 'address')
    port = app.config.getint('WebServer', 'port')
    service_name = app.config.get('WebServer', 'servicename')

    ssl_options = build_ssl_options(app.config)
    if ssl_options is None:
        protocol = "http"
        log.warning("Server should be always on HTTPS!")
    else:
        protocol = "https"
        log.info("Good body, you have HTTPS configured")

    app.config.set('WebServer', 'protocol', protocol)

    server = tornado.httpserver.HTTPServer(app, ssl_options=ssl_options)

    while True:
        try:
            log.info('try port %s', port)
            server.bind(port)
            log.info("%s at %s://%s:%s", service_name, protocol, addr, port)
            app.config.set('WebServer', 'port', str(port))
            break
        except Exception as e:
            log.info('port %s already used (%s) ... ', str(port), str(e))
            port += 1

    app.service = Service(service_name, addr, port)
    try:
        app.sd.register(app.service)
        app.service.registered = True
    except Exception as e:
        log.error("Cannot register the service on Consul: %s", str(e))
        app.service.registered = False

    server.start(app.config.getint('WebServer', 'nproc'))

    mongodb_host = app.config.get('MongoDB', 'host')
    mongodb_port = app.config.get('MongoDB', 'port')
    mongodb_url = app.config.get('MongoDB', 'url')

    if mongodb_url != '':
        app.db = MotorClient(mongodb_url)
    else:
        app.db = MotorClient('mongodb://%s:%s' % (mongodb_host, mongodb_port))

    app.sd = ServiceDiscovery(
        endpoint=app.config.get('ServiceDiscovery', 'sd'))

    ioloop = tornado.ioloop.IOLoop.instance()

    def callback_for_signal(sig, frame):
        ioloop.add_callback_from_signal(on_shutdown, app)

    for sig in (SIGINT, SIGTERM, SIGQUIT):
        signal(sig, callback_for_signal)

    if app.service.registered:
        log.info("%s started and registered (PID: %s)",
                 service_name, os.getpid())
    else:
        log.info("%s started but *not* registered (PID: %s)",
                 service_name, os.getpid())

    ioloop.start()


def main():
    tornado.options.parse_command_line()
    startWebServer()


if __name__ == '__main__':
    main()
