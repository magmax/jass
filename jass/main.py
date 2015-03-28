#!/usr/bin/env python
from __future__ import absolute_import, print_function, unicode_literals

import os
import logging
import argparse
import datetime
import colorlog
from yapsy.PluginManager import PluginManager
from . import data
from . import plugin

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
LOGGER = logging.getLogger(__name__)

PLUGINS_PARSER = 'parser'

PLUGINS = {
    PLUGINS_PARSER : plugin.Parser,
}


class Jass(object):
    def __init__(self, settings, plugin_manager):
        self._settings = settings
        self._plugin_manager = plugin_manager
        self._starting_date = datetime.datetime.now()

    def process(self):
        self.task_initialize()
        self.task_create_document_list()
        self.task_remove_deleted_data()
        self.task_update_document_content()
        self.task_generate_output()

    def task_initialize(self):
        LOGGER.debug('Initializing database')
        data.initialize()

    def task_create_document_list(self, walk_fn=os.walk, add_fn=data.Document.add):
        LOGGER.info('Generating the document list')
        n = 0
        for root, dirs, files in walk_fn(self._settings.path):
            for filename in files:
                path = os.path.join(root, filename)
                relative_path = os.path.relpath(path, self._settings.path)
                if not self.is_supported(relative_path):
                    continue
                stat = os.stat(path)
                date = datetime.datetime.fromtimestamp(stat.st_mtime)
                if add_fn(path, relative_path, date):
                    n += 1
        LOGGER.info('%s documents added', n)

    def task_remove_deleted_data(self, fn_remove_documents_older_than=
                                 data.Document.remove_older_than):
        LOGGER.debug('Removing deleted documents')
        n = fn_remove_documents_older_than(self._starting_date)
        LOGGER.debug('%s documents were removed', n)

    def task_update_document_content(self):
        LOGGER.info('%s documents to be reloaded',
                    data.Document.count_content_outofdate())

        for doc in data.Document.get_content_outdated():
            for plugin in self.plugins_parser:
                if plugin.plugin_object.can_manage(doc.path):
                    LOGGER.debug('Plugin %s will process doc %s', plugin.name, doc.path)
                    content = plugin.plugin_object.parse(doc.path, doc.add_property)
                    if doc.content:
                        doc.content.data = content
                    else:
                        doc.content = data.Content.create(data=content)
                    doc.is_content_updated = True
                    doc.is_render_updated = False
                    doc.save()
                    break

    def task_generate_output(self):
        LOGGER.info('%s documents to be regenerated',
                    data.Document.count_render_outofdate())
        for doc in data.Document.get_render_outdated():
            pass


    def is_supported(self, path):
        for plugin in self.plugins_parser:
            if plugin.plugin_object.can_manage(path):
                return True

        return False

    @property
    def plugins_parser(self):
        return self._plugin_manager.getPluginsOfCategory(PLUGINS_PARSER)

def logging_setup(verbose):
    def inner(logger_name, format, level):
        logger = logging.getLogger(logger_name)
        handler = logging.StreamHandler()
        logger.addHandler(handler)

        formatter = colorlog.ColoredFormatter(format)
        for handler in logger.handlers:
            handler.setFormatter(formatter)

        logger.setLevel(level)
        logger.propagate = False
        if level == logging.INFO:
            LOGGER.debug('Logging INFO for %s' % logger_name)
        elif level == logging.DEBUG:
            LOGGER.debug('Logging DEBUG for %s' % logger_name)

    format = '%(log_color)s%(relativeCreated)#10.2f [%(levelname)5.5s]%(reset)s %(blue)s%(message)s'
    if verbose == 0:
        format = '%(name)s %(levelname)s %(message)s'
        level = logging.WARN
        level_peewee = logging.WARN
    elif verbose == 1:
        level = logging.INFO
        level_peewee = logging.WARN
    elif verbose == 2:
        level = logging.DEBUG
        level_peewee = logging.INFO
    else:
        level = logging.DEBUG
        level_peewee = logging.DEBUG

    inner('jass', format, level)
    inner('peewee', format, level_peewee)
    inner('yapsy', format, level)


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
    parser.add_argument('--plugin-path', dest='plugin_paths', action='append', default=[],
                        help='Where plugins should be found.')

    settings = parser.parse_args()

    settings.plugin_paths.extend([
        os.path.join(os.path.expanduser("~"), '.config', 'jass', 'plugins'),
        os.path.join(THIS_DIR, 'plugins'),
    ])

    logging_setup(settings.verbose)

    LOGGER.debug('Loading plugins in %s', settings.plugin_paths)
    plugin_manager = PluginManager()
    plugin_manager.setPluginPlaces(settings.plugin_paths)
    plugin_manager.setCategoriesFilter(PLUGINS)
    plugin_manager.collectPlugins()

    jass = Jass(settings, plugin_manager)
    jass.process()


if __name__ == '__main__':
    main()
