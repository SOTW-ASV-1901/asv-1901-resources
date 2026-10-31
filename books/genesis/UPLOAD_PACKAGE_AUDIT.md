# Genesis per-book repository upload repackaging | 2026-10-31

- Package is additive and book-scoped. Repository top-level paths are `books/genesis/` and `data/asv1901/genesis/`. 
- The original digital chapter JSON, page-index JSON, source witnesses, evidence records, and original-print facsimile PDFs are byte-for-byte identical to the accepted source ZIP.
- Scripture and historical source accuracy claims remain unchanged from the original validation report.
- Release manifest and book-specific documentation updated for new repository-relative paths.
- Builder script's root default and per-book manifest target corrected to avoid accidental hashing of or modifying other books in a 66-book repository.
- Genesis reader base path adjusted from `../data/...` to `../../../data/...` to load from `books/genesis/site/`.
- Genesis original page-boundary repair and 45 two-page verses preserved.
- No repository root `index.html`, shared manifest, central configuration, other book paths, or application files are included or altered.
