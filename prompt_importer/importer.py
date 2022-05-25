import abc
import re
import sqlite3

from beancount.ingest import importer


class Event(abc.ABC):
    @abc.abstractmethod
    def get_field(field: str) -> str:
        pass


class PromptImporter(importer.ImporterProtocol, abc.ABC):
    def __init__(self, db_file):
        self.db_file = db_file

    @abc.abstractmethod
    def get_events(self, filename: str) -> list[Event]:
        pass

    def extract(self, filename: str):
        con = sqlite3.connect(self.db_file)
        cur = con.cursor()
        columns = "(field text, regex text, recipient text, skip integer)"
        print(self.name())
        cur.execute(f"CREATE TABLE if not exists {self.name()} {columns}")

        mappings = list(cur.execute(f"SELECT * FROM {self.name()}"))

        for event in self.get_events(filename):
            recipient_account = None
            skip_event = False
            for field, regex, recipient, skip in mappings:
                r = re.compile(regex)
                if re.fullmatch(r, event.get_field(field)):
                    if skip:
                        skip_event = True
                    else:
                        recipient_account = recipient
                    break

            if skip_event:
                continue

        return []
