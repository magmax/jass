import logging
LOGGER = logging.getLogger('jass.plugin.' + __name__)
from jass import plugin


class Indexer(plugin.Indexer):
    def get_documents(self, context):
        return []
