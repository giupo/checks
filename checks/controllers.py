# -*- coding:utf-8 -*-

import json
import logging
import numpy

import tornado.web
import tornado.gen
import tornado.escape

from tornado.httpclient import AsyncHTTPClient
from bson.json_util import dumps, loads

from pymongo import ReturnDocument


AsyncHTTPClient.configure("tornado.curl_httpclient.CurlAsyncHTTPClient")
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
            setError(
                handler,
                error='Malformed operator %s' % operator, code=400)
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

        self.finish(dumps(res))

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
            self.finish(dumps(res))
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

        res = yield db.checks.checks.find_one_and_update({

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
        self.set_status(202)
        self.finish(dumps(res))


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

    @tornado.gen.coroutine
    def post(self):
        db = self.application.db
        data = self.request.body.decode("UTF-8")
        if ";" in data:
            delimiter = ";"
        elif "," in data:
            delimiter = ","
        elif "\t" in data:
            delimiter = "\t"
        else:
            setError(self,
                     error="Cannot undestand delimiter in file",
                     code=400)
            return

        lines = data.split("\n")
        log.debug("Length : %s", len(lines))
        log.debug(self.request.body.decode("UTF-8"))
        csv_reader = [
            [x.strip() for x in row.split(delimiter) if len(x.strip()) > 0]
            for row in lines
        ]
        list_to_insert = []
        for row in csv_reader:
            if len(row) > 0:
                list_to_insert.append(self.row_to_dict(row))

        yield db.checks.checks.insert_many(list_to_insert)

        self.set_status(201)
        self.finish()

    def row_to_dict(self, row):
        if (len(row) < 6):
            raise Exception("Malformed checks row: " % row)

        ret = dict(zip(
            ["name", "group", "formula", "operator", "threshold"],
            row[:5]
        ))

        deps = row[5:]
        ret["deps"] = deps

        try:
            ret["threshold"] = float(ret["threshold"])
        except Exception:
            log.debug("failed to convert threshold to float: %s",
                      ret["threshold"])

        return ret


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
        self.finish(dumps(checks))


class GroupChecksHandler(tornado.web.RequestHandler):
    @classmethod
    def routes(cls):
        return [
            (r'/checks/(\w+)', cls)
        ]

    def set_default_headers(self):
        self.set_header('Content-Type', 'application/json')

    @tornado.gen.coroutine
    def get(self, group):
        db = self.application.db

        condition = {'group': {'$eq': group}}

        length = yield db.checks.checks.count_documents(condition)
        checks = db.checks.checks.find(condition)
        checks = yield checks.to_list(length=length)
        self.finish(dumps(checks))

    @tornado.gen.coroutine
    def delete(self, group):
        db = self.application.db
        condition = {'group': {'$eq': group}}
        yield db.checks.checks.delete_many(condition)
        self.set_status(202)
        self.finish()


class CheckExecHandler(tornado.web.RequestHandler):
    @classmethod
    def routes(cls):
        return [
            (r'/checks/(\w+)/(\w+)/exec/(\w+)', cls)
        ]

    def set_default_headers(self):
        self.set_header('Content-Type', 'application/json')

    @tornado.gen.coroutine
    def get(self, group, name, tag):
        sd = self.application.sd
        checkurl = sd.getService("CheckService") + "/checks"
        dataurl = sd.getService("DataService") + "/data"
        execurl = sd.getService("EvalService") + "/eval"

        log.debug("check url: %s", checkurl)
        log.debug("data url: %s", dataurl)
        log.debug("exec url: %s", execurl)

        http_client = AsyncHTTPClient()

        url = "/".join([checkurl, group, name])
        log.debug("connecting to %s" % url)
        res = yield http_client.fetch(url, validate_cert=False)
        check = loads(res.body)

        if res.code == 404:
            setError(self, error="Check not found %s/%s" % (group, name))
            return

        check = loads(res.body)

        log.debug("check: %s", check)
        log.debug("type check: %s", type(check))

        formula = check['formula']
        deps_name = check['deps']
        deps = {}

        for dep_name in deps_name:
            dataurl = sd.getService("DataService") + "/data"
            url = dataurl + "/" + tag + "/" + dep_name
            log.debug("URL to call for deps: %s", url)
            res = yield http_client.fetch(url, validate_cert=False,
                                          raise_error=False)
            if res.code == 404:
                log.warn("Deps %s for check %s/%s not found",
                         dep_name, group, name)
                url = dataurl + "/" + tag + "/ZERIQ"
                res = yield http_client.fetch(url, validate_cert=False,
                                              raise_error=False)
                if res.code == 404:
                    setError(self,
                             error="Couldn't load ZERIQ after deps unmatched",
                             code=500)
                    return

            deps[dep_name] = loads(res.body)

            if 'formula' in deps[dep_name]:
                # questo sta qui solo per ovviare problemi di codec
                # sul fronte EvalService.
                #
                # vanno corretti i dati ed i vari codec delle stringhe
                del deps[dep_name]['formula']

        # see exes params in exes/consts.py
        body = {
            '.formula': formula,
            '.deps': deps,
            '.expected': check['name']
        }

        res = yield http_client.fetch(execurl,
                                      method='POST',
                                      body=dumps(body),
                                      validate_cert=False,
                                      raise_error=False)

        if res.code < 200 or res.code > 299:
            setError(self, error="Error connecting to EvalService: %s" %
                     res.body, code=res.code)
            return

        res = loads(res.body)
        log.debug("Res: %s", res)
        dataresult = res[check['name']]['numbers']
        threshold = check['threshold']
        operator = check['operator']

        if operator == '<=':
            ok = all([x <= threshold
                      for x in dataresult
                      if not numpy.isnan(x)])
        elif operator == '==':
            ok = all([x == threshold
                      for x in dataresult
                      if not numpy.isnan(x)])
        elif operator == '>=':
            ok = all([x >= threshold
                      for x in dataresult
                      if not numpy.isnan(x)])
        elif operator == '>':
            ok = all([x > threshold
                      for x in dataresult
                      if not numpy.isnan(x)])
        elif operator == '<':
            ok = all([x < threshold
                      for x in dataresult
                      if not numpy.isnan(x)])
        else:
            setError(self, error="unknown operator: %s" % operator, code=500)

        res['ok'] = ok
        self.finish(dumps(res))


class GroupChecksExecController(tornado.web.RequestHandler):
    @classmethod
    def routes(cls):
        return [
            (r'/checks/(\w+)/exec/(\w+)', cls)
        ]

    def set_default_headers(self):
        self.set_header('Content-Type', 'application/json')

    @tornado.gen.coroutine
    def get(self, group, tag):
        sd = self.application.sd
        checkurl = sd.getService("CheckService") + "/checks"
        url = "/".join([checkurl, group])
        http_client = AsyncHTTPClient()
        res = yield http_client.fetch(url, validate_cert=False)
        if res.code == 404:
            res = loads(res.body)
            setError(self, error=res['error'])
            return

        checks = loads(res.body)
        ret = {}
        for check in checks:
            checkurl = sd.getService("CheckService") + "/checks"
            exec_url = '/'.join([checkurl, group, check['name'], 'exec', tag])
            res = yield http_client.fetch(exec_url,
                                          validate_cert=False,
                                          raise_error=False)
            ret[check['name']] = loads(res.body)

        self.finish(dumps(ret))
