import os
import re
import logging
from collections import namedtuple
from yapsy.IPlugin import IPlugin

LOGGER = logging.getLogger('jass.' + __name__)


NewDocument = namedtuple('NewDocument', [
    'path',
    'title',
    'summary',
    'body',
    'properties',  # list
])


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
        pass  # do nothing


class Parser(JassPlugin):
    def can_manage(self, filename):
        """
        Returns True if this plugin can manage this file.
        """
        return True

    def parse(self, path):
        """
        Returns a NewDocument instance with path data.
        """

    def output_file_name(self, filename):
        """
        Returns The final filename
        """
        name, ext = os.path.splitext(filename)
        return name + '.html'

    def read_document(self, path):
        self.logger.debug('Reading file %s', path)
        previous = None
        reading_head = True

        with open(path) as fd:
            lines = fd.readlines()

        # Read the header
        properties = {}
        while lines:
            line = lines.pop(0).strip()
            if line == previous == '':
                break
            previous = line
            if ':' in line:
                key, value = line.split(':', 1)
                if key.startswith('.. '):
                    key = key[3:]
                properties[key] = value

        title = properties.get('title') or self._extract_title(path)
        summary, body = self._split_summary_and_content(''.join(lines))

        self.api.update_document(
            NewDocument(
                path=path,
                title=title,
                summary=summary,
                body=body,
                properties=properties,
            )
        )

    def _extract_title(self, path):
        basename = os.path.basename(path)
        name, ext = os.path.splitext(basename)
        return name.replace('_', ' ')

    def _split_summary_and_content(self, content):
        regex = (
            '(?P<summary>.*)'
            '(?:<!--\s*)?\.\. TEASER_END(?:\s*-->)?'
            '(?P<content>.*)'
        )
        m = re.match(regex, content)
        if m:
            return m.group('summary'), m.group('content')

        return '', content


class Render(JassPlugin):
    def can_manage(self, filename):
        """
        Returns True if this plugin can manage this file.
        """
        return False


    def render(self, document):
        raise NotImplemented('Abstract method')


class Indexer(JassPlugin):
    def get_documents(self, context):
        """
        Should return a list of documents. Generators are allowed.
        """
        raise NotImplemented('Abstract method')
