# Prompt Importer

This package provides a `PromptImporter` base class to build other beancount importers with.
The functionality `PromptImporter` provides is to prompt the user to input recipient accounts
for each transaction while keeping a list of common accounts for easy access.
For example:

```
02/05/2022: Online payment from CHK 1234, 100.00
What should the recipient account be? ('x' to not extract a transaction)
1. Expenses:Groceries   2. Expenses:Restaurants   3. Assets:Checking
>>
```

It also provides functionality to store regexes with which to identify the same account in the future.

## Usage

### Events

To create class that derives from `PromptImporter` you must first define a subclass of `prompt_importer.Event`.
Events represent single transactions from whatever type of file you are importing.
For example, if you are importing a `csv` file, you may have one event per row.
The subclass should implement the following methods:

#### get_field(self, field: str) -> str

Each event may have different fields associated with it.
This method should return the value of a field given an associated field name.

#### get_id(self) -> str

This should return the **globally unique** id associated with an event.

#### display(self) -> str

This is how the event will be displayed to the user before the prompt.

#### get_transaction(self, filename: str, index: int, recipient_account: str) -> data.Transaction

This should return a transaction associated with an event.
To help build the transaction, it takes the file the event was sourced from, its index within the file, and the account that should be the "recipient" of the transaction.

Note that the `data.Transaction` type refers to the `data` from `beancount.core`.

### Importers

Once you have defined an event you can create a subclass of `PromptImporter`.
To do so, you must implement the typical methods associated with the beancount`importer.ImporterProtocol` class.
**Important** the value the method `name(self)` returns should _not_ contain characters not allowed in SQLite table names, such as periods.

The importer should also implement the following method:

#### get_events(self, f) -> list[Event]

Given a beancount file this should return a list of events for the
importer to process.
