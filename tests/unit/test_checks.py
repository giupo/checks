#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_checks
----------------------------------

Tests for `checks` module.
"""
import json
from tornado.testing import AsyncHTTPTestCase
import checks.app


class TestChecksApp(AsyncHTTPTestCase):

    def get_app(self):
        self.app = checks.app.get_app()
        return self.app

    def test_homepage(self):
        response = self.fetch('/checks')
        self.assertEqual(response.code, 200)
        self.assertEqual(json.loads(response.body), [])

    def tearDown(self):
        super(AsyncHTTPTestCase, self).tearDown()
        self.app.db.close()
