"""Importers turn external sources into canonical data files.

Rules of the road (see docs/data-sources.md):
- importers READ external repositories/APIs and WRITE data/ files, stamping
  the exact revision of what they read into the provenance fields;
- importers must be re-runnable and deterministic for a pinned source revision;
- raw downloads/caches never enter git — only the distilled canonical records.
"""
