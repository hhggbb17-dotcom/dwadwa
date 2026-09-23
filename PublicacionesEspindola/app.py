from __future__ import annotations

import json
import sqlite3
import threading
import webbrowser
from datetime import date
from pathlib import Path

from flask import Flask, jsonify, render_template, request


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "sadyv.db"
JSON_SOURCE = DATA_DIR / "store.json"

app = Flask(__name__)


def connection() -> sqlite3.Connection:
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    return db


def initialize_database() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    with connection() as db:
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS customers (
              id INTEGER PRIMARY KEY AUTOINCREMENT, code TEXT UNIQUE, name TEXT NOT NULL,
              rfc TEXT DEFAULT '', phone TEXT DEFAULT '', email TEXT DEFAULT '',
              address TEXT DEFAULT '', city TEXT DEFAULT '', credit_limit REAL DEFAULT 0,
              balance REAL DEFAULT 0, discount REAL DEFAULT 0, active INTEGER DEFAULT 1
            );
            CREATE TABLE IF NOT EXISTS suppliers (
              id INTEGER PRIMARY KEY AUTOINCREMENT, code TEXT UNIQUE, name TEXT NOT NULL,
              rfc TEXT DEFAULT '', phone TEXT DEFAULT '', email TEXT DEFAULT '',
              address TEXT DEFAULT '', balance REAL DEFAULT 0, active INTEGER DEFAULT 1
            );
            CREATE TABLE IF NOT EXISTS publications (
              id INTEGER PRIMARY KEY AUTOINCREMENT, code TEXT UNIQUE, title TEXT NOT NULL,
              supplier_id INTEGER, barcode TEXT DEFAULT '', tax REAL DEFAULT 0,
              monitored INTEGER DEFAULT 0, active INTEGER DEFAULT 1
            );
            CREATE TABLE IF NOT EXISTS editions (
              id INTEGER PRIMARY KEY AUTOINCREMENT, publication_id INTEGER NOT NULL,
              number TEXT DEFAULT '', name TEXT DEFAULT '', barcode TEXT DEFAULT '',
              arrival_date TEXT DEFAULT '', return_deadline TEXT DEFAULT '',
              price REAL DEFAULT 0, stock REAL DEFAULT 0, reserved REAL DEFAULT 0,
              active INTEGER DEFAULT 1
            );
            CREATE TABLE IF NOT EXISTS operations (
              id INTEGER PRIMARY KEY AUTOINCREMENT, kind TEXT NOT NULL, folio TEXT NOT NULL,
              operation_date TEXT NOT NULL, party_code TEXT DEFAULT '', party_name TEXT DEFAULT '',
              total REAL DEFAULT 0, notes TEXT DEFAULT '', created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        already_loaded = db.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
        if not already_loaded and JSON_SOURCE.exists():
            source = json.loads(JSON_SOURCE.read_text(encoding="utf-8"))
            db.executemany(
                """INSERT OR IGNORE INTO customers
                (id,code,name,rfc,phone,email,address,city,credit_limit,balance,discount,active)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                [
                    (x.get("id"), x.get("code"), x.get("name") or "SIN NOMBRE", x.get("rfc", ""),
                     x.get("phone", ""), x.get("email", ""), x.get("address", ""), x.get("city", ""),
                     x.get("creditLimit", 0), x.get("balance", 0), x.get("discountPercent", 0), int(x.get("active", True)))
                    for x in source.get("customers", [])
                ],
            )
            db.executemany(
                """INSERT OR IGNORE INTO suppliers
                (id,code,name,rfc,phone,email,address,balance,active) VALUES (?,?,?,?,?,?,?,?,?)""",
                [(x.get("id"), x.get("code"), x.get("name") or "SIN NOMBRE", x.get("rfc", ""),
                  x.get("phone", ""), x.get("email", ""), x.get("address", ""),
                  x.get("balance", 0), int(x.get("active", True))) for x in source.get("suppliers", [])],
            )
            db.executemany(
                """INSERT OR IGNORE INTO publications
                (id,code,title,supplier_id,barcode,tax,monitored,active) VALUES (?,?,?,?,?,?,?,?)""",
                [(x.get("id"), x.get("code"), x.get("title") or "SIN TITULO", x.get("supplierId"),
                  x.get("barcode", ""), x.get("taxPercent", 0), int(x.get("monitored", False)),
                  int(x.get("active", True))) for x in source.get("publications", [])],
            )
            db.executemany(
                """INSERT OR IGNORE INTO editions
                (id,publication_id,number,name,barcode,arrival_date,return_deadline,price,stock,reserved,active)
                VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                [(x.get("id"), x.get("publicationId"), x.get("number", ""), x.get("name", ""),
                  x.get("barcode", ""), x.get("arrivalDate", "")[:10], x.get("returnDeadline", "")[:10],
                  x.get("price", 0), x.get("stock", 0), x.get("reserved", 0), int(x.get("active", True)))
                 for x in source.get("editions", [])],
            )


@app.get("/")
def index():
    return render_template("index.html", today=date.today().strftime("%d/%m/%Y"))


@app.get("/api/<entity>")
def list_entity(entity: str):
    config = {
        "customers": ("customers", "id, code, name, rfc, phone, city, balance", "name"),
        "suppliers": ("suppliers", "id, code, name, rfc, phone, balance", "name"),
        "publications": ("publications", "id, code, title, barcode, tax", "title"),
        "editions": ("editions e JOIN publications p ON p.id=e.publication_id",
                     "e.id, p.code publication_code, p.title, e.number, e.name, e.price, e.stock, e.arrival_date", "p.title"),
        "operations": ("operations", "id, kind, folio, operation_date, party_code, party_name, total", "id DESC"),
    }
    if entity not in config:
        return jsonify({"error": "Catálogo desconocido"}), 404
    table, fields, ordering = config[entity]
    term = request.args.get("q", "").strip()
    limit = min(int(request.args.get("limit", 250)), 1000)
    where, params = "", []
    if term:
        searchable = {"customers": "name", "suppliers": "name", "publications": "title",
                      "editions": "p.title", "operations": "party_name"}[entity]
        where, params = f" WHERE {searchable} LIKE ?", [f"%{term}%"]
    with connection() as db:
        rows = db.execute(f"SELECT {fields} FROM {table}{where} ORDER BY {ordering} LIMIT ?", (*params, limit)).fetchall()
    return jsonify([dict(row) for row in rows])


@app.post("/api/<entity>")
def save_entity(entity: str):
    body = request.get_json(force=True)
    specs = {
        "customers": (["code", "name", "rfc", "phone", "email", "address", "city", "credit_limit", "balance", "discount"], "name"),
        "suppliers": (["code", "name", "rfc", "phone", "email", "address", "balance"], "name"),
        "publications": (["code", "title", "supplier_id", "barcode", "tax"], "title"),
        "operations": (["kind", "folio", "operation_date", "party_code", "party_name", "total", "notes"], "folio"),
    }
    if entity not in specs:
        return jsonify({"error": "Operación no disponible"}), 404
    fields, required = specs[entity]
    if not str(body.get(required, "")).strip():
        return jsonify({"error": f"El campo {required} es obligatorio"}), 400
    values = [body.get(field, "") for field in fields]
    placeholders = ",".join("?" for _ in fields)
    try:
        with connection() as db:
            cursor = db.execute(f"INSERT INTO {entity} ({','.join(fields)}) VALUES ({placeholders})", values)
            new_id = cursor.lastrowid
        return jsonify({"ok": True, "id": new_id})
    except sqlite3.IntegrityError as exc:
        return jsonify({"error": str(exc)}), 409


if __name__ == "__main__":
    initialize_database()
    threading.Timer(1.0, lambda: webbrowser.open("http://127.0.0.1:5000")).start()
    app.run(host="127.0.0.1", port=5000, debug=False)
