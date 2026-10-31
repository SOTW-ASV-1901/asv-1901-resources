# 1 Kings | Historical and technical verification report

- All **22 chapters and 816 verses** are present in order. The English-only USX and comparison USFM agree on verse wording once layout whitespace is normalized. Their underlying digital-transcription independence has not been established.
- **84 supplied-word italic spans** agree between both digital sources; italics are retained as structural data, not merely HTML styling.
- The original 1901 scan contains **33 original printed Scripture pages**, source PDF pages **367–399**, printed pages **333–365**. All page openings and chapter transitions are indexed. **27 verses** cross physical page boundaries, including `1KI.18.32` on pages 392 and 393. The 33 pages contain no interleaved maps.
- Historical PDFs preserve the whole original page content in two volumes. Original image stream and rendered-page parity are independently checked and reported in `VALIDATION_REPORT.json`.
- The complete package has versioned schemas, source and rights records, SHA-256 inventories, and additive path checks against earlier book packages.
- **Limits:** chapter-level historical verification does not equal character-by-character visual certification. Related digital witnesses may contain shared errors. No Strong's or Hebrew alignment is accepted; official hosted-browser test was not performed.

## Independent final checks

- All **33 original historical pages** were compared with the extracted PDF volumes for matching dimensions, embedded image streams, and rendered pixels. **PASS**.
- All **84 supplied-word italic spans** were independently parsed from the comparison USFM and matched to the structured USX-derived Scripture data. **PASS**.
- Byte-identical reproduction of all derived chapter files, page index, and historical PDF volumes from locked sources. **PASS**.
- Eight local HTTP resource paths loaded with matching SHA-256 bytes, including the optional inspection reader and both PDF volumes. **PASS**.
- ZIP integrity, individual file SHA-256s, all 816 verse lookups, and zero filename collisions with ten earlier packages. **PASS**.
- Live hosted-browser navigation was not tested; browser-specific `#page` rendering is not guaranteed.
