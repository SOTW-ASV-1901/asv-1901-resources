# ASV 1901 Exodus | Independent Single-Book GitHub Installation

This is a **book-only upload**, not a replacement of the repository's homepage or any other book.
The paths inside the ZIP are already **relative to the repository root**; do not put the ZIP's filename
or a second enclosing folder into your GitHub repository. Do not copy these files to the repository
root as a flat list.

## Install manually, one book at a time

1. **Extract this ZIP locally**. GitHub does not unpack a ZIP into the repository for you.
2. Open or clone the *separate ASV1901 Foundation* repository locally (GitHub Desktop is suitable).
3. From the extracted package, merge the two top-level folders `books/` and `data/` into the
   matching repository-root folders, **preserving their contents and subdirectories**.
   GitHub Desktop will then show the added book-specific files; commit and push.
   Alternatively, drag the two folders into GitHub's repository-root **Add file → Upload files**
   page in the browser, keeping the directory structure.
4. Do not replace the entire existing `books/` or `data/` folder: **merge the new contents**.
5. Pages should publish from `main` and `/(root)`; visit `books/exodus/` after deployment.
   Your foundation's root homepage is maintained separately and is never overwritten by book ZIPs.
6. To verify after extraction in a repository checkout, run:
   `python books/exodus/scripts/validate_release.py .`

## Paths the book adds

- `books/exodus/`: reader, original source witnesses, build inputs, schemas, scripts, reports, and manifest.
- `data/asv1901/exodus/`: all verse data and historical page/PDF facsimile resources.
- `data/asv1901/catalog-exodus.json`: per-book catalog descriptor (unique name).

**Do not upload the full original 135 MB source PDF to GitHub Pages.** The book contains its own
small whole-page, checksum-verified historical volumes. No GitHub edit or deployment was made by this release.
