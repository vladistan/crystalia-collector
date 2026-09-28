"""Crystalia data model: generated LinkML classes plus the v2 behaviour package.

Observability contract (NFR-007): the package logs only through the
``crystalia_data_model`` logger, which carries a ``NullHandler`` so importing
the library never emits anything; consumers attach their own handlers.
"""

from __future__ import annotations

import logging
from importlib import resources
from pathlib import Path

from crystalia_data_model.__about__ import VERSION

__version__ = VERSION

logger = logging.getLogger("crystalia_data_model")
logger.addHandler(logging.NullHandler())

SCHEMA_NAME = "linkml_crystalia.yaml"


def schema_path() -> Path:
    """Return the on-disk path of the shipped LinkML schema.

    Resolved through ``importlib.resources`` so it works from an installed
    wheel and from a vendored copy alike.
    """
    ref = resources.files("crystalia_data_model").joinpath("schema", SCHEMA_NAME)
    with resources.as_file(ref) as path:
        return Path(path)


__all__ = ["SCHEMA_NAME", "__version__", "logger", "schema_path"]
