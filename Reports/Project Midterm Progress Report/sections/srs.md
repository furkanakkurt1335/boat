## Requirements

### Functional

1. User
   1. Accounts
      1. User shall be able to sign up or log in.
   2. Annotation
      1. Navigation
         1. User shall be able to select a sentence to be annotated.
         2. User shall be able to navigate to the preceding or succeeding sentences.
         3. User shall be able to navigate to a sentence by index.
         4. User shall be able to customize the annotation table by
            1. showing or hiding columns of the table.
            2. adding or deleting a row of the table, if the change is found to be valid.
      2. Information
         1. User shall be able to see the sentence being annotated at all times.
         2. User shall be able to see a dependency graph of a sentence.
         3. User shall be able to take notes during annotation.
      3. Modifications
         1. User shall be able to annotate a sentence by
            1. navigating to a specific sentence.
            2. modifying the categories and features corresponding to the fields of the CoNLL-U format in tabular format.
         2. User should be able to undo or redo the modifications as much as they want.
         3. User shall be able to reset the fields of the current sentence to the state they were in before the user opened the sentence.
   3. Access
      1. User shall be able to access the application through a web browser.
      2. User shall be able to access a help page, related to annotating in general and keyboard shortcuts.
   4. Search
      1. User should be able to search the `conllu` files or previous annotations by lemmas, phrases, dependencies & categories.
      2. User should be able to search using regular expressions, if chosen.
2. System
   1. Settings
      1. System should store settings & preferences of a user for use in a subsequent session.
      2. System shall store an annotator's sentences uploaded to the server & annotations done.
   2. Annotation
      1. System shall validate the annotations and check for errors in dependencies.
      2. System shall provide helpful error messages.
   3. Keyboard shortcuts
      1. System shall provide keyboard shortcuts for most tasks.
      2. System shall provide autocompleted results for the fields being edited.
   4. Database
      1. System shall provide a database to store user information.

### Non-functional

1. Errors
   1. Errors given by the validation procedure shall comply with the CoNLL-U format of annotation of [UD](https://universaldependencies.org/format.html).
