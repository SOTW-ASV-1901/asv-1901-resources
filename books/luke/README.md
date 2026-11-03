# Luke | American Standard Version (1901)

**Servants of the Way | Book 42 | standalone, additive, original-source-locked foundation**

Luke contains **24 chapters**, **1,149 ASV 1901 main-text verses** and **1,151 traditional numbering positions**, including **two positions absent from running text**. The complete book uses one original historical map (source PDF page **1036**) and **36 original printed Scripture pages** (source PDF pages **1037–1072**, printed New Testament pages **57–92**). No PDF images were recreated or redrawn. The whole original parent scan is hash-pinned but not bundled.

## Apparatus must not become verse text

The printed ASV 1901 excludes **Luke 17:36 and Luke 23:17** from its main running text, but contains their readings in the historical apparatus. The comparison USFM source includes both as normal verses. This release retains their source notices separately and does **not** fabricate ASV main-text verses. Luke **22:43–44**, **23:34**, **24:12** and **24:40** appear in the 1901 running Scripture text, although historical notes express manuscript uncertainty. Luke 24:51–52 also carries manuscript-specific phrase notes. Selected cautionary notices are in `data/asv1901/luke/textual-apparatus.json`, and all original notes remain in the original witnesses and printed facsimile pages.

## Sources and fidelity

The original 1901 printing is the edition authority. The unchanged English-only USX file supplies baseline verses and italicized translator-supplied spans; the unchanged USFM file is an independent comparison input in the build, **not proven to be an independently originated transcription**. The two differ in 26 typographic locations (historic ligatures and small capitals) and two omitted positions. All **209** supplied-word USX spans were checked against the **208** USFM supplied-word runs; one verse divides a single USFM run into two USX spans separated by plain whitespace. Printed small capitals are projected as uppercase at Luke 1:31, 2:21, and 23:38; original source witnesses are unchanged. Text accuracy is **not certified by exhaustive character-by-character collation** of all 36 printed pages.

Original physical page openings, endings and verse carryovers were independently indexed. Each available main-text verse has a page comparison, including original margins and footnotes. Historical map preservation is physical, not a map-geolocation claim. The book reader uses JSON and local PDF URLs and should be tested again in GitHub hosting after installation. Unverified English-to-Strong's alignments from third-party files were deliberately excluded.

See `VALIDATION_REPORT.json`, `INDEPENDENT_AUDIT.json` and `RELEASE_MANIFEST.json` for precise checks, counts, and file hashes.
