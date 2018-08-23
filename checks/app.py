# -*- coding:utf-8 -*-

import os
import json
import logging

import tornado.web
import tornado.ioloop
import tornado.options
import tornado.httpserver

from ServiceDiscovery.discovery import ServiceDiscovery, Service
from signal import signal, SIGINT, SIGTERM, SIGQUIT

from checks.checks import Check, session_scope
from checks.config import make_config
from ServiceDiscovery.app import ConfigHandler
log = logging.getLogger(__name__)


class CheckHandler(tornado.web.RequestHandler):
    """Handles all the HTTP traffic (mainly CRUD) for Checks"""

    @classmethod
    def routes(cls):
        return [
            (r'/checks/(.*)', cls),
            (r'/checks/', cls),
            (r'/checks', cls)
        ]

    def set_default_headers(self):
        # this is a JSON RESTful API
        self.set_header('Content-Type', 'application/json')

    def get(self, id=None):
        with session_scope() as session:
            if id is None:
                # get all the checks
                result = [x.to_dict() for x in session.query(Check).all()]
            else:
                if id.isdigit():
                    result = session.query(Check).filter(id=id).first()
                else:
                    result = session.query(Check).filter(name=id).first()

                if result is not None:
                    result = result.to_dict()
                else:
                    raise tornado.web.HTTPError(404)

            self.finish(json.dumps(result))

    def post(self):
        with session_scope() as session:
            check = Check(**self.arguments)
            session.add(check)
            session.commit()
            self.set_status(201)
            self.finish(check.to_json())


def build_routes():
    routes = []
    routes.extend(CheckHandler.routes())
    routes.extend(ConfigHandler.routes())
    return routes


def get_app():
    """Factory for torando.web.Application"""
    config = make_config()
    settings = {
        "cookie_secret": os.environ.get('SECRET') or 'secret',
        "xsrf_cookies": False,
        "debug": config.getboolean('WebServer', 'debug')
    }

    app = tornado.web.Application(build_routes(), **settings)
    app.config = config
    app.sd = ServiceDiscovery(endpoint=config.get('ServiceDiscovery', 'sd'))
    return app


def on_shutdown(app):
    """shutdown callback"""
    global checkService
    log.info("Shutdown started")
    try:
        app.sd.unregister(app.service)
    except Exception as e:
        log.error("Cannot de-register on Consul: %s", str(e))
    tornado.ioloop.IOLoop.instance().stop()
    log.info("Shutdown completed")


def startWebServer():
    app = get_app()
    server = tornado.httpserver.HTTPServer(app)
   
    protocol = app.config.get('WebServer', 'protocol')
    addr = app.config.get('WebServer', 'address')
    port = app.config.getint('WebServer', 'port')
    service_name = app.config.get('WebServer', 'servicename')

    ssl_options = None
    if "https" == protocol:
        ssl_options = {
            "certfile": app.config.get('WebServer', 'servercert'),
            "keyfile": app.config.get('WebServer', 'keyfile')
        }
        log.info("Good body, you have HTTPS configured")
    else:
        log.warning("Server should be always on HTTPS!")

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
    except Exception as e:
        log.error("Cannot register on service on Consul: %s", str(e))
        
    server.start(app.config.getint('WebServer', 'nproc'))
    ioloop = tornado.ioloop.IOLoop.instance()

    def callback_for_signal(sig, frame):
        ioloop.add_callback_from_signal(on_shutdown, app)
    
    for sig in (SIGINT, SIGTERM, SIGQUIT):
        signal(sig, callback_for_signal)

    log.info("%s started and registered (PID: %s)", service_name, os.getpid())
    ioloop.start()


def main():
    tornado.options.parse_command_line()
    startWebServer()


if __name__ == '__main__':
    main()
