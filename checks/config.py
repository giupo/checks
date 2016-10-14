# -*- coding:utf-8 -*-

import logging

from socket import gethostname

from tornado.options import parse_command_line, options, define

try:
    from ConfigParser import ConfigParser
except ImportError:
    from configparser import ConfigParser

log = logging.getLogger(__name__)


define("nproc", default=1, type=int, help="Numero processi")


def makeDefaultConfig():
    """init the config object"""
    parse_command_line()
    config = ConfigParser()
    config.add_section('WebServer')
    config.set('WebServer', 'protocol', 'http')
    config.set('WebServer', 'address', gethostname())
    config.set('WebServer', 'port', str(9100))
    config.set('WebServer', 'nproc', str(1))
    config.set('WebServer', 'servicename', 'CheckService')

    for key, value in options.items():
        config.set('WebServer', str(key), str(value))

    return config


def update_config():
    """updates the config (when it will be available as a Service)"""
    global config
    pass

config = makeDefaultConfig()

for section in config.sections():
    for key, value in config.items(section):
        log.info("[%s] %s = %s", section, key, value)
