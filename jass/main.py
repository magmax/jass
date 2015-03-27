#!/usr/bin/env python
from __future__ import absolute_import, print_function, unicode_literals

import os
import logging
import argparse
import datetime
from . import data

LOGGER = logging.getLogger(__name__)


class Jass(object):
    def __init__(self, settings):
        self._settings = settings
        self._starting_date = datetime.datetime.now()

    def process(self):
        self.task_initialize()
        self.task_create_file_list()
        self.task_remove_deleted_data()
        self.task_update_document_content()

    def task_initialize(self):
        LOGGER.debug('Initializing database')
        data.initialize()

    def task_create_file_list(self, walk_fn=os.walk, add_fn=data.Document.add):
        LOGGER.info('Generating the document list')
        n = 0
        for root, dirs, files in walk_fn(self._settings.path):
            for filename in files:
                path = os.path.join(root, filename)
                relative_path = os.path.relpath(path, self._settings.path)
                stat = os.stat(path)
                date = datetime.datetime.fromtimestamp(stat.st_mtime)
                if add_fn(relative_path, date):
                    n += 1
        LOGGER.info('%s documents added', n)

    def task_remove_deleted_data(self, fn_remove_documents_older_than=
                                 data.Document.remove_older_than):
        LOGGER.info('Removing removed documents')
        n = fn_remove_documents_older_than(self._starting_date)
        LOGGER.info('%s documents were removed', n)

    def task_update_document_content(self):
        LOGGER.info('%s documents to be reloaded',
                    data.Document.count_content_outofdate())


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

    format = '%(relativeCreated)#10.2f [%(levelname)5.5s] %(message)s'
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
