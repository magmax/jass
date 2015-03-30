import logging
LOGGER = logging.getLogger('jass.plugin.' + __name__)
from jass import plugin
try:
    import markdown
except:
    markdown = None
    LOGGER.error('Markdown plugin disabled: markdown library not found')



class Markdown(plugin.Parser):
    def can_manage(self, filename):
        return markdown and filename.endswith((
            '.md',
            '.markdown',
        ))

    def parse(self, path, fn_add_property):
        content = super(Markdown, self).parse(path, fn_add_property)
        md = markdown.Markdown()
        ucontent = unicode(content, errors="ignore")  # FIXME
        return md.convert(ucontent)
