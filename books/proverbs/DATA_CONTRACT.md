# ASV1901 Proverbs book data

- Canonical verse ID: `PRO.chapter.verse`.
- Edition-qualified ID: `ASV1901:PRO.chapter.verse`.
- One `chapters/NN.json` per chapter (31 total), following Matthew's 1.0.0 data shape.
- `spans[].kind = supplied` preserves translator-supplied italic words; normal spans use `text`.
- `page-index.json` references actual PDF page positions from the original 1901 scan; `volume_pdf_page` is the local page inside a split facsimile.
- `SOURCE_INVENTORY.json`, `RELEASE_MANIFEST.json` and `VALIDATION_REPORT.json` preserve source locks and release checks.
- No speculative Hebrew, Greek, morphology, or Strong's word mapping is imported.
- Plain text and historic facsimile are presented side by side. Historical footnotes remain in original source files/facsimiles; this release does not invent structured footnote equivalence.
