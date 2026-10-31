# ASV 1901 Leviticus data contract 1.0.0

- `LEV.c.v` is a stable Scripture reference identity and `ASV1901:LEV.c.v` an edition-specific verse identity. Identifiers are separate from publication URLs.
- `data/asv1901/leviticus/chapters/01.json` through `27.json` contain the 859 verses in ordered `spans` (`kind: text` or `kind: supplied`). The latter correspond to the **58 translator-supplied italic spans**, not to independently verified Hebrew word alignments.
- `data/asv1901/leviticus/page-index.json` maps verses to whole original print pages in physical PDF order. There are **29 verses spanning two physical Scripture pages**. Source-PDF pages 123 through 154 correspond to original printed pages 97 through 128. There are no interleaved map sheets inside this selected Leviticus extent.
- Printed running-head verse references and physical first-verse references are kept separately: some pages start by continuing the previous verse. Whole original PDF pages are used, with no verse-to-pixel mapping and no destructive rasterization.
- Original digital sources, provenance, and validation input decisions are preserved under `books/leviticus/`; the owner's 135 MB historical master scan is not copied into the public ZIP.
- The USFM's Strong's markup is **not verified** and is not imported as a canonical lexicon, language alignment, or theological assertion. Paragraph markers are reader formatting, not proof of exact original typography. Corrections to derived data need source evidence and versioned audit history.
- The Leviticus book package uses the same chapter schema version and verse-ID strategy as Genesis and Exodus. A shared 66-book catalog is deferred; this book supplies only its unique per-book metadata.
