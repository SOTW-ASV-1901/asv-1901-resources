# Additive Joshua upload to ASV Foundation GitHub repository

Extract this ZIP locally. Open the target repository root, use **Add file → Upload files**, and drag both extracted `books` and `data` folders onto the upload surface, preserving nested paths. This creates `books/joshua/`, `data/asv1901/joshua/`, and `data/asv1901/catalog-joshua.json`, without deleting any unrelated existing paths. Do not copy an outer ZIP-name directory or upload the ZIP file itself.

Use `python3 books/joshua/scripts/validate_release.py .` at repository root to independently validate the installed files. `books/joshua/site/index.html` is a QA reader, not a central website. Relative resource requests require serving via HTTP(S) instead of `file://`. GitHub Pages publication is separate and not automatically established by this upload.

Do not overwrite Genesis, Exodus, Leviticus, Numbers, Deuteronomy, or shared foundation runtime. No direct production changes are made by the package builder.
