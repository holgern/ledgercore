"""Tests for the build-generated version metadata."""

from __future__ import annotations

import re

import ledgercore


def test_package_exposes_version() -> None:
    assert hasattr(ledgercore, "__version__")
    assert isinstance(ledgercore.__version__, str)
    assert ledgercore.__version__


def test_version_in_all() -> None:
    assert "__version__" in ledgercore.__all__


def test_version_module_importable() -> None:
    from ledgercore import _version

    assert _version.__version__ == ledgercore.__version__
    # setuptools_scm also exposes the tuple form.
    assert isinstance(_version.__version_tuple__, tuple)


def test_version_is_pep440ish() -> None:
    # Accept release (0.2.0), dev (0.2.0.dev1 / 0.1.dev1), and
    # dirty/git-suffixed forms produced by hatch-vcs / setuptools_scm.
    # The release segment may have two or three numeric components.
    pattern = r"^\d+(\.\d+)*([abrc]\d+|\.dev\d+)?(\+[\w.]+)?$"
