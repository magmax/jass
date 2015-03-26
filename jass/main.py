#!/usr/bin/env python

import os
import logging
import argparse

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    text,
)
from sqlalchemy.orm import (
    sessionmaker,
    relationship,
    backref,
)
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()


LOGGER = logging.getLogger(__name__)

engine = create_engine('sqlite:///.jass.db', echo=False)
Session = sessionmaker(bind=engine)


class File(Base):
    __tablename__ = 'files'

    id = Column(Integer, primary_key=True)
    path = Column(String, unique=True)
    checksum = Column(String)
    updated = Column(DateTime, server_default=text('NOW'))

    content = relationship("Content", backref="file")
    render = relationship("Render", backref="file")
    properties = relationship("Property")

    def __repr__(self):
        return self.path


class Content(Base):
    __tablename__ = 'content'

    id = Column(Integer, primary_key=True)
    file_id = Column(Integer, ForeignKey('files.id'))


class Render(Base):
    __tablename__ = 'render'

    id = Column(Integer, primary_key=True)
    file_id = Column(Integer, ForeignKey('files.id'))


class Property(Base):
    __tablename__ = 'properties'

    id = Column(Integer, primary_key=True)
    file_id = Column(Integer, ForeignKey('files.id'))
    key = Column(String)
    value = Column(String)


class Jass(object):
    def __init__(self, settings):
        self._settings = settings

    def process(self):
        self.task_initialize()
        self.task_create_file_list()

    def task_initialize(self):
        LOGGER.debug('Initializing database')
        Base.metadata.create_all(engine)

    def task_create_file_list(self):
        LOGGER.debug('Generating the file list')
        for root, dirs, files in os.walk(self._settings.path):
            for filename in files:
                path = os.path.join(root, filename)
                relative_path = os.path.relpath(path, self._settings.path)
                print relative_path


def logging_setup(verbose):
    def inner(logger_name, format, level):
        logger = logging.getLogger(logger_name)
        if len(logger.handlers) == 0:
            handler = logging.StreamHandler()
            logger.addHandler(handler)

        formatter = logging.Formatter(format)
        for handler in logger.handlers:
            handler.setFormatter(formatter)

        logger.setLevel(level)
        logger.propagate = False
        if level == logging.INFO:
            LOGGER.info('Logging INFO for %s' % logger_name)
        elif level == logging.DEBUG:
            LOGGER.debug('Logging DEBUG for %s' % logger_name)

    format = '%(asctime)s [%(levelname)5.5s] %(message)s'
    if verbose == 0:
        format = '%(name)s %(levelname)s %(message)s'
        level = logging.WARN
        level_alchemy = logging.WARN
    elif verbose == 1:
        level = logging.INFO
        level_alchemy = logging.WARN
    elif verbose == 2:
        level = logging.DEBUG
        level_alchemy = logging.WARN
    elif verbose == 3:
        level = logging.DEBUG
        level_alchemy = logging.INFO
    elif verbose == 4:
        level = logging.DEBUG
        level_alchemy = logging.INFO
    else:
        level = logging.DEBUG
        level_alchemy = logging.DEBUG

    inner('jass', format, level)
    inner('sqlalchemy', format, level_alchemy)

def main():
    parser = argparse.ArgumentParser(description='Just Another Static Site: Static Sites generator')
    parser.add_argument('--path', default='source',
                        help='path to the project definition')
    parser.add_argument('--output', default='output',
                        help='where results should be put.')
    parser.add_argument('--follow-symlinks', dest='follow_symlinks', action='store_true', default=False,
                        help='If the process should follow symlinks')
    parser.add_argument('--verbose', '-v', action='count', default=0,
                        help='Verbosity level. Accumulative.')

    settings = parser.parse_args()

    logging_setup(settings.verbose)

    jass = Jass(settings)
    jass.process()



if __name__ == '__main__':
    main()
