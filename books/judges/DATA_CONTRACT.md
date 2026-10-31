# ASV 1901 Judges data contract 1.0.0

- `JDG.c.v` identifies a canonical Scripture verse; `ASV1901:JDG.c.v` identifies its edition-specific text. These identities are independent of file URLs.
- `data/asv1901/judges/chapters/01.json` through `21.json` contain 618 ordered verse records. `spans` distinguish regular `text` from translator-supplied `supplied` italics (62 spans), not unverified Hebrew or Greek word alignments.
- `data/asv1901/judges/page-index.json` indexes all original source PDF pages 267–293 (printed pages 239–265); 25 verses occur on two original printed pages. Page numbering is 1-based, and the actual first verse is separate from a possibly misleading running head.
- Original full-page facsimiles are preserved in smaller PDFs without OCR overlays, cropping, or destructive re-rendering. The full 1901 scan is preserved and hash-referenced outside this ZIP.
- Both digital sources and printed edition can be traced through source inventories and build-inputs. Source differences (none in Judges after ignoring spacing) and scope-limited chapter checks are documented. Strong's tagging in the USFM is not accepted as validated word alignment.
- Schema version 1.0.0 is compatible with preceding ASV books, and later schema evolution must remain explicit and versioned.
