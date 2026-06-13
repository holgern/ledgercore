Storage helpers
===============

``ledgercore`` provides several storage primitives for safely reading and writing
structured files.

Atomic writes
-------------

Use ``atomic_write_text`` when replacing a file is expected:

.. code:: python

   from pathlib import Path
   from ledgercore.atomic import atomic_write_text

   atomic_write_text(Path("index.json"), "{}\n")

The write goes to a temporary file first, then ``os.replace`` atomically moves it
to the target. Parent directories are created automatically. Replacing an
existing file preserves its permission bits; a newly created file keeps the
private ``0600`` mode created by ``mkstemp``.

Use ``atomic_create_text`` when an existing file must not be overwritten:

.. code:: python

   from pathlib import Path
   from ledgercore.atomic import atomic_create_text

   atomic_create_text(Path("records/task-0001.md"), "---\nid: task-0001\n---\n")

This uses ``O_CREAT|O_EXCL`` and raises ``AtomicWriteError`` if the target already
exists.

Both functions support an optional ``fast_io_env_var`` parameter. When the named
environment variable is set, ``fsync`` is skipped for faster I/O on temporary
filesystems.

Front matter documents
----------------------

Front matter documents are Markdown files with a YAML header:

.. code:: text

   ---
   id: task-0001
   status: open
   ---
   # Task body here

Reading
~~~~~~~

.. code:: python

   from pathlib import Path
   from ledgercore.frontmatter import read_front_matter_document

   metadata, body = read_front_matter_document(Path("records/task-0001.md"))

The YAML block must be a mapping. ``metadata`` is always a ``dict``. ``body``
includes everything after the closing ``---`` delimiter.

For content already held in memory:

.. code:: python

   from ledgercore.frontmatter import (
       render_front_matter_text,
       split_front_matter_text,
       update_front_matter_text,
   )

   metadata, body = split_front_matter_text(text, missing="empty")
   text = update_front_matter_text(text, {"status": "ready"})
   text = render_front_matter_text(metadata, body, key_order=("id", "status"))

Parsing can preserve YAML timestamps as strings and quote template
placeholders. Rendering supports caller-defined key order and body modes.
Minimal scalar rendering accepts only simple alphanumeric, underscore, and
hyphen metadata keys and raises ``FrontMatterError`` for unsafe YAML keys.

For deterministic front matter without PyYAML's formatting choices:

.. code:: python

   text = render_front_matter_text(
       {"title": "Example", "tags": ["one", "two"], "empty": ""},
       "# Body\n",
       scalar_style="minimal",
       sequence_indent="  ",
       empty_string_style="double",
       remaining_key_order="sorted",
   )

The default ``scalar_style="pyyaml"`` preserves existing output. Minimal mode
supports strings, booleans, integers, nulls, and flat scalar sequences. The minimal
renderer quotes any string that is not a conservative safe plain scalar
(alphanumeric lead character followed by letters, digits, spaces, underscores,
dots, slashes, or hyphens) and any value that folds to a YAML boolean or null
token, so values such as ``- item``, ``*alias``, ``~``, ``no``, or ``2026-06-13`` round-trip
without producing invalid YAML or silently changing type. Use
``quote_template_placeholders="anywhere"`` to parse placeholders embedded in simple
unquoted scalar values.

Writing
~~~~~~~

.. code:: python

   from pathlib import Path
   from ledgercore.frontmatter import write_front_matter_document

   write_front_matter_document(
       Path("records/task-0001.md"),
       {"id": "task-0001", "status": "open"},
       "# Implement parser\n",
       body_mode="ensure-single-final-newline",
   )

``body_mode="ensure-single-final-newline"`` normalizes trailing whitespace in the
body. The default ``"preserve"`` writes the body as-is.

Iterating files
~~~~~~~~~~~~~~~

.. code:: python

   from pathlib import Path
   from ledgercore.frontmatter import iter_markdown_files, iter_source_files

   md_files = iter_markdown_files(Path("records/"))
   all_files = iter_source_files(Path("records/"), (".md", ".yaml"))

Both return sorted ``list[Path]``.

JSON store
----------

.. code:: python

   from pathlib import Path
   from ledgercore.jsonio import dumps_json, load_json_object, write_json

   path = Path("state.json")
   write_json(path, {"next": 4})
   state = load_json_object(path, missing="empty")
   compact = dumps_json(state, compact=True)

- ``load_json_object`` validates that the root is a JSON object.
- ``load_json_array`` validates that the root is a JSON array.
- ``write_json`` produces deterministic output: indent 2, sorted keys, final newline.
- ``dumps_json`` and ``write_json`` can change indentation, key sorting, ASCII
  escaping, compact separators, and final-newline behavior.
- All operations raise ``JsonStoreError`` on failure.

Both loaders accept ``missing="empty"`` to return an empty container only when the
file does not exist; an unreadable path that does exist (for example a directory,
or a permission error) raises ``JsonStoreError`` rather than being masked as empty.
``empty="empty"`` (the default) returns an empty container when the file is blank.

JSONL store
-----------

.. code:: python

   from pathlib import Path
   from ledgercore.jsonl import load_jsonl_object_map, write_jsonl_objects

   path = Path("records.jsonl")
   write_jsonl_objects(path, [{"id": 1}, {"id": 2}])
   result = load_jsonl_object_map(path, key="id", missing="empty")

``load_jsonl_object_rows`` retains each valid object's source line.
``load_jsonl_object_map`` indexes rows by a selected field and reports missing,
invalid, and duplicate keys in ``issues``. Duplicate policy can be ``"last"``,
``"first"``, or ``"error"``. Writes remain compact and deterministic.

YAML store
----------

.. code:: python

   from pathlib import Path
   from ledgercore.yamlio import load_yaml_object, write_yaml

   path = Path("config.yaml")
   write_yaml(path, {"records_dir": "records"}, sort_keys=True)
   config = load_yaml_object(path, missing="empty")

- ``load_yaml_object`` validates that the root is a YAML mapping.
- ``write_yaml`` produces block-style output with a final newline. Keys can be
  sorted on request.
- All operations raise ``YamlStoreError`` on failure.

Path safety
-----------

Path helpers enforce strict rules to prevent directory traversal:

.. code:: python

   from ledgercore.paths import validate_relative_posix_path

   validate_relative_posix_path("records/task-0001.md")  # ok
   validate_relative_posix_path("../etc/passwd")          # raises PathValidationError
   validate_relative_posix_path("/etc/passwd")            # raises PathValidationError

Rejected inputs include:

- Absolute paths (starting with ``/``).
- Paths containing ``..`` or ``.`` segments.
- Paths containing backslashes.
- Paths that resolve outside the base directory.

Config discovery
~~~~~~~~~~~~~~~~

.. code:: python

   from pathlib import Path
   from ledgercore.paths import locate_config, resolve_config_relative_path

   locator = locate_config(Path.cwd(), ("ledger.toml", ".ledger.toml"))
   if locator is not None:
       records_dir = resolve_config_relative_path(
           locator.config_path,
           "records",
           field_name="records_dir",
       )

``locate_config`` walks upward from the starting directory, returning a
``ConfigLocator`` with ``workspace_root``, ``config_path``, and ``source`` fields.

``resolve_config_relative_path`` resolves a path relative to the config file's
parent directory, applying the same safety checks.

For arbitrary resolved paths, use ``ensure_inside_base`` before access and
``relative_to_base`` when storing a POSIX relative path. ``resolve_under_base``
combines strict relative validation with containment and optional existence
checking.

``normalize_path_text`` is intentionally separate. It can normalize Unicode
punctuation, backslashes, whitespace, and casing for matching, but its output
must still pass the strict path helpers before filesystem use.

The default punctuation profile preserves existing behavior. Use
``punctuation_profile="wide"`` for additional quote, prime, dash, and minus
variants, ``"none"`` to disable named translations, or
``punctuation_translation`` to add application-specific matching substitutions.
