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
