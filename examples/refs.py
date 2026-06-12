"""Example: working with cross-ledger resource references."""

from ledgercore.refs import (
    LedgerResourceRef,
    is_resource_ref,
    parse_global_ref,
    parse_local_ref,
    parse_resource_ref,
)

# Parse a canonical global ref
ref = parse_resource_ref("tl:task-0001")
assert ref.ledger == "tl"
assert ref.kind == "task"
assert ref.number == 1
assert ref.local_id == "task-0001"
assert ref.global_ref == "tl:task-0001"
assert ref.file_ref == "tl-task-0001"

# Parse a file-safe alias
ref2 = parse_resource_ref("al-adr-0002")
assert ref2.global_ref == "al:adr-0002"

# Parse a local ref and assign a ledger
ref3 = parse_resource_ref("task-0003", default_ledger="tl")
assert ref3.global_ref == "tl:task-0003"

# Require a global ref
ref4 = parse_global_ref("sw:spec-0001")
assert ref4.ledger == "sw"

# Require a local ref (no ledger)
ref5 = parse_local_ref("task-0007")
assert ref5.ledger is None

# Construct directly
ref6 = LedgerResourceRef(ledger="tl", kind="task", number=42)
assert ref6.format("canonical") == "tl:task-0042"
assert ref6.format("file") == "tl-task-0042"
assert ref6.format("local") == "task-0042"

# Copy with a different ledger
ref7 = ref6.with_ledger("al")
assert ref7.global_ref == "al:task-0042"

# Check validity
assert is_resource_ref("tl:task-0001")
assert not is_resource_ref("not-a-ref")

# Restrict to allowed ledgers and kinds
ref8 = parse_resource_ref(
    "tl:task-0001",
    allowed_ledgers={"tl", "al"},
    allowed_kinds={"task", "adr"},
)
assert ref8.ledger == "tl"

print("refs example passed")
