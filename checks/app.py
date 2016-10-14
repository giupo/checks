# -*- coding;utf-8 -*-

import json

import tornado.web
import tornado.options

from checks import Check, session_scope
from config import config


class CheckHandler(tornado.web.RequestHandler):
    """Handles all the HTTP traffic (mainly CRUD) for Checks"""

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

routes = [
    (r'/checks/(.*)', CheckHandler),
    (r'/checks', CheckHandler)
]
