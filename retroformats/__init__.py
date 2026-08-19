"""retroformats: tooling for the edopro-retro-formats historical format framework.

Canonical data lives in data/ and formats/; this package validates it and
builds EDOPro-consumable assets into dist/. Standard library only, on purpose:
anyone with Python 3.10+ can run the toolchain with no installation step.
"""

__version__ = "0.1.0"

GENERATOR_NAME = f"edopro-retro-formats/{__version__}"
