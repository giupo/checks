# -*- coding:utf-8 -*-

import json
import logging

import tornado.web
import tornado.gen
import tornado.escape

from pymongo import ReturnDocument

log = logging.getLogger(__name__)


def setError(handler, **params):
    handler.set_header('Content-Type', 'application/json')

    ret = {
        'error': 'Not found',
        'code': 404,
        'host': handler.request.host
    }

    handler.set_status(ret['code'])
    
    for key, value in params.items():
        ret[key] = value

    handler.finish(json.dumps(ret))


def validateCheck(handler, check):
    """ 
    Apply validation check
    
    Makes sure 'check' is properly compiled and set an Error
    on handler in case it's not.

    return `True` on validation, `False` otherwise
    """
    
    if 'formula' not in check:
        setError(handler, error='Check must have a "formula"', code=400)
        return False
  
    if 'deps' not in check:
        setError(handler, error='Check must have "deps" specified', code=400)
        return False
  
    if 'autore' not in check:
        setError(handler, error='Check must have an "author"', code=400)
        return False
  
    if 'threshold' not in check:
        check['threshold'] = 0.1
        
    if 'operator' not in check:
        check['operator'] = '<='
    else:
        operator = check['operator']
        if operator not in ('<', '>', '==', '<=', '>=', '<>'):
            setError(self, error='Malformed operator %s' % operator, code=400)
            return False

    return True
          
    
class NotFoundHandler(tornado.web.RequestHandler):
    def prepare(self):
        setError(self)


class CheckHandler(tornado.web.RequestHandler):
    """Handles all the HTTP traffic (mainly CRUD) for Checks"""

    @classmethod
    def routes(cls):
        return [
            (r'/checks/(\w+)/(\w+)', cls)
        ]

    def set_default_headers(self):
        # this is a JSON RESTful API
        self.set_header('Content-Type', 'application/json')

    @tornado.gen.coroutine
    def get(self, group, name):
        db = self.application.db
        res = yield db.checks.checks.find_one({
            'group': {'$eq': group},
            'name': {'$eq': name}
        })

        if res is None:
            setError(self, error='Check %s/%s not found' % (group, name))
            return

        self.finish(json.dumps(res))

    @tornado.gen.coroutine
    def post(self, group, name):
        db = self.application.db
        check = tornado.escape.json_decode(self.request.body)
        if not validateCheck(self, check):
            return

        try:
            res = yield db.checks.checks.find_one_and_update({
                'group': {'$eq': group},
                'name': {'$eq': name}
            }, check, upsert=True, return_document=ReturnDocument.AFTER)
            
            self.set_status(201)
            self.finish(json.dumps(res))
        except Exception as e:
            log.error(e)
            setError(self, error=str(e), code=500)
            return
            
    def put(self, group, name):
        db = self.application.db
        check = tornado.escape.json_decode(self.request.body)
        res = yield db.checks.checks.find_one({
            'group': {'$eq': group},
            'name': {'$eq': name}    
        })
        
        if res is None:
            setError(self, error='Check %s/%s not found' % (group, name))
            return

        res = yield db.checks.checks.find_one_and_updatee({
            
        }, {
            '$set': check
        }, return_document=ReturnDocument.AFTER)

        self.finish(json.dumps(res))
        
    def delete(self, group, name):
        db = self.application.db
        res = yield db.checks.checks.find_one_and_delete({
            'group': {'$eq': group},
            'name': {'$eq': name}         
        })
        self.finish(json.dumps(res))


class CsvBulkHandler(tornado.web.RequestHandler):
    @classmethod
    def routes(cls):
        return [
            (r'/checks.csv', cls)
        ]

    def set_default_headers(self):
        self.set_header('Content-Type', 'text/csv')

    @tornado.gen.coroutine
    def get(self):
        db = self.application.db
        length = yield db.checks.checks.count_documents({})
        checks = db.checks.checks.find()
        checks = yield checks.to_list(length=length)
        for check in checks:
            row = ';'.join([
                check['name'],
                check['group'],
                check['formula'],
                check['operator'],
                check['threshold'],
                ';'.join(check['deps'])
            ])
            self.write(row)
            self.write('\n')

        self.finish()

    def post(self):
        db = self.application.db
        csv = self.request.body
        
        self.set_status(201)
        self.finish()


class BulkHandler(tornado.web.RequestHandler):
    @classmethod
    def routes(cls):
        return [
            (r'/checks', cls)
        ]

    def set_default_headers(self):
        self.set_header('Content-Type', 'application/json')

    @tornado.gen.coroutine
    def get(self):
        db = self.application.db
        length = yield db.checks.checks.count_documents({})
        checks = db.checks.checks.find()
        checks = yield checks.to_list(length=length)
        self.finish(json.dumps(checks))

    
