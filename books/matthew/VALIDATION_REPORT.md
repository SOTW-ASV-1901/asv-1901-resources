# Matthew | ASV 1901 release validation

**Status: PASS.** This standalone book release contains 28 chapters and **1,068 main-text verses** across **1,071 traditional numbering positions**. The original ASV 1901 printed edition omits 17:21, 18:11, and 23:14 from the running main Scripture text; it preserves their variant readings in the printed textual apparatus. Their absence is explicitly documented under `verse-omissions.json`, and no canonical main-text verse was fabricated.

Both digital text sources agree substantively apart from 19 documented typographical differences (historic æ ligatures and small capitals). These were checked against the original print and reconciled in the derived data. The original witness files were preserved unchanged. All **108** supplied-word italic spans agree between witnesses.

The included **35 original historical pages** are original source PDF pages **976–1010**: a Matthew-associated historical map before the book and 34 Scripture pages, corresponding to printed Matthew New Testament pages 1–34. All 35 pages passed exact embedded-image-stream and placement comparisons; six selected pages passed full rendered-pixel comparisons at low zoom. The page index covers all 1,068 main-text verses and identifies 29 page-spanning verses. The PDF volumes and all derived data rebuilt byte-identically.

JSON schemas, reader JavaScript syntax, local HTTP loading, input hashes, manifest hashes, and repository-relative installation paths were checked. This is *not* exhaustive character-by-character print proofreading, and live hosted browser interactions were not tested. No speculative Strong’s word alignments are imported. Source witness independence has not been established.

Installation is additive: upload the prepared `books` and `data` folder trees to the repository root. No prior files need replacement.
