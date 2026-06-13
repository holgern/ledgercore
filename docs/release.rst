Release process
===============

This document describes how to build, validate, and publish a ``ledgercore``
release.

Prerequisites
-------------

Install build and validation tools:

.. code:: bash

   python -m pip install -e ".[dev,docs,release]"
   # or, equivalently:
   python -m pip install -e ".[dev]" && python -m pip install build twine

``ledgercore`` uses hatch-vcs for versioning. Installing or building the project
generates a gitignored ``ledgercore/_version.py`` that exposes
``ledgercore.__version__``; do not commit that file.
Direct source-tree imports fall back to ``0.0.0+unknown`` when that generated
module is absent.

Pre-release checklist
---------------------

1. Ensure all tests pass:

.. code:: bash

   python -m pytest -q

2. Ensure lint is clean:

.. code:: bash

   python -m ruff check .

3. Ensure type checking passes:

.. code:: bash

   python -m mypy ledgercore

4. Ensure formatting and documentation are clean:

.. code:: bash

   python -m ruff format --check .
   python -m sphinx -W -b html docs docs/_build/html

5. Ensure a ``LICENSE`` file is present and ships in the built artifacts:

.. code:: bash

   test -f LICENSE

6. Ensure examples run from the source tree with ``PYTHONPATH=. python examples/*.py``
   (or after installing the package).

Building
--------

.. code:: bash

   python -m build

Builds from a non-git source archive are supported when the intended version is
provided explicitly:

.. code:: bash

   SETUPTOOLS_SCM_PRETEND_VERSION=0.2.0 python -m build

This produces ``dist/ledgercore-<version>.tar.gz`` and
``dist/ledgercore-<version>-py3-none-any.whl``.

Validating the distribution
---------------------------

.. code:: bash

   python -m twine check dist/*

Smoke testing (required release gate)
-------------------------------------

Install the built wheel into a clean virtualenv and run the smoke test. Use a
writable location for the venv (on some platforms ``/tmp`` is not writable):

.. code:: bash

   smoke_dir="$(pwd)/.smoke"
   rm -rf "$smoke_dir"
   python -m venv "$smoke_dir"
   "$smoke_dir/bin/python" -m pip install "$(echo dist/*.whl)"
   "$smoke_dir/bin/python" - <<'PY'
   from pathlib import Path
   import tempfile
   from ledgercore import __version__
   from ledgercore.ids import LedgerIdFormat
   from ledgercore.refs import parse_resource_ref
   from ledgercore.frontmatter import render_front_matter_text, split_front_matter_text
   from ledgercore.jsonl import load_jsonl_object_map, write_jsonl_objects
   from ledgercore.time import utc_now_iso

   assert isinstance(__version__, str) and __version__
   assert LedgerIdFormat(prefix="task").format(1) == "task-0001"
   assert parse_resource_ref("tl:task-0001").global_ref == "tl:task-0001"
   text = render_front_matter_text({"id": "task-0001", "flag": "no"}, "# Body\n", scalar_style="minimal")
   meta, body = split_front_matter_text(text)
   assert meta["id"] == "task-0001" and meta["flag"] == "no" and body == "# Body\n"
   with tempfile.TemporaryDirectory() as d:
       path = Path(d) / "rows.jsonl"
       write_jsonl_objects(path, [{"id": "a", "v": 1}, {"id": "b", "v": 2}])
       result = load_jsonl_object_map(path, key="id")
       assert not result.issues and set(result.rows_by_key) == {"a", "b"}
   assert utc_now_iso().endswith("Z")
   print("ledgercore smoke test passed")
   PY
   rm -rf "$smoke_dir"

Also verify the built artifacts ship the ``LICENSE`` file and the generated
``ledgercore/_version.py``:

.. code:: bash

   python - <<'PY'
   import glob, tarfile, zipfile
   wheel = glob.glob("dist/*.whl")[0]
   sdist = glob.glob("dist/*.tar.gz")[0]
   with zipfile.ZipFile(wheel) as z:
       names = z.namelist()
       assert any(name.endswith("LICENSE") for name in names)
       assert "ledgercore/_version.py" in names
   with tarfile.open(sdist) as t:
       names = t.getnames()
       assert any(name.endswith("/LICENSE") for name in names)
       assert any(name.endswith("/ledgercore/_version.py") for name in names)
   print("artifact check passed")
   PY

Publishing
----------

.. code:: bash

   python -m twine upload dist/*

Version policy
--------------

``ledgercore`` is pre-1.0. Public APIs are intended to be stable within the
0.2.x series, but breaking changes may still happen before 1.0.0 when needed
to keep the core API small and consistent.
