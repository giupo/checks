# -*- coding: utf-8 -*-

import os
import logging
import json

from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy import Text, Float, Boolean
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
    formula = Column(Text, nullable=False)
    operator = Column(String, nullable=False)
    benchmark = Column(Float, nullable=False, default=0.0)
    created = Column(DateTime, nullable=False)
    updated = Column(DateTime)
    author = Column(String, nullable=False)
    note = Column(Text, default="")
    tag = Column(String, nullable=False)


class Result(Base, JsonMixin, SQLAlchemyDictMixin):
    "Stores checks execution results"
    __tablename__ = "check_results"
    id = Column(Integer, primary_key=True)
    results = Column(Text, nullable=False)
    compliant = Column(Boolean, nullable=False)
    tag = Column(String, nullable=False)
    check = relationship("Check")


Base.metadata.create_all(engine)
