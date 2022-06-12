import abc
import collections
import json
import re

from beancount.core import data
from beancount.ingest import importer
import blessed
from pytest import skip


class QueueSet:
    # A queue that bumps duplicate items to the front instead of prepending them
    def __init__(self, size):
        self.size = size
        self.queue = []

    def push(self, item):
        self.queue = [item] + list(filter(lambda i: i != item, self.queue))
        self.queue = self.queue[: self.size]

    def __iter__(self):
        return iter(self.queue)


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

    @abc.abstractmethod
    def get_transaction(
        self, filename: str, index: int, recipient_account: str
    ) -> data.Transaction:
        pass


class PromptImporter(importer.ImporterProtocol, abc.ABC):
    def __init__(self, json_filename: str, skip_character: str = "x"):
        self.json_filename = json_filename
        self.skip_characteracter = skip_character

    @abc.abstractmethod
    def get_events(self, f) -> list[Event]:
        pass

    def prompt(self):
        return input(">> ")

    def extract(self, f):
        top_level_key = self.name()

        try:
            with open(self.json_filename, "r") as infile:
                mapping_data = json.load(infile)
        except FileNotFoundError:
            print("Mapping file does not exist, creating...")
            mapping_data = {}

        if top_level_key not in mapping_data:
            mapping_data[top_level_key] = {"id": [], "regex": []}

        """
        mapping_data structure:
        {
            <top_level_key>: {
                regex: [
                    {
                        field: ...,
                        regex: ...,
                        recipient ..., (None if skip)
                    }
                ],
                id: [
                    {
                        event_id: ...,
                        recipient: ..., (None if skip)
                    }
                ]
            }
        }
        """

        id_mappings = mapping_data[top_level_key]["id"]
        regex_mappings = mapping_data[top_level_key]["regex"]

        known_recipients = collections.Counter(
            [m["recipient"] for m in regex_mappings]
            + [m["recipient"] for m in id_mappings]
        )

        top_known_recipients = {}
        for index, (kr, _) in enumerate(known_recipients.most_common(3)):
            top_known_recipients[str(index + 1)] = kr

        num_top_known_recipients = len(top_known_recipients)

        recent_recipients = QueueSet(3)
        txns = []
        print_txns = True
        term = blessed.Terminal()
        for index, event in enumerate(self.get_events(f)):
            recipient_account = None

            # Check if one of the IDs matches
            for id_mapping in id_mappings:
                if event.get_id() == id_mapping["event_id"]:
                    recipient_account = id_mapping["recipient"]
                    break

            # If no ID match occurred, check if any of the regexes matches
            if recipient_account is None:
                for regex_mapping in regex_mappings:
                    r = re.compile(regex_mapping["regex"])
                    if re.fullmatch(r, event.get_field(regex_mapping["field"])):
                        recipient_account = regex_mapping["recipient"]

            if recipient_account is None:
                print_txns = False
                self.skip_character = "x"

                print(term.home + term.clear)
                print(event.display())
                print(
                    f"What should the recipient account be? ('{self.skip_character}' to not extract a transaction)"
                )

                for rr_index, rr in enumerate(recent_recipients):
                    top_known_recipients[
                        str(num_top_known_recipients + rr_index + 1)
                    ] = rr

                known_recipients_message = ""
                for label, kr in top_known_recipients.items():
                    known_recipients_message += f"{label}. {kr}   "
                print(known_recipients_message)

                recipient_account = self.prompt().strip()

                if recipient_account in top_known_recipients:
                    recipient_account = top_known_recipients[recipient_account]

                if recipient_account == self.skip_character:
                    recipient_account = "skip"
                else:
                    recent_recipients.push(recipient_account)

                print(
                    f"What regex should identify this account (or skip) in the future? ('{self.skip_character}' to not identify this accoung with a regex)"
                )
                identify_regex = self.prompt().strip()

                if identify_regex == self.skip_character:
                    id_mappings.append(
                        {"event_id": event.get_id(), "recipient": recipient_account}
                    )
                else:
                    print(f"What field should the regex act upon?")
                    target_field = self.prompt().strip()
                    regex_mappings.append(
                        {
                            "field": target_field,
                            "regex": identify_regex,
                            "recipient": recipient_account,
                        }
                    )

            if print_txns and recipient_account != "skip":
                txns.append(event.get_transaction(f.name, index, recipient_account))

        with open(self.json_filename, "w+") as outfile:
            json.dump(mapping_data, outfile, indent=4)

        if print_txns:
            return txns
        else:
            return []
