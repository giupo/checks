# -*- coding:utf-8 -*-

import logging
import coloredlogs

from socket import gethostname

from tornado.options import options, define

try:
    from ConfigParser import ConfigParser
except ImportError:
    from configparser import ConfigParser

log = logging.getLogger(__name__)

DEFAULT_KEY_PATH = 'server.key'
DEFAULT_CERT_PATH = 'server.crt'
DEFAULT_SD = 'http://localhost:8500'
DEFAULT_MONGODB_HOST = 'localhost'
DEFAULT_MONGODB_PORT = '27017'

if 'nproc' not in options:
    define("nproc", default=1, type=int, help="Numero processi")

if 'debug' not in options:
    define("debug", default=False, type=bool,
           help="Starts the server in debug mode")

if 'certfile' not in options:
    define('certfile', default=DEFAULT_CERT_PATH, type=str,
           help='Path to you cert file')

if 'keyfile' not in options:
    define('keyfile', default=DEFAULT_KEY_PATH, type=str,
           help='Path to your key file')

if 'sd' not in options:
    define('sd', default=DEFAULT_SD, type=str,
           help='URL for Consul')

if 'mongodb-host' not in options:
    define('mongodb-host', default=DEFAULT_MONGODB_HOST,
           help='host of mongodb')

if 'mongodb-port' not in options:
    define('mongodb-port', default=DEFAULT_MONGODB_PORT,
           help='port of mongodb')

           
def make_config():
    """init the config object"""
    config = ConfigParser()
    coloredlogs.install(level=log.level)
    config.add_section('WebServer')
    config.set('WebServer', 'protocol', 'http')
    config.set('WebServer', 'address', gethostname())
    config.set('WebServer', 'port', str(9100))
    config.set('WebServer', 'nproc', str(1))
    config.set('WebServer', 'servicename', 'CheckService')
    config.set('WebServer', 'certfile', options.certfile)
    config.set('WebServer', 'keyfile', options.keyfile)
    config.add_section('MongoDB')
    config.set('MongoDB', 'host', options['mongodb_host'])
    config.set('MongoDB', 'port', options['mongodb-port'])
    config.add_section('ServiceDiscovery')
    config.set('ServiceDiscovery', 'sd', options.sd)
    for key, value in options.items():
        config.set('WebServer', str(key), str(value))

    for section in config.sections():
        for key,value in config.items(section):
            log.info("[%s] %s = %s", section, key, value)
        
    return config
