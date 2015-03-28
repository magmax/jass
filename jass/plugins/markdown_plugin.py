import logging
from jass import plugin
import markdown

LOGGER = logging.getLogger('jass.' + __name__)


class Markdown(plugin.Parser):
    def can_manage(self, filename):
        return filename.endswith((
            '.md',
            '.markdown',
        ))

    def parse(self, path, fn_add_property):
        content = super(Markdown, self).parse(path, fn_add_property)
        return markdown.Markdown(content, extensions=['markdown.extensions.extra'])
