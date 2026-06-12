"""Atomic file write utilities for ledgercore."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from ledgercore.errors import AtomicWriteError


def _should_fsync(fast_io_env_var: str | None) -> bool:
    if fast_io_env_var is None:
        return True
    return not os.environ.get(fast_io_env_var, "")


def _fsync_dir(path: Path) -> None:
    try:
        fd = os.open(path, os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _cleanup_tmp(tmp_fd: int | None, tmp_path: Path | None) -> None:
    if tmp_fd is not None:
        try:
            os.close(tmp_fd)
        except OSError:
            pass
    if tmp_path is not None:
        try:
            tmp_path.unlink()
        except OSError:
            pass


def atomic_write_text(
    path: Path,
    contents: str,
    *,
    normalize: bool = False,
    fsync: bool = True,
    fast_io_env_var: str | None = None,
) -> None:
    """Write text to a file atomically using a temp file and os.replace."""
    if normalize:
        contents = contents.replace("\r\n", "\n").replace("\r", "\n")

    path.parent.mkdir(parents=True, exist_ok=True)
    do_fsync = fsync and _should_fsync(fast_io_env_var)

    tmp_fd: int | None = None
    tmp_path: Path | None = None
    try:
        tmp_fd, tmp_name = tempfile.mkstemp(
            dir=str(path.parent),
            prefix=".ledgercore-tmp-",
        )
        tmp_path = Path(tmp_name)
        with os.fdopen(tmp_fd, "wb") as f:
            f.write(contents.encode("utf-8"))
            if do_fsync:
                f.flush()
                os.fsync(f.fileno())
        tmp_fd = None  # closed by fdopen context manager
        os.replace(tmp_name, str(path))
        tmp_path = None
        if do_fsync:
            _fsync_dir(path.parent)
    except OSError as exc:
        _cleanup_tmp(tmp_fd, tmp_path)
        raise AtomicWriteError(f"Atomic write failed for {path}") from exc


def atomic_create_text(
    path: Path,
    contents: str,
    *,
    fsync: bool = True,
    fast_io_env_var: str | None = None,
) -> None:
    """Create a new file atomically using O_CREAT|O_EXCL for race safety.

    Fails with AtomicWriteError if the target already exists or if a
    concurrent process creates the file between the check and the write.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    do_fsync = fsync and _should_fsync(fast_io_env_var)

    try:
        fd = os.open(str(path), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    except FileExistsError as exc:
        raise AtomicWriteError(f"Target already exists: {path}") from exc
    except OSError as exc:
        raise AtomicWriteError(f"Atomic create failed for {path}") from exc

    try:
        encoded = contents.encode("utf-8")
        os.write(fd, encoded)
        if do_fsync:
            os.fsync(fd)
    except OSError as exc:
        try:
            os.close(fd)
        except OSError:
            pass
        try:
            path.unlink()
        except OSError:
            pass
        raise AtomicWriteError(f"Atomic create failed for {path}") from exc

    try:
        os.close(fd)
    except OSError as exc:
        raise AtomicWriteError(f"Atomic create failed for {path}") from exc

    if do_fsync:
        _fsync_dir(path.parent)
