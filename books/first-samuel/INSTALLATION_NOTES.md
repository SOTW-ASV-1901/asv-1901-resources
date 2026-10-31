# Install 1 Samuel (additive package)

Extract the ZIP. At the **root** of the ASV 1901 GitHub repository choose **Add file → Upload files** and drag only the package's `books` and `data` directories. Do not upload the ZIP itself.

The archive contains only `books/first-samuel/`, `data/asv1901/first-samuel/`, and `data/asv1901/catalog-first-samuel.json`. It does **not** overwrite Genesis, Exodus, Leviticus, Numbers, Deuteronomy, Joshua, Judges or Ruth. No root site/homepage or global master catalog is added.

Test locally after merging with `python3 books/first-samuel/scripts/validate_release.py .` (Python with jsonschema and PyMuPDF). Optional temporary site needs HTTP(S) hosting. Browser PDF fragments may not scroll reliably in every browser; official applications should use `page-index.json` and a controlled viewer.
