# ASV 1901 Deuteronomy | independent GitHub installation

**Upload only this book's ZIP, independently of Genesis, Exodus, Leviticus, and Numbers.** The ZIP's root contains `books/` and `data/` with proper repository-relative paths. Extract it on your Mac and upload these **two folders** into your ASV Foundation repository root using GitHub's **Add file → Upload files**; GitHub adds new files without removing other book files. Do **not** upload the zipped file itself or its enclosing folder.

The new paths are `books/deuteronomy/`, `data/asv1901/deuteronomy/`, and `data/asv1901/catalog-deuteronomy.json`. No previously used path or shared homepage is included. If a file of the same path unexpectedly exists, stop rather than overwrite it.

Post-install validation (with Python, jsonschema, PyMuPDF): `python books/deuteronomy/scripts/validate_release.py .` from the checkout root.

This data foundation is intended to serve the central Servants of the Way website and other consumer tools. A root website is not required. Publication through GitHub Pages, if configured, makes public JSON/PDF files addressable via HTTPS. This release makes no production changes or deployments.
