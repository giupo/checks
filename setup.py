#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys

from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand


class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import pytest
        errcode = pytest.main(self.test_args)
        sys.exit(errcode)


readme = open('README.rst').read()
history = open('HISTORY.rst').read().replace('.. :changelog:', '')

requirements = [
    'pysd',
    'tornado',
    'sqlalchemy'
]

test_requirements = [
    'pytest',
    'pytest-cov',
    'pytest-bdd',
    'pytest-xdist',
    'pytest-watch',
    'tox',
    'detox'
]

setup(
    name='checks',
    version='0.0.3',
    description='Checks Service Executin Environemnt: executes consistency ' +
                'checks and other types of checks on a FA database',
    long_description=readme + '\n\n' + history,
    author='Giuseppe Acito',
    author_email='giuseppe.acito@gmail.com',
    url='https://github.com/giupo/checks',
    packages=find_packages('checks', excludes='tests')
    include_package_data=True,
    install_requires=requirements,
    license="BSD",
    zip_safe=False,
    keywords='checks',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.5',
    ],
    cmdclass={'test': PyTest},
    test_suite='tests',
    tests_require=test_requirements,
    dependency_links=[
        'https://github.com/giupo/pysd/tarball/master#egg=pysd-0.1.0'
    ]
)
