# ASV 1901 Song of Solomon | Independent validation scope

The complete book contains **8 chapters, 117 verses and 60 structured supplied-word italic spans**. All verse numbers and italics agree between the English-only USX and the comparison USFM. **Two digital verse discrepancies** were independently checked in the original 1901 printing and the derived verse data was corrected accordingly:

- **Song 1:5:** Original printed page 669 (source PDF 711) uses “O ye”, not “Oh ye”.
- **Song 8:10:** Printed page 674 (PDF 716) has a colon after “thereof”. This word is supplied and italicized in both witnesses. The colon is inserted in an adjacent *nonitalic text span* without changing the supplied-word markup.

The exact digital source files are preserved, unchanged, under `sources/`. The 1901 printing is checksum-locked outside this release. Printed Scripture occurs on source PDF pages 711–716, printed pages 669–674. All six pages are copied as original whole pages into one compact PDF volume. Original embedded image digests, dimensions and positions and independently rendered 1× pixels were checked page by page against the source. Verse `SNG.7.12` continues from printed page 673 onto 674 despite the page 674 running head beginning at 7:13. All 117 verses are indexed.

The independent check includes source word and italic agreement after documented original-print corrections, JSON schema validation, manifest hashes, exact page-image preservation, deterministic rebuilds of JSON/PDF, reader JavaScript syntax, local HTTP retrieval and ZIP integrity. The ZIP contains only three additive Song-of-Solomon path prefixes and does not overwrite any prior book or shared catalog.

**Limitations:** Not exhaustive letter-by-letter collation against the 1901 printing; independence of the two digital witnesses is not established. Hosted GitHub Pages interactivity was not tested. No unverified lexical or Strong’s mapping is imported.
