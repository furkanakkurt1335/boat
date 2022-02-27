# Web Annotation Tool
A Web Application for Annotating Dependency Parse Treebanks – 492 Project

## Description
This project is being developed for improving the already-existing Annotation Tool [here](https://github.com/boun-tabi/BoAT) and creating a web application for it.

## Fork of original desktop GUI
There is a fork of the original desktop GUI, based on Qt & written in Python, uploaded to this repository under the folder `src_fork`.

Main changes to the original is:
- Upgrading from PySide2 to PySide6 [Qt5 to Qt6]
- Removing the table's column label checkboxes atop & adding a textbox atop instead that's to be used to add / remove columns. This text field can be focused with `ALT + C` and has a shorthand writing system where one can write the initials of a column and then press enter, and the column appears or disappears depending on its previous state. For example, if one writes `fore` and presses enter, the column `Foreign` appears if it was hidden & disappears if it was on. If one writes a non-existing name for a column, it's just discarded. This was intended to reduce clutter and make space for the most important part of the window, the table.
- Autocomplete of table cell textboxes where one can fill the cells during annotation and the program checks whether the text filled is compatible with the column's type. If it's not compatible, it's just discarded. It also has a shorthand writing system where one can just write the initials (e.g. `s` for `Sing` under the column `Number`).

All the available columns are here for reference: ID, FORM, LEMMA, UPOS, XPOS, FEATS, HEAD, DEPREL, DEPS, MISC, Abbr, Animacy, Aspect, Case, Clusivity, Definite, Degree, Echo, Evident, Foreign, Gender, Mood, NounClass, Number, Number[psor], NumType, Person, Person[psor], Polarity, Polite, Poss, PronType, Reflex, Register, Tense, VerbForm, Voice

### Changes to document saving
The original application saves the document with the new annotations after each change to the cells, after going to a sentence with the `Go` button and after resetting with the `Reset` button (or by the shortcut). Document saving has been observed to cause a freezing for a couple seconds. Saving by the aforementioned 3 ways have been deprecated. Hence, 2 new ways to save the `conllu` document has been established:
- A new button `Save` has been added next to the `Next` button where the document can be saved.
- Closing the application also triggers saving the document in case it was not saved with the button.

As mentioned, saving the document takes a couple seconds, so after closing the application, one should be aware that it's saving the document before closing.

### Note to previous users of the application
The Python library requirements have changed: PySide6 should be installed before executing the app. One can do this by calling `pip install -r requirements.txt` in the working directory.
