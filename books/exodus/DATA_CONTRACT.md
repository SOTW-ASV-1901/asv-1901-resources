# ASV 1901 Exodus contract, compatible with Genesis v1.0.0

- `EXO.c.v` is a stable book/chapter/verse identity; `ASV1901:EXO.c.v` identifies edition-specific text. Never derive IDs from URLs.
- `data/asv1901/exodus/chapters/01.json` through `40.json` contain verses and ordered `spans` (`kind=text` or `supplied`). `supplied` spans render in italics and are structural data, not HTML markup. `paragraph_start` is a reader projection.
- Original page ranges in `page-index.json` map verse identifiers to complete original printed pages. Historical map and its blank verso are preserved. PDF volumes contain unchanged whole printed pages, not OCR coordinate annotations.
- Running-head references are stored independently from actual physical-page first verses; a page may begin with a continuation of the previous verse. Page order is the source order; when a verse belongs to multiple pages, show the lower PDF page number first. `printed_page` means the number printed in the historical ASV volume, distinct from `source_pdf_page` and `volume_pdf_page`.
- Typography corrections are recorded in `build-inputs/source-differences-resolved.json` and applied only to derived chapter data, never original archived digital sources.
- Source files and provenance are kept separate from data projections; all agent contributions should retain source citations and version history, with no silent replacement of text.
- The historic source PDF is outside this public package. This projection can migrate from GitHub Pages to other storage or database engines without changing canonical Scripture IDs.
- The comparison USFM contains exploratory Strong's numbering, which has not been validated and is not released as canonical word alignment.
