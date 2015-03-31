#!/usr/bin/env python
from __future__ import absolute_import, print_function, unicode_literals

import os
import logging
import argparse
import datetime
import colorlog
import jinja2
from yapsy.PluginManager import PluginManager

from . import data
from . import plugin

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
LOGGER = logging.getLogger(__name__)

PLUGINS_PARSER = 'parser'
PLUGINS_INDEX = 'index'
PLUGINS_TASK = 'task'

PLUGINS = {
    PLUGINS_PARSER : plugin.Parser,
    PLUGINS_INDEX : plugin.Indexer,
    PLUGINS_TASK: plugin.Task,
}


UNDEFINED = object()


class Jass(object):
    def __init__(self, settings, plugin_manager):
        self._settings = settings
        self._plugin_manager = plugin_manager
        self._starting_date = datetime.datetime.now()
        jinja_loader = jinja2.ChoiceLoader([
            jinja2.FileSystemLoader(os.path.join(THIS_DIR, 'templates')),
        ])
        self._jinja_env = jinja2.Environment(loader=jinja_loader)

    def process(self):
        self.task_create_document_list()
        self.task_create_generated_content()
        self.task_remove_deleted_data()
        self.task_update_document_content()
        self.task_render()
        self.task_generate_output()

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

    def task_create_generated_content(self):
        context = dict()

        for plugin in self._plugin_manager.getPluginsOfCategory(PLUGINS_INDEX):
            for document in plugin.plugin_object.get_documents(context.copy()):
                LOGGER.error('Generating document: %s', document )

    def task_remove_deleted_data(self, fn_remove_documents_older_than=
                                 data.Document.remove_older_than):
        LOGGER.debug('Removing deleted documents')
        n = fn_remove_documents_older_than(self._starting_date)
        LOGGER.debug('%s documents were removed', n)

    def task_update_document_content(self):
        LOGGER.info('%s documents to be reloaded',
                    data.Document.count_content_outofdate())

        for doc in data.Document.get_content_outdated():
            LOGGER.info('Reloading %s', doc.relative_path)
            for plugin in self.plugins_parser:
                if plugin.plugin_object.can_manage(doc.path):
                    LOGGER.debug('Plugin %s will process doc %s', plugin.name, doc.path)
                    output_path = plugin.plugin_object.output_file_name(doc.relative_path)
                    content = plugin.plugin_object.parse(doc.path, doc.add_property)
                    if doc.content:
                        doc.content.data = content
                        doc.content.save()
                    else:
                        doc.content = data.Content.create(data=content)
                    doc.is_content_updated = True
                    doc.is_render_updated = False
                    doc.output_path = output_path
                    doc.save()
                    break

    def task_render(self):
        LOGGER.info('%s documents to be regenerated',
                    data.Document.count_render_outofdate())
        for doc in data.Document.get_render_outdated():
            content = doc.content.data
            if doc.render:
                render = doc.render
                render.data = content
                render.save()
            else:
                render = data.Render.create(data=content)
                doc.render = render
            doc.is_render_updated = True
            doc.save()

    def task_generate_output(self):
        LOGGER.info('Writing results')
        for doc in data.Document.select():
            output_path = os.path.join(self._settings.output, doc.output_path)
            directory = os.path.dirname(output_path)
            if os.path.exists(output_path):
                stat = os.stat(output_path)
                if datetime.datetime.fromtimestamp(stat.st_mtime) >= doc.st_mtime:
                    continue
            if not os.path.exists(directory):
                os.makedirs(directory)
            LOGGER.debug('Writing results for %s', output_path)
            try:
                template = self._jinja_env.get_template(doc.template or 'base.html')
            except jinja2.exceptions.TemplateNotFound as e:
                LOGGER.error('Template %s not found. File %s skipped', e, output_path)
                continue

            post_context = doc.get_properties_as_dict()
            post_context['content'] = doc.render.data
            post_context['tags'] = [x.strip() for x in post_context.get('tags', '').split(',')]
            full_rendered = template.render(post=post_context)
            with open(output_path, 'wb') as fd:
                full_content = unicode.encode(full_rendered, errors="ignore")
                fd.write(full_content)

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


class API(object):
    def __init__(self, plugin_manager):
        self._plugin_manager = plugin_manager
        self.settings = None

    def should_manage_file(self, path):
        return any(
            plugin.plugin_object.can_manage(path)
            for plugin in self._plugin_manager.getPluginsOfCategory(PLUGINS_PARSER)
        )

    def data_store(self, plugin_name, kind, key, value):
        try:
            prop = data.DataStore.select().where(
                (data.DataStore.plugin == plugin_name)
                & (data.DataStore.kind == kind)
                & (data.DataStore.key == key)
            ).get()
            prop.value = value
        except data.DataStore.DoesNotExist:
            prop = data.DataStore.create(
                plugin=plugin_name,
                kind=kind,
                key=key,
                value=value
            )
        prop.save()

    def data_retrieve(self, plugin_name, kind, key, default=UNDEFINED):
        try:
            prop = data.DataStore.select().where(
                (data.DataStore.plugin == plugin_name)
                & (data.DataStore.kind == kind)
                & (data.DataStore.key == key)
            ).get()
            return prop.value
        except data.DataStore.DoesNotExist:
            if default is UNDEFINED:
                raise
            return default

    def register_document(self, plugin_name, path, relative_path, st_mtime):
        data.Document.add(path, relative_path, st_mtime)


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

    api = API(plugin_manager)
    api.settings = settings

    data.initialize()
    tasks = sorted(plugin_manager.getPluginsOfCategory(PLUGINS_TASK),
                   key=lambda x: (x.plugin_object.priority, x.name))

    for task in tasks:
        task.plugin_object.jass_initialize(task.name, api)
        task.plugin_object.find_documents()

    return
    jass = Jass(settings, plugin_manager)
    jass.process()


if __name__ == '__main__':
    main()
