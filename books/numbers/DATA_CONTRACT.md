# ASV 1901 Numbers data contract 1.0.0

- `NUM.c.v` is a stable Scripture reference identity and `ASV1901:NUM.c.v` an edition-specific verse identity. Identifiers are separate from publication URLs.
- `data/asv1901/numbers/chapters/01.json` through `36.json` contain the 1288 verses in ordered `spans` (`kind: text` or `kind: supplied`). The latter correspond to the **110 translator-supplied italic spans**, not to independently verified Hebrew word alignments.
- `data/asv1901/numbers/page-index.json` maps verses to whole original print pages in physical PDF order. There are **37 verses spanning two physical Scripture pages**. Source-PDF pages 155 through 199 correspond to original printed pages 129 through 173. There are no interleaved map sheets inside this selected Numbers extent.
- Printed running-head verse references and physical first-verse references are kept separately: some pages start by continuing the previous verse. Whole original PDF pages are used, with no verse-to-pixel mapping and no destructive rasterization.
- Original digital sources, provenance, and validation input decisions are preserved under `books/numbers/`; the owner's 135 MB historical master scan is not copied into the public ZIP.
- The USFM's Strong's markup is **not verified** and is not imported as a canonical lexicon, language alignment, or theological assertion. Paragraph markers are reader formatting, not proof of exact original typography. Corrections to derived data need source evidence and versioned audit history.
- The Numbers book package uses the same chapter schema version and verse-ID strategy as Genesis, Exodus, and Leviticus. A shared 66-book catalog is deferred; this book supplies only its unique per-book metadata.
