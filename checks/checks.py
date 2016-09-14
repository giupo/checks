# -*- coding: utf-8 -*-

import os
import logging
import json

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


class Check(Base, JsonMixin, SQLAlchemyDictMixin):
    "Stores Checks data in the DB"
    __tablename__ = 'checks'
    id = Column(Integer, primary_key=True)

    name = Column(String, unique=True)
    """unique name of the check"""

    formula = Column(Text, nullable=False)
    """formula to be executed"""

    expected = Column(String, nullable=True)
    """
    variable name to be present in formula after its execution
    if null, use eval instead of exec
    """

    operator = Column(String, nullable=False)
    """Comparision opeartor used against benchmark"""

    benchmark = Column(Float, nullable=False, default=0.0)
    """a number used as a benchmark for comparision with the opeartor"""

    created = Column(DateTime, nullable=False)
    """When this Check has been created"""

    updated = Column(DateTime)
    """When this Check has been updated"""

    author = Column(String, nullable=False)
    """Author of the check"""

    note = Column(Text, default="")
    """Additional descriptive notes of the check"""

    tag = Column(String, nullable=False)
    """Tag to group the check"""

    def __repr__(self):
        return "<Check(id=%s, name=%s, %s %s %s)>" % (
            self.id,
            self.name,
            self.formula,
            self.operator,
            self.benchmark)


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
