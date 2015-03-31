import os
import datetime
from jass import plugin


class CreateDocumentList(plugin.Task):
    priority = 100

    def find_documents(self, fn_walk=None, fn_stat=None):
        self.logger.info('Generating the document list')
        fn_walk = fn_walk or os.walk
        fn_stat = fn_stat or os.stat
        for root, dirs, files in fn_walk(self.api.settings.path):
            for filename in files:
                path = os.path.join(root, filename)
                relative_path = os.path.relpath(path, self.api.settings.path)
                if not self.api.should_manage_file(relative_path):
                    continue

                stat = fn_stat(path)
                self.api.register_document(self.name, path, relative_path, stat.st_mtime)
