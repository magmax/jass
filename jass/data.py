import logging
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    DateTime,
    Sequence,
    ForeignKey,
    text,
)
from sqlalchemy.orm import (
    sessionmaker,
    relationship,
    backref,
)
from sqlalchemy.sql import (
    exists,
)
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

LOGGER = logging.getLogger(__name__)

engine = create_engine('sqlite:///.jass.db', echo=False)
Session = sessionmaker(bind=engine)


class File(Base):
    __tablename__ = 'files'

    path = Column(String, primary_key=True)
    checksum = Column(String)
    updated = Column(DateTime)

    content = relationship("Content", backref="file")
    render = relationship("Render", backref="file")
    properties = relationship("Property")

    def __repr__(self):
        return self.path


class Content(Base):
    __tablename__ = 'content'

    id = Column(Integer, primary_key=True)
    filename = Column(String, ForeignKey('files.path'))


class Render(Base):
    __tablename__ = 'render'

    id = Column(Integer, primary_key=True)
    filename = Column(String, ForeignKey('files.path'))


class Property(Base):
    __tablename__ = 'properties'

    filename = Column(String, ForeignKey('files.path'), primary_key=True)
    key = Column(String, primary_key=True)
    value = Column(String)


def initialize():
    Base.metadata.create_all(engine)


def add_file(path):
    if exists().where(File.path==path):
        return
    LOGGER.debug('Adding file %s', path)
    return


    filename = File(path=key(path))

    session = Session()
    obj = session.query(File).get(filename)
    print dir(obj)
    return
    f = File(path=path)
    session.add(f)
    session.commit()

    return f
