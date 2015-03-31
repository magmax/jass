import os
import logging
from collections import namedtuple
from yapsy.IPlugin import IPlugin

LOGGER = logging.getLogger('jass.' + __name__)


Document = namedtuple('Document', [
    'slug',
    'title',
    'summary',
    'body',
    'output_path',
    'properties',  # list
])


class JassPlugin(IPlugin):
    priority = 100
    name = 'JassPlugin'

    def jass_initialize(self, name, api):
        self.name = name
        self.api = api
        self.logger = logging.getLogger('jass.plugin.%s' % self.name)


class Task(JassPlugin):
    def find_documents(self):
        raise NotImplemented('Abstract method')


class Parser(JassPlugin):
    def can_manage(self, filename):
        """
        Returns True if this plugin can manage this file.
        """
        return False

    def output_file_name(self, filename):
        """
        Returns The final filename
        """
        name, ext = os.path.splitext(filename)
        return name + '.html'

    def parse(self, path, fn_add_property):
        previous = None
        reading_head = True

        with open(path) as fd:
            lines = fd.readlines()

        # Read the header
        while True:
            line = lines.pop(0).strip()
            if line == previous == '':
                break
            previous = line
            if ':' in line:
                key, value = line.split(':', 1)
                if key.startswith('.. '):
                    key = key[3:]
                fn_add_property(key, value)
                continue

        content = ''.join(lines)
        return content


class Indexer(JassPlugin):
    def get_documents(self, context):
        """
        Should return a list of documents. Generators are allowed.
        """
        raise NotImplemented('Abstract method')
