# Leviticus final verification scope

- 27 chapters and 859 verse records are present and sequential according to the expected per-chapter verse counts.
- All 859 verse strings agree between the supplied English-only USX and comparison USFM when layout whitespace is ignored. Their editorial lineage may overlap.
- All 58 supplied-word italic spans agree exactly by verse and English content between the two digital sources.
- Source print contains 32 consecutive Leviticus Scripture pages, original printed 97–128 (PDF pages 123–154). All page openings and verse transitions were inspected; 29 verses begin on one page and continue on the next.
- Original source-to-small-volume facsimile PDF raster parity passed on all 32 pages; original full 135 MB scan is not included.
- Full chapter and page index schema checks, file hashes, repository install paths and archive integrity are validated automatically.
- **Limit:** Chapter-level visual inspection is not an exhaustive character-by-character transcription audit. The hosted site interaction has not been tested in a live browser.

Additional checks: clean rebuild byte-exact across 31 data/PDF files, seven local HTTP resources returned successfully, reader JavaScript page matching tested for all 859 verses, and simulated three-book installation preserved all prior files.
