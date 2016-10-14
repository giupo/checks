# -*- coding:utf-8 -*-

import logging

from tornado.options import parse_command_line, options, define

try:
    from configParser import ConfigParser
except ImportError:
    from configparser import ConfigParser

log = logging.getLogger(__name__)


define("nproc", default=1, type=int, help="Numero processi")


def makeDefaultConfig():
    """init the config object"""
    parse_command_line()
    config = ConfigParser()
    config.add_section('WebServer')

    for key, value in options.items():
        config.set('WebServer', key, value)

    return config

config = makeDefaultConfig()
