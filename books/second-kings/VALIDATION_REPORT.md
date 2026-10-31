# 2 Kings | historical and technical verification report

- All **25 chapters / 719 verses** agree in the two digital witness sources after whitespace-only differences are disregarded. Digital source genealogical independence is not established.
- All **67 translator-supplied italic spans** agree and remain structurally recorded, with no invented original-language alignments.
- Original pages **400–435** span printed pages **366–397**, preserving **32 Scripture pages**, two historical maps and two blank reverse sides.
- **27 verses** traverse two printed Scripture pages. Some span historical map insertions, including `2KI.16.13` on source pages 420 and 423; `2KI.23.15` crosses pages 431 and 432 even though page 431's running header gives the misleading ending 23:13.
- The historical PDFs preserve whole physical pages. Their independent image-stream and rendered-page parity findings appear in `VALIDATION_REPORT.json`.
- Validation includes stable reference IDs, schemas, page-range lookups, source provenance, SHA-256 inventories, ZIP integrity, and additive repository path isolation.
- **Limits:** not an exhaustive per-character visual proof of the historical text; the digital witnesses may share source history; neither Strong's tagging nor Hebrew alignment is certified; live hosted browser testing remains outstanding.

## Independent final checks

- All 36 preserved PDF pages match the source scan's embedded image data and rendered image pixels in the independent PDF comparison.
- All 719 verses cross-match between the two digital witnesses; each of the 67 supplied-word spans agrees.
- All 25 chapter JSON files and the two PDF volumes rebuild byte-identically from the preserved inputs and chapter/page evidence.
- Eight book resources successfully loaded over local HTTP, including the reader, first and last chapter, page index, and both historical PDF volumes. JavaScript syntax and JSON schemas validate.
- Release ZIP CRC, SHA-256 manifest, and disjoint file paths versus all eleven earlier single-book releases pass.
- **Still outstanding:** hosted-browser interactive acceptance testing. The PDF `#page=` fragment in the optional inspection reader is browser-dependent; the final integrated reader should use the source-page index with a controlled PDF viewer.
