import logging
from yapsy.IPlugin import IPlugin

LOGGER = logging.getLogger('jass.' + __name__)


class Parser(IPlugin):
    def can_manage(self, filename):
        """
        Returns True if this plugin can manage this file.
        """
        return False

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
                fn_add_property(key, value)
                continue

        content = ''.join(lines)
        return content
