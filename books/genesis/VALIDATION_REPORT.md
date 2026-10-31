# Genesis final validation report | ASV1901

**Result: PASS for complete Genesis source-data coverage, digital cross-comparison, italics preservation, source-page mapping, document-splitting and release-file integrity, subject to disclosed limits.** This is not a claim of every-character visual certification.

## Verified results

- **50 chapters / 1,533 verses** present, correctly numbered and nonempty. Source IDs are unique. The separate digital English-only USX and eBible-derived USFM both contain 1,533 Genesis verses.
- **60 translator-supplied italic spans** are present in the primary USX and exactly the same 60 spans appear as `\add` spans in the independent USFM text witness. Italics survive as `kind: supplied` within per-verse data, and the reader displays them in italic styling.
- **Six substantive digital wording/punctuation differences** remained after whitespace-only differences were ignored. All six were inspected against actual original printed pages; the primary USX matches the original printing in each. The per-verse reasons and physical source PDF page numbers are recorded in `build-inputs/source-differences-resolved.json`.
- **All 1,533 verses** are covered by inclusive first and last verse ranges on **52 original Scripture-bearing pages**. **45 verses span two physical Scripture pages**, including **3 across historical maps** (GEN.10.8, GEN.19.30, GEN.37.7). Genesis occupies supplied source PDF pages **17–76**, with **four historical maps and four historical blank/map-back pages** in correct order. These are all included and classified. Original-source page numbers are distinct from printed Bible page numbers (1–52).
- **Three small complete-page PDF volumes** were made without reconstructing, cropping, or replacing the original scanned page content. PDF pages and 10 sampled rendered source-vs-split page images match exactly (source pages 17, 18, 19, 27, 44, 49, 61, 65, 75, 76).
- **Schemas validated** for all 50 JSON chapter files and the page index. **HTTP retrieval succeeded** for home page, reader HTML, first and last chapters, page index and a PDF volume. The reader JavaScript passes the Node.js syntax checker.
- All packaged files have SHA-256 hashes in the release manifest. The ZIP archive itself is tested for CRC integrity and the package is not installed or deployed automatically.

## Targeted refined-boundary correction

The historical page-index first-reference values were corrected wherever the page begins with the trailing text of the preceding verse. Printed running-head first-reference values are retained separately. Both Bible chapters and original PDF volumes are byte-identical to the previous Genesis release. The updated Compare reader presents the two matching Scripture pages in original PDF order and supports separate browsing of all 60 source pages, including maps and versos. The complete per-page audit and all two-page verse pairs are recorded in `build-inputs/page-boundary-evidence.json` and `build-inputs/spanning-verses.json`.

## Regression rebuild results

A fresh production rebuild reproduced all 50 Scripture chapter JSON files and all 60 page-index records. The reconstructed historical PDFs are identical to the original release PDF volumes after excluding the PDF generator’s volatile document `/ID` metadata. The unchanged original facsimile PDFs remain in this ZIP, retaining their original SHA-256 values. The original-image page transitions at GEN.10.8, GEN.19.30, and GEN.37.7 were also visually checked.

## Verification scope and limitations

The source check is the agreed *chapter-level* verification approach: each chapter's physical page coverage and chapter boundaries were checked against the uploaded original scan, including original Genesis headings and page continuity, without a character-by-character proof of every word. The six substantive witness variants were visually inspected against the printed original. The two digital transcriptions agree on the italic spans; **an independent visual inspection of all 60 italic occurrences was not performed**.

A real Chromium automation run was attempted, but this hosted environment blocks local and file URL navigation at the browser administrator level. Therefore an **interactive browser acceptance test on GitHub Pages remains unverified**; this is reported rather than silently passed. Static JavaScript syntax, HTTP serving and the full data validation passed. The Chrome PDF viewer's `#page=` fragment is browser-dependent; a direct PDF link is provided.

The comparison-only USFM contains Strong's word-label metadata. That metadata appears unrelated to trustworthy word-alignment certainty, so **none of the USFM Strong's tags are imported as verified Greek/Hebrew mappings**. The compressed SWORD archive was retained only as an uploaded candidate; it was not counted as an independent witness. Original historical notes and cross-references remain available in the source USX and facsimile rather than being reclassified as Bible verse wording.

The original full Bible PDF was supplied as a 1,310-page working file and remains external to the release ZIP. Its SHA-256 and the extracted page PDF hashes are recorded in `RELEASE_MANIFEST.json`.
