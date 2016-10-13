# -*- coding: utf-8 -*-

import os
import logging
import json
import datetime

from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy import Text, Float, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

log = logging.getLogger(__name__)

DB_URL = os.environ.get('DATABASE_URL', 'sqlite://')
engine = create_engine(DB_URL, echo=log.level < logging.INFO)
Session = sessionmaker(bind=engine)
Base = declarative_base()


class JsonMixin(object):
    "Converts to JSON, given the object has a to_dict method"
    def to_json(self):
        return json.dumps(self.to_dict())


class SQLAlchemyDictMixin(object):
    """Converts a Row object to a plain dict based only
       on the columns definitions
    """
    def to_dict(self):
        ret = {}
        for column in self.__table__.columns:
            ret[column.name] = str(getattr(self, column.name))

        return ret


def get_created_value(context):
    """gets 'created' value from current context"""
    return context.current_parameters.get('created')


def datetime_default():
    return datetime.datetime.utcnow()


class Check(Base, JsonMixin, SQLAlchemyDictMixin):
    "Stores Checks data in the DB"
    __tablename__ = 'checks'
    id = Column(Integer, primary_key=True)

    _name = Column("name", String, unique=True)
    _formula = Column("formula", Text, nullable=False)
    _expected = Column("expected", String, nullable=True)
    _operator = Column("operator", String, nullable=False)
    _benchmark = Column("benchmark", Float, nullable=False,
                        default=0.0)
    created = Column("created", DateTime, nullable=False,
                     default=datetime_default())
    """When this Check has been created"""

    _updated = Column("updated", DateTime, nullable=False,
                      default=get_created_value)
    _author = Column("author", String, nullable=False)

    _note = Column("note", Text, default="")
    _tag = Column("tag", String, nullable=False)

    def __repr__(self):
        return "<Check(id=%s, name=%s, %s %s %s)>" % (
            self.id,
            self.name,
            self.formula,
            self.operator,
            self.benchmark)

    @property
    def name(self):
        """unique name of the check"""
        return self._name

    @name.setter
    def name(self, name):
        self._updated = datetime.datetime.utcnow()
        self._name = name

    @property
    def formula(self):
        """formula to be executed"""
        return self._formula

    @formula.setter
    def formula(self, formula):
        self._updated = datetime_default()
        self._formula = formula

    @property
    def expected(self):
        """
        variable name to be present in formula after its execution
        if null, use eval instead of exec
        """
        return self._expected

    @expected.setter
    def expected(self, expected):
        self._updated = datetime_default()
        self._expected = expected

    @property
    def operator(self):
        """Comparision opeartor used against benchmark"""
        return self._operator

    @operator.setter
    def operator(self, operator):
        self._updated = datetime_default()
        self._operator = operator

    @property
    def benchmark(self):
        """a number used as a benchmark for comparision with the opeartor"""
        return self._benchmark

    @benchmark.setter
    def benchmark(self, benchmark):
        self._updated = datetime_default()
        self._benchmark = benchmark

    @property
    def updated(self):
        """When this Check has been updated"""
        return self._updated

    @updated.setter
    def updated(self, updated):
        self._updated = updated

    @property
    def author(self):
        """Author of the check"""
        return self._author

    @author.setter
    def author(self, author):
        self._updated = datetime_default()
        self._author = author

    @property
    def note(self):
        """Additional descriptive notes of the check"""
        return self._note

    @note.setter
    def note(self, note):
        self._updated = datetime_default()
        self._note = note

    @property
    def tag(self):
        """Tag to group the check"""
        return self._tag

    @tag.setter
    def tag(self, tag):
        self._updated = datetime_default()
        self._tag = tag


class Result(Base, JsonMixin, SQLAlchemyDictMixin):
    "Stores checks execution results"
    __tablename__ = "check_results"
    id = Column(Integer, primary_key=True)
    results = Column(Text, nullable=False)
    """
    Stores a JSON-serializd  object resulting from the execution
    of the check
    """

    compliant = Column(Boolean, nullable=False)
    """
     it's `True` if the application of the Check.operator against
     `Check.benchmark` is always `True`
    """

    tag = Column(String, nullable=False)
    """tag to group results"""

    check_id = Column(Integer, ForeignKey(Check.id))
    """foreign_key to the Check"""

    check = relationship("Check", foreign_keys='Result.check_id')
    """check object referenced from Result.check_id"""

    def __repr__(self):
        return "<Result(id=%s, compliant=%s, check_id:%s)>" % (
            self.id,
            self.compliant,
            self.check_id)

Base.metadata.create_all(engine)
