===============================
Checks service for FA
===============================

.. image:: https://badge.fury.io/py/checks.png
    :target: http://badge.fury.io/py/checks
    
.. image:: https://travis-ci.org/giupo/checks.png?branch=master
        :target: https://travis-ci.org/giupo/checks

.. image:: https://pypip.in/d/checks/badge.png
        :target: https://pypi.python.org/pypi/checks


Checks Service Executin Environemnt: executes consistency checks and other types
of checks on a FA database

* Free software: BSD license
* Documentation: http://checks.rtfd.org.

Features
--------

* Handles persistence for checks definitions
* Issues exections of checks
* Stores checks resutls

Requirements
------------
The service provide a single point for creating, reading, updating and
deleting (CRUD) checks. A check is a set of name, formula (to be executed),
operator (logical opeprator) a baseline/benchmark to for comparison.

Every check, once a formula has been executed and the operator applied to
verify its compliancy to a baseline/benchmark, produces a result which is
stored and used for later retrieval.

It could be useful to use another attribute for checks and results for grouping
the checks. grouping of checks and grouping of results has not to be the same,
they can be different and with different meaning: they are just tags to group a
set of checks logically connected and a set of results logically connected.

The execution of the formula should be delegated to another (micro)service with
the responsability to execute generic formulas, given all the dependencies are
satisfied (This service is already online, but not freely available). By now we
can mockup an execution service as an evaluator of Python expressions: it should
be enough.

Tech Requirements
-----------------
This service should be reachable and searchable. At startup it should declare
itself and be freely available. 

The service should use HTTP(S)/REST to talk to the world.
