# -*- coding: utf-8 -*-

import os
import logging

from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

log = logging.getLogger(__name__)

DB_URL = os.environ.get('DATABASE_URL', 'sqlite://')
engine = create_engine(DB_URL, echo=log.level < logging.INFO)
Session = sessionmaker(bind=engine)
Base = declarative_base()


class JsonMixin(object):
    "Converts to JSON, given the object has a to_dict method"
    def to_json(self):
        return json.dumps(self.to_dict())


class Check(Base):
    "Stores Checks data in the DB"
    __tablename__ = 'checks'
    id = Column(Integer, primary_key=True)


Base.metadata.create_all(engine)
