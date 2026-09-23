"""Copia completa de una base Firebird SADYV a SQLite para la aplicación web.

El importador sólo ejecuta SELECT sobre Firebird. Trabaja contra una copia de la
base original y crea un archivo SQLite independiente con todas las tablas y filas.
"""

from __future__ import annotations

import argparse
import os
import sqlite3
from datetime import date, datetime, time
from decimal import Decimal
from pathlib import Path

import firebirdsql


def quote(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def sqlite_value(value):
    if value is None or isinstance(value, (str, int, float, bytes)):
        return value
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (date, datetime, time)):
        return value.isoformat(sep=" ") if isinstance(value, datetime) else value.isoformat()
    if isinstance(value, memoryview):
        return bytes(value)
    if hasattr(value, "read"):
        data = value.read()
        return bytes(data) if not isinstance(data, str) else data
    return str(value)


def tables(cursor) -> list[str]:
    cursor.execute(
        """SELECT TRIM(RDB$RELATION_NAME)
           FROM RDB$RELATIONS
           WHERE COALESCE(RDB$SYSTEM_FLAG,0)=0 AND RDB$VIEW_BLR IS NULL
           ORDER BY RDB$RELATION_NAME"""
    )
    return [row[0].strip() for row in cursor.fetchall()]


def columns(cursor, table: str) -> list[str]:
    cursor.execute(
        """SELECT TRIM(RDB$FIELD_NAME)
           FROM RDB$RELATION_FIELDS
           WHERE RDB$RELATION_NAME=? ORDER BY RDB$FIELD_POSITION""",
        (table,),
    )
    return [row[0].strip() for row in cursor.fetchall()]


def migrate(args) -> None:
    destination = Path(args.output).resolve()
    if destination.exists() and not args.replace:
        raise SystemExit(f"Ya existe {destination}. Usa --replace para recrearla.")
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    if temporary.exists():
        temporary.unlink()

    source = firebirdsql.connect(
        host=args.host,
        port=args.port,
        database=str(Path(args.database).resolve()),
        user=args.user,
        password=args.password,
        charset=args.charset,
    )
    target = sqlite3.connect(temporary)
    try:
        target.execute("PRAGMA journal_mode=WAL")
        target.execute("PRAGMA synchronous=NORMAL")
        target.execute(
            """CREATE TABLE migration_manifest(
               table_name TEXT PRIMARY KEY, row_count INTEGER NOT NULL,
               imported_at TEXT NOT NULL)"""
        )
        metadata = source.cursor()
        table_names = tables(metadata)
        print(f"Tablas encontradas: {len(table_names)}", flush=True)

        for position, table in enumerate(table_names, 1):
            names = columns(metadata, table)
            target.execute(
                f"CREATE TABLE {quote(table)} ({','.join(quote(name) for name in names)})"
            )
            source_cursor = source.cursor()
            source_cursor.execute(f"SELECT * FROM {quote(table)}")
            placeholders = ",".join("?" for _ in names)
            insert = f"INSERT INTO {quote(table)} VALUES ({placeholders})"
            total = 0
            while True:
                rows = source_cursor.fetchmany(1000)
                if not rows:
                    break
                converted = [tuple(sqlite_value(value) for value in row) for row in rows]
                target.executemany(insert, converted)
                total += len(rows)
            target.execute(
                "INSERT INTO migration_manifest VALUES(?,?,?)",
                (table, total, datetime.now().isoformat(timespec="seconds")),
            )
            target.commit()
            print(f"[{position:02}/{len(table_names)}] {table}: {total:,}", flush=True)

        check = target.execute("PRAGMA integrity_check").fetchone()[0]
        if check != "ok":
            raise RuntimeError(f"SQLite no pasó la verificación: {check}")
    finally:
        target.close()
        source.close()

    if destination.exists():
        os.replace(destination, destination.with_suffix(destination.suffix + ".bak"))
    os.replace(temporary, destination)
    print(f"Migración completa: {destination}", flush=True)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser()
    result.add_argument("database", help="Copia de CARLOSE.FDB")
    result.add_argument("output", help="Archivo SQLite de salida")
    result.add_argument("--host", default="127.0.0.1")
    result.add_argument("--port", type=int, default=3050)
    result.add_argument("--user", default="SYSDBA")
    result.add_argument("--password", default=os.environ.get("SADYV_FIREBIRD_PASSWORD", "masterkey"))
    result.add_argument("--charset", default="ISO8859_1")
    result.add_argument("--replace", action="store_true")
    return result


if __name__ == "__main__":
    migrate(parser().parse_args())
