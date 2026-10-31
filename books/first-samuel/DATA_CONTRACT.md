# ASV1901 1 Samuel data contract v1.0.0

- `1SA.c.v` is a stable Scripture reference; `ASV1901:1SA.c.v` identifies the edition's verse text. Both are independent of host URLs.
- Chapter JSON files under `data/asv1901/first-samuel/chapters/01.json` through `31.json` contain **810 verses**, including **80 translator-supplied italic spans** recorded as `kind: supplied`, separate from `kind: text`.
- Original source pages **300–337** include **34 printed Scripture pages** (printed numbers **270–303**), two intact historical maps and their two blank reverse pages. The index preserves all 38 leaves in their physical order.
- **32 verses** are indexed on two Scripture pages, including `1SA.8.9` (306 and 309 across map 307–308) and `1SA.23.10` (326 and 329 across map 327–328).
- The physical first verse is distinguished from printed running headers. Chapter-level historical page inspection is documented and **not** an exhaustive glyph-by-glyph audit.
- The two digital transcriptions disagree at `1SA.13.1` and `1SA.14.49`. Both were checked against print, including an unambiguous unbroken use of `Malchi-shua` in the original source at `1SA.31.2`.
- Original print and supplied digital source hashes and the preserved transcription files establish provenance. Historical scans are never rewritten to match derivative text.
- The experimental original-language/Strong's data carried in the comparison USFM is not verified or imported. New schema versions must be explicit and preserve old verse IDs.
