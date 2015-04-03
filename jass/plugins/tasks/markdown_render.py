from jass import plugin
try:
    import markdown
except ImportError:
    markdown = None


class MarkdownRender(plugin.Render):
    def can_manage(self, filename):
        return markdown and filename.endswith((
            '.md',
            '.markdown',
        ))

    def render(self, document):
        md = markdown.Markdown()
        usummary = unicode(document.summary, errors="ignore")  # FIXME
        ubody = unicode(document.body, errors="ignore")  # FIXME

        self.api.render_document(
            document.path,
            md.convert(usummary),
            md.convert(ubody),
        )
