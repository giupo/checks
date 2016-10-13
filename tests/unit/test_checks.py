#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_checks
----------------------------------

Tests for `checks` module.
"""

from checks.checks import Check


def test_updated_in_checks():
    x = Check()
    x.name = 'name'
    old = x.updated

    x.author = 'me'
    assert x.updated > old
    old = x.updated

    x.tag = 'dataid'
    assert x.updated > old
    old = x.updated

    x.formula = 'A+B'
    assert x.updated > old
    old = x.updated

    x.benchmark = 0.1
    assert x.updated > old
    old = x.updated
    x.operator = '<'

    assert x.updated > old
    assert x.created is None
