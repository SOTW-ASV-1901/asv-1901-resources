# Install 2 Samuel (additive one-book archive)

Extract this ZIP. At the **root** of the ASV GitHub repository select **Add file → Upload files**, then drag the extracted `books` and `data` folders to upload their contents. Do not upload the ZIP itself or nest an extra outer folder.

All files are under `books/second-samuel/`, `data/asv1901/second-samuel/`, or `data/asv1901/catalog-second-samuel.json`. Previously installed Genesis through 1 Samuel are not overwritten. No root `index.html` or global catalog is installed.

Check locally: `python3 books/second-samuel/scripts/validate_release.py .` (requires `jsonschema` and PyMuPDF). Individual browser PDF viewers may ignore the `#page` fragment; the future official reader should use the page index with a controlled PDF viewer.
