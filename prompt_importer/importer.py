import sqlite3

from beancount.ingest import importer


class PromptImporter(importer.ImporterProtocol):
    def __init__(self, db_file):
        self.db_file = db_file

    def extract(self, f):
        con = sqlite3.connect(self.db_file)
        cur = con.cursor()
        columns = "(regex text, recipient text, skip integer)"
        print(self.name())
        cur.execute(f"CREATE TABLE if not exists {self.name()} {columns}")

        return []
