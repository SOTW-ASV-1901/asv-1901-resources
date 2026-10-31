# Servants of the Way | ASV 1901 Genesis Foundation Release

**Status:** Assembled from the user-provided original 1901 print PDF and two complete digital Genesis transcripts. Structural validation passed; see `VALIDATION_REPORT.md` for exactly what was and was not checked. No GitHub repository was modified.

## What is here

- `books/genesis/site/index.html`: chapter/verse Bible reader and original-print Compare interface; source physical pages browse in original order, including historical maps and blank map backs.
- `data/asv1901/genesis/chapters/01.json` through `50.json`: 1,533 verses with stable `GEN.C.V` references and separate `ASV1901:GEN.C.V` edition identifiers. `spans[].kind="supplied"` displays original translator-supplied italics. Poetry line breaks are preserved as text newlines where encoded by USX.
- `data/asv1901/genesis/page-index.json`: 52 Scripture pages and eight map/interleaf pages, with inclusive first/last Scripture verse boundaries and source PDF page numbers. All 1,533 verses map to the original printing; 45 span two Scripture pages, including three that cross interleaved historical maps. Compare opens both pages in original order and offers separate browse-all navigation.
- `data/asv1901/genesis/facsimile/`: three **whole-page** PDF volumes extracted without re-rasterization from the supplied 1310-page original.
- `sources/`: primary English-only USX including its original footnote apparatus, and the **comparison-only** USFM. The USFM includes embedded Strong's links that are **not verified** and are **not imported** as authoritative lexical mappings.
- `build-inputs/`: source-page index, chapter evidence record, and six documented print-checked digital differences.
- `scripts/`, `schemas/`: builder, validator and documented machine data formats.
- `RELEASE_MANIFEST.json`: full file-level SHA-256 inventory and input source hashes.

## Preview / upload

Keep the directory structure unchanged. For local preview, run `python3 -m http.server 8000` from the directory containing `books/genesis/index.html` and open `http://localhost:8000/`. Simply opening the HTML via a `file://` URL will not allow chapter fetches in many browsers.

Once you create the separate ASV GitHub foundation, upload the **contents** of this ZIP at that repository root. Enable GitHub Pages from root of the selected branch. The landing page redirects to the Genesis reader. The old central Bible Foundation repository is not to be overwritten by this package.

## Architecture for growth

The JSON chapter files are *reader projections*, not an all-purpose master knowledge database. Stable reference and edition IDs do not depend on the folder structure or URL. External lexicons, Strong's records, other translations, commentaries, and future agents can link through later versioned contracts, with rights and evidence tracked separately. Church-specific interface choices never modify these canonical source records.

## Historic source boundaries

The entire 135 MB original scanned PDF is not inside the ZIP. Its SHA-256 is recorded in `RELEASE_MANIFEST.json`, and the Genesis physical pages are reproduced in the three facsimile PDFs. The original PDF should remain immutable in the owner's separate archive.
