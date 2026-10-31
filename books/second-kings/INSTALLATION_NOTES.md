# 2 Kings | Additive GitHub book installation

Extract this ZIP and use GitHub **Add file → Upload files** at your ASV resource repository's root. Drag the extracted `books` and `data` directories, preserving paths; do not upload the ZIP itself or create an extra outer folder.

This release writes only `books/second-kings/`, `data/asv1901/second-kings/`, and `data/asv1901/catalog-second-kings.json`. It does **not** include earlier Bible books, a root homepage, or the future unified ASV catalog.

Run `python3 books/second-kings/scripts/validate_release.py .` from the repository root (requires `jsonschema` and `PyMuPDF`). The optional inspection reader relies on browser-dependent `#page=` fragments; future official navigation should use a controlled PDF renderer with the included page index.
