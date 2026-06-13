Cross-ledger references
=======================

``ledgercore.refs`` provides a canonical scheme for referencing records across
independent ledgers.

Local IDs
---------

Inside a single ledger, records use local IDs:

.. code:: text

   task-0001
   adr-0002
   spec-0003

A local ID has the form ``<kind>-<number>``, where kind is a lowercase alphanumeric
token and number is a zero-padded positive integer.

Global refs
-----------

When linking records across ledgers, use canonical global refs:

.. code:: text

   <ledger>:<kind>-<number>

Examples:

.. code:: text

   tl:task-0001
   al:adr-0002
   sw:spec-0003

The ledger code is a short lowercase token that identifies the originating
ledger. It is not a URL or a path; downstream packages choose their own codes.

File-safe refs
--------------

For filenames or systems that cannot use ``:``, replace the colon with a hyphen:

.. code:: text

   tl-task-0001
   al-adr-0002

Legacy underscore alias
-----------------------

The parser also accepts underscore-based aliases:

.. code:: text

   tl_task_0001
   al_adr_0002

These exist for backward compatibility. New code should use canonical or
file-safe forms.

Parsing
-------

.. code:: python

   from ledgercore.refs import parse_resource_ref

   ref = parse_resource_ref("tl:task-0001")

   assert ref.ledger == "tl"
   assert ref.kind == "task"
   assert ref.number == 1
   assert ref.local_id == "task-0001"
   assert ref.global_ref == "tl:task-0001"
   assert ref.file_ref == "tl-task-0001"

``parse_resource_ref`` accepts canonical, file-safe, legacy, and local forms.
When parsing a local ref, set ``default_ledger`` to attach a namespace:

.. code:: python

   ref = parse_resource_ref("task-0001", default_ledger="tl")
   assert ref.global_ref == "tl:task-0001"

Allowed ledgers and kinds
-------------------------

Restrict parsing to known values:

.. code:: python

   from ledgercore.refs import parse_resource_ref

   ref = parse_resource_ref(
       "tl:task-0001",
       allowed_ledgers={"tl", "al"},
       allowed_kinds={"task", "adr"},
   )

Cross-ledger link example
-------------------------

.. code:: yaml

   source: tl:task-0001
   target: al:adr-0002
   relation: implements

Both endpoints are unambiguous because each carries its ledger namespace.

Formatting
----------

.. code:: python

   from ledgercore.refs import LedgerResourceRef

   ref = LedgerResourceRef(ledger="tl", kind="task", number=1)

   ref.format("canonical")  # "tl:task-0001"
   ref.format("file")       # "tl-task-0001"
   ref.format("local")      # "task-0001"

Checking validity
-----------------

.. code:: python

   from ledgercore.refs import is_resource_ref

   assert is_resource_ref("tl:task-0001")
   assert not is_resource_ref("not-a-ref")
