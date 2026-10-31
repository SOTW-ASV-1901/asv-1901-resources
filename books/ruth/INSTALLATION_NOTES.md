# Install Ruth into the ASV 1901 Foundation

Extract this ZIP. From your ASV Foundation repository **root**, choose **Add file → Upload files** and drag the `books` and `data` folders inside this package (not the ZIP itself). This creates only `books/ruth/`, `data/asv1901/ruth/`, and `data/asv1901/catalog-ruth.json` and does not delete or replace earlier books.

For an independent local check, run `python3 books/ruth/scripts/validate_release.py .` from the resulting repository root; requires Python with PyMuPDF and jsonschema. The optional `books/ruth/site/index.html` is served over HTTP(S) from GitHub Pages or another static host, not opened directly as a local file. Browser PDF fragment navigation is viewer-dependent. Future official reader integrations should use the `page-index.json` rather than depend on the temporary inspection UI.

No GitHub edits, deployment, or changes to the central Servants of the Way website were performed.
