# 1 Chronicles | Additive GitHub installation

Extract the ZIP. From the root of your ASV resource repository, use **Add file → Upload files** and drag in only the extracted `books` and `data` directories, preserving their internal paths. Do not upload the ZIP itself or create an extra enclosing folder.

This release adds only `books/first-chronicles/`, `data/asv1901/first-chronicles/`, and `data/asv1901/catalog-first-chronicles.json`. No earlier book files, shared homepage, or master catalog are included.

Run `python3 books/first-chronicles/scripts/validate_release.py .` from the repository root. It needs `jsonschema` and `PyMuPDF`. Per-book browser inspection is optional; the official reader should use a controlled PDF renderer rather than depend on browser-specific PDF `#page=` fragments.
