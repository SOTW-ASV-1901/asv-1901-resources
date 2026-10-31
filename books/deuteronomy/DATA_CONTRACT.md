# ASV 1901 Deuteronomy data contract 1.0.0

- `DEU.c.v` is a stable Scripture reference identity and `ASV1901:DEU.c.v` an edition-specific verse identity. Identifiers are separate from publication URLs.
- `data/asv1901/deuteronomy/chapters/01.json` through `34.json` contain the 959 verses in ordered `spans` (`kind: text` or `kind: supplied`). The latter correspond to the **75 translator-supplied italic spans**, not to independently verified Hebrew word alignments.
- `data/asv1901/deuteronomy/page-index.json` maps verses to whole original print pages in physical PDF order. There are **36 verses spanning two physical Scripture pages**. Source-PDF pages 200 through 238 correspond to original printed pages 174 through 212. There are no interleaved map sheets inside this selected Deuteronomy extent.
- Printed running-head verse references and physical first-verse references are kept separately: some pages start by continuing the previous verse. Whole original PDF pages are used, with no verse-to-pixel mapping and no destructive rasterization.
- Original digital sources, provenance, and validation input decisions are preserved under `books/deuteronomy/`; the owner's 135 MB historical master scan is not copied into the public ZIP.
- The USFM's Strong's markup is **not verified** and is not imported as a canonical lexicon, language alignment, or theological assertion. Paragraph markers are reader formatting, not proof of exact original typography. Corrections to derived data need source evidence and versioned audit history.
- Print-verified derived-text changes: DEU.3.19 removes an extraneous comma before a parenthesis; DEU.28.58 preserves the original small-capitals text as uppercase characters. The USX and USFM source files are untouched.
- The Deuteronomy book package uses the same chapter schema version and verse-ID strategy as Genesis, Exodus, Leviticus, and Numbers. A shared 66-book catalog is deferred; this book supplies only its unique per-book metadata.
