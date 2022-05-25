import abc
import re
import sqlite3

from beancount.ingest import importer
import blessed


class Event(abc.ABC):
    @abc.abstractmethod
    def get_field(self, field: str) -> str:
        pass

    @abc.abstractmethod
    def get_id(self) -> str:
        pass

    @abc.abstractmethod
    def display(self) -> str:
        pass


class PromptImporter(importer.ImporterProtocol, abc.ABC):
    def __init__(self, db_file):
        self.db_file = db_file

    @abc.abstractmethod
    def get_events(self, f) -> list[Event]:
        pass

    def prompt(self):
        return input(">> ")

    def extract(self, f):
        con = sqlite3.connect(self.db_file)
        cur = con.cursor()

        event_id_table_name = f"{self.name()}_id"
        regex_table_name = f"{self.name()}_regex"

        id_columns = f"(event_id text, recipient text, skip integer)"
        cur.execute(f"CREATE TABLE if not exists {event_id_table_name} {id_columns}")

        regex_columns = f"(field text, regex text, recipient text, skip integer)"
        cur.execute(f"CREATE TABLE if not exists {regex_table_name} {regex_columns}")

        id_mappings = list(cur.execute(f"SELECT * FROM {event_id_table_name}"))
        regex_mappings = list(cur.execute(f"SELECT * FROM {regex_table_name}"))

        new_id_mappings = []
        new_regex_mappings = []

        term = blessed.Terminal()
        for event in self.get_events(f):
            recipient_account = None
            skip_event = False

            for event_id, recipient, skip in id_mappings + new_id_mappings:
                if event.get_id() == event_id:
                    if skip:
                        skip_event = True
                    else:
                        recipient = recipient
                    break

            if recipient_account is None and not skip_event:
                for field, regex, recipient, skip in (
                    regex_mappings + new_regex_mappings
                ):

                    # SQLite adds additional escapes, remove them here
                    r = re.compile(regex.replace("\\\\", "\\"))
                    if re.fullmatch(r, event.get_field(field)):
                        if skip:
                            skip_event = True
                        else:
                            recipient_account = recipient
                        break

            if skip_event:
                continue

            if recipient_account is None:
                skip_char = "x"

                print(term.home + term.clear)
                print(event.display())
                print(
                    f"What should the recipient account be? ('{skip_char}' to not extract a transaction)"
                )
                recipient_account = self.prompt().strip()
                print(
                    f"What regex should identify this account (or skip) in the future? ('{skip_char}' to not identify this accoung with a regex)"
                )
                identify_regex = self.prompt().strip()

                if identify_regex == skip_char:
                    if recipient_account == skip_char:
                        new_id_mappings.append((event.get_id(), "", 1))
                    else:
                        new_id_mappings.append((event.get_id(), recipient_account, 0))
                else:
                    print(f"What field should the regex act upon?")
                    target_field = self.prompt().strip()

                    if recipient_account == skip_char:
                        new_regex_mappings.append((target_field, identify_regex, "", 1))
                    else:
                        new_regex_mappings.append(
                            (target_field, identify_regex, recipient_account, 0)
                        )

        if new_id_mappings:
            query = f"INSERT INTO {event_id_table_name} VALUES"
            for new_id_mapping in new_id_mappings:
                query += f"\n{new_id_mapping},"
            cur.execute(query[:-1])
            con.commit()

        if new_regex_mappings:
            query = f"INSERT INTO {regex_table_name} VALUES"
            for new_regex_mapping in new_regex_mappings:
                query += f"\n{new_regex_mapping},"
            cur.execute(query[:-1])
            con.commit()

        con.close()

        return []
