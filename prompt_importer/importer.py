import abc
import re
import sqlite3

from beancount.ingest import importer


class Event(abc.ABC):
    @abc.abstractmethod
    def get_field(self, field: str) -> str:
        pass

    @abc.abstractmethod
    def get_id(self) -> str:
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

        id_table_name = f"{self.name()}_id"
        regex_table_name = f"{self.name()}_regex"

        id_columns = "(id text, recipient text, skip integer)"
        cur.execute(f"CREATE TABLE if not exists {id_table_name} {id_columns}")

        regex_columns = "(field text, regex text, recipient text, skip integer)"
        cur.execute(f"CREATE TABLE if not exists {regex_table_name} {regex_columns}")

        id_mappings = list(cur.execute(f"SELECT * FROM {id_table_name}"))
        regex_mappings = list(cur.execute(f"SELECT * FROM {regex_table_name}"))

        for event in self.get_events(filename):
            recipient_account = None
            skip_event = False

            for event_id, recipient, skip in id_mappings:
                if event.get_id() == event_id:
                    if skip:
                        skip_event = True
                    else:
                        recipient = recipient
                    break

            if recipient_account is None and not skip_event:
                for field, regex, recipient, skip in regex_mappings:
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
