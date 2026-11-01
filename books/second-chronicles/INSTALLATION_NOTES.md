# Add 2 Chronicles to the ASV Foundation

Extract the ZIP. In your ASV Foundation GitHub repository root choose **Add file → Upload files**. Drag only the extracted `books` and `data` directories, preserving internal paths. Do not upload the ZIP itself.

This package adds **only** `books/second-chronicles/`, `data/asv1901/second-chronicles/`, and `data/asv1901/catalog-second-chronicles.json`. It never replaces an earlier book, a root homepage or the future shared catalog. Validation command: `python3 books/second-chronicles/scripts/validate_release.py .` (requires `jsonschema` and `PyMuPDF`).
