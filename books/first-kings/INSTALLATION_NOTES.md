# Install 1 Kings (additive single-book release)

Extract this ZIP and upload **only** its `books` and `data` folders at the **repository root** using GitHub **Add file → Upload files**. Don't upload the ZIP itself and don't add an extra outer folder.

Its new files are confined to `books/first-kings/`, `data/asv1901/first-kings/`, and `data/asv1901/catalog-first-kings.json`. It does not contain previously installed books or a central homepage or master catalog.

Validate from repository root: `python3 books/first-kings/scripts/validate_release.py .` (requires `jsonschema` and PyMuPDF). The optional inspection reader uses browser PDF `#page` fragments, which do not provide guaranteed automatic in-PDF navigation; a future official reader should use a controlled PDF renderer with the page-index metadata.
