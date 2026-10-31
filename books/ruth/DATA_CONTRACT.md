# ASV 1901 Ruth data contract 1.0.0

- `RUT.c.v` identifies a canonical Scripture reference, and `ASV1901:RUT.c.v` its edition-specific content. IDs are independent of publication URLs.
- Chapter JSON files `data/asv1901/ruth/chapters/01.json` through `04.json` contain all 85 verses. Ordered spans distinguish ordinary English (`kind: text`) from translator-supplied italics (`kind: supplied`), five spans total. They are not Hebrew/Greek word alignments.
- The `page-index.json` records original printed pages 266–269 (original scan PDF pages 294, 297, 298, 299). PDF pages 295–296 are a historical Canaan/map page and blank reverse, preserved in original physical order.
- Three verses continue onto a later Scripture page: `RUT.1.22` (294→297), `RUT.2.22` (297→298), and `RUT.4.5` (298→299). Original running heads are indexed separately from actual page-opening verse text.
- The original 1901 scan is retained and SHA-256 referenced but not distributed whole in the small GitHub ZIP. The single extracted volume retains complete original scanned pages without rasterization/cropping.
- Source files and verification inputs are retained within `books/ruth/` for repeatable reconstruction and future evidence-based correction. The USFM's experimental Strong's tagging has not been adopted as authoritative word alignment.
- Schema v1.0.0 is compatible with earlier ASV book releases. Future changes require explicit versioning, not silent redefinition of existing IDs.
