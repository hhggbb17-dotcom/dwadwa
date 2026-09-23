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
            CREATE TABLE IF NOT EXISTS documents (
              id INTEGER PRIMARY KEY AUTOINCREMENT, kind TEXT NOT NULL, folio TEXT NOT NULL,
              document_date TEXT NOT NULL, party_code TEXT DEFAULT '', party_name TEXT DEFAULT '',
              sale_type TEXT DEFAULT '', source_store TEXT DEFAULT '', destination_store TEXT DEFAULT '',
              subtotal REAL DEFAULT 0, discount REAL DEFAULT 0, tax REAL DEFAULT 0, total REAL DEFAULT 0,
              status INTEGER DEFAULT 1, notes TEXT DEFAULT '', created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS document_items (
              id INTEGER PRIMARY KEY AUTOINCREMENT, document_id INTEGER NOT NULL,
              edition_id INTEGER NOT NULL, publication_code TEXT NOT NULL, edition_number TEXT DEFAULT '',
              title TEXT DEFAULT '', quantity INTEGER NOT NULL, price REAL DEFAULT 0,
              discount REAL DEFAULT 0, tax REAL DEFAULT 0, amount REAL DEFAULT 0,
              FOREIGN KEY(document_id) REFERENCES documents(id),
              FOREIGN KEY(edition_id) REFERENCES editions(id)
            );
            CREATE TABLE IF NOT EXISTS accounts_receivable (
              id INTEGER PRIMARY KEY AUTOINCREMENT, customer_id INTEGER NOT NULL, account_type INTEGER NOT NULL,
              document_id INTEGER, charge REAL DEFAULT 0, payment REAL DEFAULT 0,
              entry_date TEXT NOT NULL, reference TEXT DEFAULT '', status INTEGER DEFAULT 1
            );
            CREATE TABLE IF NOT EXISTS accounts_payable (
              id INTEGER PRIMARY KEY AUTOINCREMENT, supplier_id INTEGER NOT NULL, account_type INTEGER NOT NULL,
              document_id INTEGER, amount REAL DEFAULT 0, balance REAL DEFAULT 0,
              entry_date TEXT NOT NULL, reference TEXT DEFAULT '', status INTEGER DEFAULT 1
            );
            CREATE TABLE IF NOT EXISTS stock_ledger (
              id INTEGER PRIMARY KEY AUTOINCREMENT, document_id INTEGER NOT NULL, edition_id INTEGER NOT NULL,
              store TEXT NOT NULL, quantity INTEGER NOT NULL, movement TEXT NOT NULL,
              entry_date TEXT NOT NULL
            );
            """
        )
        edition_columns = {row[1] for row in db.execute("PRAGMA table_info(editions)")}
        if "stock_returns" not in edition_columns:
            db.execute("ALTER TABLE editions ADD COLUMN stock_returns REAL DEFAULT 0")
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
        "operations": ("documents", "id, kind, folio, document_date operation_date, party_code, party_name, total", "id DESC"),
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


@app.get("/api/edition-lookup")
def edition_lookup():
    publication = request.args.get("publication", "").strip()
    number = request.args.get("edition", "").strip()
    with connection() as db:
        row = db.execute(
            """SELECT e.id, p.code publication_code, p.title, e.number, e.name, e.price,
                      e.stock, e.stock_returns, p.tax
               FROM editions e JOIN publications p ON p.id=e.publication_id
               WHERE p.code=? AND (e.number=? OR e.name=? OR e.id=?)
               ORDER BY e.id DESC LIMIT 1""",
            (publication, number, number, int(number) if number.isdigit() else -1),
        ).fetchone()
    if not row:
        return jsonify({"error": "No existe esa revista/edición"}), 404
    return jsonify(dict(row))


def number(value, default=0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


@app.post("/api/documents")
def save_document():
    body = request.get_json(force=True)
    kind = str(body.get("kind", "")).strip().upper()
    items = body.get("items") or []
    if not kind or not items:
        return jsonify({"error": "La operación requiere al menos una partida"}), 400

    supported = {
        "COMPRA", "VENTA", "DEVOLUCION DE CLIENTE", "DEVOLUCION EXTEMPORANEA",
        "DEVOLUCION A PROVEEDOR", "TRASPASO"
    }
    if kind not in supported:
        return jsonify({"error": "Este módulo aún requiere seleccionar el documento original"}), 400

    try:
        with connection() as db:
            normalized = []
            subtotal = discount_total = tax_total = total = 0.0
            for item in items:
                edition_id = int(item.get("edition_id") or 0)
                quantity = int(number(item.get("quantity")))
                if edition_id <= 0 or quantity <= 0:
                    raise ValueError("Revista, edición y cantidad son obligatorias")
                edition = db.execute(
                    """SELECT e.id,e.number,e.price,e.stock,e.stock_returns,p.code,p.title,p.tax
                       FROM editions e JOIN publications p ON p.id=e.publication_id WHERE e.id=?""",
                    (edition_id,),
                ).fetchone()
                if not edition:
                    raise ValueError("Una edición seleccionada ya no existe")
                price = number(item.get("price"), edition["price"])
                discount = number(item.get("discount"))
                base = quantity * price
                discounted = base * (1 - discount / 100)
                tax_rate = number(edition["tax"])
                tax_amount = discounted * tax_rate / 100
                amount = discounted + tax_amount
                subtotal += base
                discount_total += base - discounted
                tax_total += tax_amount
                total += amount
                normalized.append((edition, quantity, price, discount, tax_rate, amount))

            cursor = db.execute(
                """INSERT INTO documents
                (kind,folio,document_date,party_code,party_name,sale_type,source_store,destination_store,
                 subtotal,discount,tax,total,status,notes) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,1,?)""",
                (kind, str(body.get("folio", "")), str(body.get("operation_date", date.today().isoformat())),
                 str(body.get("party_code", "")), str(body.get("party_name", "")),
                 str(body.get("sale_type", "")), str(body.get("source_store", "")),
                 str(body.get("destination_store", "")), subtotal, discount_total, tax_total, total,
                 str(body.get("notes", ""))),
            )
            document_id = cursor.lastrowid

            for edition, quantity, price, discount, tax_rate, amount in normalized:
                db.execute(
                    """INSERT INTO document_items
                    (document_id,edition_id,publication_code,edition_number,title,quantity,price,discount,tax,amount)
                    VALUES (?,?,?,?,?,?,?,?,?,?)""",
                    (document_id, edition["id"], edition["code"], edition["number"], edition["title"],
                     quantity, price, discount, tax_rate, amount),
                )
                movements = []
                if kind == "COMPRA":
                    movements = [("BODEGA", quantity, "COMPRA")]
                elif kind == "VENTA":
                    if edition["stock"] < quantity:
                        raise ValueError(f"Existencia insuficiente de {edition['title']}: {edition['stock']}")
                    movements = [("BODEGA", -quantity, "VENTA")]
                elif kind in {"DEVOLUCION DE CLIENTE", "DEVOLUCION EXTEMPORANEA"}:
                    movements = [("DEVOLUCIONES", quantity, kind)]
                elif kind == "DEVOLUCION A PROVEEDOR":
                    source = str(body.get("source_store", "BODEGA")).upper()
                    available = edition["stock_returns"] if source == "DEVOLUCIONES" else edition["stock"]
                    if available < quantity:
                        raise ValueError(f"Existencia insuficiente de {edition['title']} en {source}")
                    movements = [(source, -quantity, kind)]
                elif kind == "TRASPASO":
                    source = str(body.get("source_store", "BODEGA")).upper()
                    destination = str(body.get("destination_store", "DEVOLUCIONES")).upper()
                    if source == destination:
                        raise ValueError("El origen y el destino deben ser diferentes")
                    available = edition["stock_returns"] if source == "DEVOLUCIONES" else edition["stock"]
                    if available < quantity:
                        raise ValueError(f"Existencia insuficiente de {edition['title']} en {source}")
                    movements = [(source, -quantity, "SALIDA TRASPASO"), (destination, quantity, "ENTRADA TRASPASO")]

                for store, movement_quantity, movement in movements:
                    column = "stock_returns" if store == "DEVOLUCIONES" else "stock"
                    db.execute(f"UPDATE editions SET {column}={column}+? WHERE id=?", (movement_quantity, edition["id"]))
                    db.execute(
                        "INSERT INTO stock_ledger(document_id,edition_id,store,quantity,movement,entry_date) VALUES(?,?,?,?,?,?)",
                        (document_id, edition["id"], store, movement_quantity, movement, body.get("operation_date", date.today().isoformat())),
                    )

            if kind == "VENTA" and str(body.get("sale_type", "CONTADO")).upper() == "CREDITO":
                customer = db.execute("SELECT id FROM customers WHERE code=?", (str(body.get("party_code", "")),)).fetchone()
                if not customer:
                    raise ValueError("El cliente no existe")
                db.execute("UPDATE customers SET balance=balance+? WHERE id=?", (total, customer["id"]))
                db.execute(
                    """INSERT INTO accounts_receivable
                    (customer_id,account_type,document_id,charge,payment,entry_date,reference,status)
                    VALUES(?,1,?,?,0,?,?,1)""",
                    (customer["id"], document_id, total, body.get("operation_date", date.today().isoformat()), body.get("folio", "")),
                )
            if kind == "COMPRA":
                supplier = db.execute("SELECT id FROM suppliers WHERE code=?", (str(body.get("party_code", "")),)).fetchone()
                if not supplier:
                    raise ValueError("El proveedor no existe")
                db.execute("UPDATE suppliers SET balance=balance+? WHERE id=?", (total, supplier["id"]))
                db.execute(
                    """INSERT INTO accounts_payable
                    (supplier_id,account_type,document_id,amount,balance,entry_date,reference,status)
                    VALUES(?,1,?,?,?,?,?,1)""",
                    (supplier["id"], document_id, total, total, body.get("operation_date", date.today().isoformat()), body.get("folio", "")),
                )
        return jsonify({"ok": True, "id": document_id, "total": round(total, 2)})
    except (ValueError, sqlite3.IntegrityError) as exc:
        return jsonify({"error": str(exc)}), 400


if __name__ == "__main__":
    initialize_database()
    threading.Timer(1.0, lambda: webbrowser.open("http://127.0.0.1:5000")).start()
    app.run(host="127.0.0.1", port=5000, debug=False)
