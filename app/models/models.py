from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime, Float, UniqueConstraint
from sqlalchemy.sql.operators import json_path_getitem_op
from .db import Base
from datetime import datetime

class Sparqlendpoint(Base):
    __tablename__ = 'sparql_endpoint'
    id = Column(Integer, primary_key=True)
    local_url = Column(String(256), unique=True)
    name = Column(String(256))
    url = Column(String(256), unique=True)
    # class_relation_file_name = Column(String(256))

    def __init__(self, url=None, name=None, local_url=None):
        self.name=name
        self.local_url=local_url
        self.url=url

class Prefix(Base):
    __tablename__ = 'prefix'
    __table_args__ = (UniqueConstraint('prefix', 'name_space'), {})
    id = Column(Integer, primary_key=True)
    name_space = Column(String(256), unique=True)
    prefix = Column(String(256), unique=True)

    def __init__(self, name_space=None, prefix=None):
        self.name_space=name_space
        self.prefix=prefix

class Class(Base):
    __tablename__ = 'class'
    __table_args__ = (UniqueConstraint('endpoint_id', 'prefix_id', 'name'), {})
    id = Column(Integer, primary_key=True)
    endpoint_id = Column(Integer, ForeignKey('sparql_endpoint.id'))
    prefix_id = Column(Integer, ForeignKey('prefix.id'))
    name = Column(String(256))

    def __init__(self, endpoint_id=None, prefix_id=None,name=None):
        self.endpoint_id=endpoint_id
        self.prefix_id=prefix_id
        self.name=name

class Triple(Base):
    __tablename__ = 'triple'
    __table_args__ = (UniqueConstraint('endpoint_id', 'domain_data', 'domain_datatype', 'prefix_id', 'name', 'range_data','range_datatype', 'probability'), {})
    id = Column(Integer, primary_key=True)
    endpoint_id = Column(Integer, ForeignKey('sparql_endpoint.id'))
    domain_data = Column(String(256))
    domain_datatype = Column(String(256))
    prefix_id = Column(Integer, ForeignKey('prefix.id'))
    name = Column(String(256))
    range_data = Column(String(256))
    range_datatype = Column(String(256))
    range_class = Column(String(256))
    probability = Column(Float)

    def __init__(self, endpoint_id=None, domain_data=None, domain_datatype=None, prefix_id=None, name=None, range_data=None, range_datatype=None, range_class=None, probability=None):
        self.endpoint_id=endpoint_id
        self.domain_data=domain_data
        self.domain_datatype=domain_datatype
        self.prefix_id=prefix_id
        self.name=name
        self.range_data=range_data
        self.range_datatype=range_datatype
        self.range_class=range_class
        self.probability=probability