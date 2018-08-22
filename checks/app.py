# -*- coding:utf-8 -*-

import os
import json
import signal
import logging

import tornado.web
import tornado.ioloop
import tornado.options
import tornado.httpserver

from ServiceDiscovery.discovery import Service

from checks import Check, session_scope
from config import config
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


routes = []
routes.extend(CheckHandler.routes())
routes.extend(ConfigHandler.routes())

settings = {
    "cookie_secret": os.environ.get('SECRET') or 'secret',
    "xsrf_cookies": False
}

application = tornado.web.Application(routes, **settings)
checkService = None


def on_shutdown():
    """shutdown callback"""
    global checkService
    log.info("Shutdown started")
    if checkService:
        checkService.unregister()

    tornado.ioloop.IOLoop.instance().stop()
    log.info("Shutdown completed")


def startWebServer():
    server = tornado.httpserver.HTTPServer(application)
    protocol = config.get('WebServer', 'protocol')
    addr = config.get('WebServer', 'address')
    port = config.getint('WebServer', 'port')
    service_name = config.get('WebServer', 'servicename')

    while True:
        try:
            log.info('try port %s', port)
            server.bind(port)
            log.info("%s at %s://%s:%s", service_name, protocol, addr, port)
            config.set('WebServer', 'port', str(port))
            break
        except Exception as e:
            log.info('port %s already used (%s) ... ', str(port), str(e))
            port += 1

    checkService = Service(service_name, "%s://%s:%s" % (
        protocol,
        addr,
        port
    ))

    server.start(config.getint('WebServer', 'nproc'))
    ioloop = tornado.ioloop.IOLoop.instance()
    checkService.register()

    signal.signal(signal.SIGINT,
                  lambda sig, frame:
                  ioloop.add_callback_from_signal(on_shutdown))
    signal.signal(signal.SIGTERM,
                  lambda sig, frame:
                  ioloop.add_callback_from_signal(on_shutdown))
    signal.signal(signal.SIGQUIT,
                  lambda sig, frame:
                  ioloop.add_callback_from_signal(on_shutdown))

    log.info("%s started and registered (PID: %s)", service_name, os.getpid())
    ioloop.start()


def main():
    startWebServer()

if __name__ == '__main__':
    main()
