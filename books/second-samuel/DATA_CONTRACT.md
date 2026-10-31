# ASV1901 2 Samuel data contract v1.0.0

- `2SA.c.v` is the stable biblical reference identity; `ASV1901:2SA.c.v` identifies this edition's verse. IDs do not depend on GitHub URLs.
- `data/asv1901/second-samuel/chapters/01.json` through `24.json` contain all **695 verses**, preserving **76 translator-supplied italic spans** as `kind: supplied`, separate from normal `kind: text` spans.
- Original source PDF pages **338–366** correspond to printed pages **304–332**, 29 consecutive physical Scripture pages. Two original full-page facsimile PDF volumes preserve those pages without rewriting or rasterizing them.
- **27 verses** cross two consecutive Scripture pages, including `2SA.18.3` (PDF pages 356 and 357). `first_verse` is the physically present verse, including a continuation from the preceding leaf, while `running_head_first_verse` retains the original printed heading for historical comparison.
- Historical page boundaries are checked at page and chapter level, not by inspecting every individual printed character. A scan-to-pixel or word-level alignment was neither required nor attempted.
- Digital English sources agree on all 695 verses after formatting whitespace normalization and agree on italic span content. Their independence is not established and must not be presumed.
- No unverified original-language/Strong's alignment has been imported. Future word indexes must use separately validated evidence and versioned schemas.
