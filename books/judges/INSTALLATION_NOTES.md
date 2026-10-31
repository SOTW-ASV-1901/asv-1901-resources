# Additive Judges upload to ASV Foundation

Extract this archive, then from the **root** of the ASV Foundation GitHub repository choose **Add file → Upload files**. Upload the extracted `books` and `data` folders (not the outer named ZIP folder and not the ZIP itself). GitHub adds their new book-specific paths without deleting existing Genesis–Joshua resources.

Verify locally with `python3 books/judges/scripts/validate_release.py .` from the repository root. The optional `books/judges/site/index.html` reader uses relative HTTP(S) requests; it is not the shared SOTW website. Hosted interactive-browser verification is a separate UI matter.

No direct GitHub edits or deployment are included in this release.
