"""Serialize SQLite in memory, encrypt on commit, serialize access across processes."""
import os
from pathlib import Path
import sqlite3
import time

from api.protection import read_protected, write_protected


class ProtectedConnection(sqlite3.Connection):
    def persist(self):
        if self.execute("SELECT COUNT(*) FROM sqlite_master").fetchone()[0]:
            write_protected(self.protected_path, self.serialize())

    def commit(self):
        super().commit()
        self.persist()

    def __exit__(self, kind, value, traceback):
        result = super().__exit__(kind, value, traceback)
        if kind is None:
            self.persist()
        return result

    def close(self):
        try:
            super().close()
        finally:
            lock = getattr(self, "file_lock", None)
            if lock is not None:
                import msvcrt
                lock.seek(0)
                msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)
                lock.close()
                self.file_lock = None


def connect(database):
    if str(database) == ":memory:":
        return sqlite3.connect(":memory:")
    if os.name != "nt":
        raise RuntimeError("El almacenamiento protegido requiere Windows")
    import msvcrt
    path = Path(database)
    lock = path.with_suffix(path.suffix + ".lock").open("a+b")
    lock.seek(0, 2)
    if lock.tell() == 0:
        lock.write(b"0")
        lock.flush()
    deadline = time.monotonic() + 10
    while True:
        try:
            lock.seek(0)
            msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
            break
        except OSError:
            if time.monotonic() >= deadline:
                lock.close()
                raise TimeoutError("La base de datos está ocupada")
            time.sleep(0.05)
    try:
        connection = sqlite3.connect(":memory:", factory=ProtectedConnection)
    except BaseException:
        lock.close()
        raise
    connection.file_lock = lock
    connection.protected_path = path
    try:
        connection.execute("PRAGMA temp_store=MEMORY")
        if path.exists():
            content = path.read_bytes()
            legacy = content.startswith(b"SQLite format 3\x00")
            if legacy:
                for suffix in ("-wal", "-journal"):
                    if Path(str(path) + suffix).exists():
                        raise RuntimeError("Cierra la API anterior antes de proteger la base de datos")
            connection.deserialize(content if legacy else read_protected(path))
            if connection.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise ValueError("La base de datos no supera la comprobación de integridad")
            if legacy:
                connection.persist()
        connection.execute("PRAGMA secure_delete=ON")
        return connection
    except BaseException:
        connection.close()
        raise
