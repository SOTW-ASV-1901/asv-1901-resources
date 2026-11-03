# Proverbs | ASV 1901 release validation

**Source-verified and internally validated standalone release.** 31 chapters; **915** Scripture main-text verses (no missing verse positions in either digital witness); **209** translator-supplied italic spans; **395** upstream USX footnote elements retained in the byte-preserved witness. The first verse is PRO.1.1 and the last is PRO.31.31.

Both original digital archives match the SHA-256 values recorded when Matthew was built. The complete original scanned Bible PDF also matches Matthew's historical source hash byte-for-byte. Original source PDF pages **671–701** correspond to printed Proverbs pages **629–659**. There are **31** original facsimile pages split across **two** PDF volumes. All 915 verses are mapped, including eight verses that span two original pages.

**Print-reconciled differences.** Two substantive orthographic differences between the digital witnesses are documented in `build-inputs/source-differences-resolved.json`. PRO.14.10 retains `inter-meddle` from the primary USX with explicit uncertainty about the print's line-break hyphen. PRO.27.1 uses `to-morrow`, supported by the comparison USFM and unbroken usage in the same 1901 printed edition (PRO.3.28). Original witness bytes remain unchanged.

**Testing:** JSON schemas, canonical verse identities, chapter counts, supplied italics, declared source hashes, release-manifest file hashes, complete physical-page numbering, source image bytes and placements for all 31 pages, and pixel-identical renders on six representative printed pages were verified. The reader's JavaScript parses successfully and its relative resources are locally addressable via HTTP. PDF volumes rebuild deterministically from the same source scan.

**Important limitations:** This is not exhaustive character-by-character comparison of the 1901 printing to every digital verse; the independence of the two digital witnesses is not established; a hosted browser/production site interaction test has not been completed; and unverified Strong's English-word alignments were not imported. Historical footnotes remain accessible in the source and facsimile, not as an invented structured notes layer.

**Installation:** Add only the new Proverbs paths. This package does not change GitHub, any existing book, or the player.
