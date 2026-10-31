# Deuteronomy | ASV 1901 foundation release

This is the fifth book-level ASV 1901 data release. It installs separately from Genesis, Exodus, Leviticus, and Numbers and does not add or replace the ASV Foundation's root site or catalogs for other books.

- `books/deuteronomy/`: source witnesses, proofing inputs, build/validation scripts, release manifest, an optional book-specific read/Compare demonstration, and source records.
- `data/asv1901/deuteronomy/chapters/`: 34 full Scripture chapter JSON files, preserving the 75 supplied-word italics as structured spans.
- `data/asv1901/deuteronomy/page-index.json`: first/last actual verse on each original physical page, ordered correctly across page-spanning verses.
- `data/asv1901/deuteronomy/facsimile/`: 39 unchanged whole scanned Scripture pages, split into two PDF volumes.
- `data/asv1901/catalog-deuteronomy.json`: discoverable Deuteronomy book metadata; not the deferred multi-book master catalog.

The historical master PDF is not in this release. To validate in a repository checkout: `python books/deuteronomy/scripts/validate_release.py .`. Python packages `pymupdf` and `jsonschema` are required.

The optional reader at `books/deuteronomy/` is a demonstration resource, **not a separate ASV foundation homepage**. The central Servants of the Way application is maintained independently.
