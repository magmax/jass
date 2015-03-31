import os
import logging
from collections import namedtuple
from yapsy.IPlugin import IPlugin

LOGGER = logging.getLogger('jass.' + __name__)


class Parser(IPlugin):
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


Document = namedtuple('Document', [
    'content',
    'output_path',
    'properties',
])


class Indexer(IPlugin):
    def get_documents(self):
        """
        Should return a list of documents. Generators are allowed.
        """
        raise NotImplemented('Abstract method')
