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
LEGACY_DB_PATH = DATA_DIR / "legacy.db"

app = Flask(__name__)


def connection() -> sqlite3.Connection:
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    return db


def legacy_connection() -> sqlite3.Connection:
    db = sqlite3.connect(LEGACY_DB_PATH)
    db.row_factory = sqlite3.Row
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
            CREATE TABLE IF NOT EXISTS priorities (code TEXT PRIMARY KEY, percentage REAL DEFAULT 0);
            CREATE TABLE IF NOT EXISTS customer_groups (
              id INTEGER PRIMARY KEY, name TEXT NOT NULL, accumulated REAL DEFAULT 0, active INTEGER DEFAULT 1
            );
            CREATE TABLE IF NOT EXISTS routes (
              id INTEGER PRIMARY KEY, name TEXT NOT NULL, active INTEGER DEFAULT 1
            );
            CREATE TABLE IF NOT EXISTS employees (
              id INTEGER PRIMARY KEY, name TEXT NOT NULL, position TEXT DEFAULT '', area TEXT DEFAULT '', active INTEGER DEFAULT 1
            );
            CREATE TABLE IF NOT EXISTS account_types (
              id INTEGER PRIMARY KEY, name TEXT NOT NULL, kind TEXT NOT NULL, active INTEGER DEFAULT 1
            );
            CREATE TABLE IF NOT EXISTS movement_types (
              id INTEGER PRIMARY KEY, concept TEXT NOT NULL, kind TEXT NOT NULL, active INTEGER DEFAULT 1
            );
            CREATE TABLE IF NOT EXISTS packages (
              id INTEGER PRIMARY KEY, customer_id INTEGER NOT NULL, publication_id INTEGER NOT NULL,
              quantity INTEGER DEFAULT 0, distribution_date TEXT DEFAULT '', active INTEGER DEFAULT 1
            );
            CREATE TABLE IF NOT EXISTS orders (
              id INTEGER PRIMARY KEY, customer_id INTEGER NOT NULL, order_date TEXT NOT NULL,
              purchase_id INTEGER, status INTEGER DEFAULT 1
            );
            CREATE TABLE IF NOT EXISTS order_items (
              id INTEGER PRIMARY KEY, order_id INTEGER NOT NULL, publication_id INTEGER NOT NULL,
              edition_id INTEGER NOT NULL, quantity INTEGER DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS cash_register (
              id INTEGER PRIMARY KEY, employee_id INTEGER, customer_id INTEGER,
              charged REAL DEFAULT 0, cash REAL DEFAULT 0, change_amount REAL DEFAULT 0,
              withdrawal REAL DEFAULT 0, status INTEGER DEFAULT 1, entry_date TEXT, notes TEXT DEFAULT ''
            );
            CREATE TABLE IF NOT EXISTS cash_details (
              id INTEGER PRIMARY KEY, cash_id INTEGER NOT NULL, movement_id INTEGER,
              amount REAL DEFAULT 0, movement_type INTEGER
            );
            CREATE TABLE IF NOT EXISTS legacy_cancellations (
              id INTEGER PRIMARY KEY AUTOINCREMENT, category TEXT NOT NULL, folio TEXT NOT NULL,
              canceled_at TEXT NOT NULL, reason TEXT DEFAULT '', UNIQUE(category,folio)
            );
            """
        )
        edition_columns = {row[1] for row in db.execute("PRAGMA table_info(editions)")}
        if "stock_returns" not in edition_columns:
            db.execute("ALTER TABLE editions ADD COLUMN stock_returns REAL DEFAULT 0")
        migrations = {
            "customers": {
                "priority": "TEXT DEFAULT ''", "group_id": "INTEGER", "legal_name": "TEXT DEFAULT ''",
                "postal_code": "TEXT DEFAULT ''", "state": "TEXT DEFAULT ''", "fax": "TEXT DEFAULT ''",
                "classification": "TEXT DEFAULT ''", "zone": "TEXT DEFAULT ''", "payment_condition": "TEXT DEFAULT ''",
                "payment_term": "INTEGER DEFAULT 0", "first_payment_day": "TEXT DEFAULT ''",
                "second_payment_day": "TEXT DEFAULT ''", "buyer": "TEXT DEFAULT ''", "payer": "TEXT DEFAULT ''",
                "representative": "TEXT DEFAULT ''", "return_percentage": "REAL DEFAULT 100",
                "route_id": "INTEGER", "distribution_order": "INTEGER DEFAULT 1"
            },
            "suppliers": {
                "legal_name": "TEXT DEFAULT ''", "city": "TEXT DEFAULT ''", "state": "TEXT DEFAULT ''",
                "postal_code": "TEXT DEFAULT ''", "mobile": "TEXT DEFAULT ''", "payment_condition": "TEXT DEFAULT ''",
                "supplier_return_days": "INTEGER DEFAULT 0", "customer_return_days": "INTEGER DEFAULT 0"
            },
            "publications": {"supplier_code": "TEXT DEFAULT ''", "supplier_publication_code": "TEXT DEFAULT ''", "top25": "INTEGER DEFAULT 0"},
            "editions": {"legacy_code": "TEXT DEFAULT ''", "supplier_deadline": "TEXT DEFAULT ''", "customer_discount": "REAL DEFAULT 0"}
        }
        for table, additions in migrations.items():
            present = {row[1] for row in db.execute(f"PRAGMA table_info({table})")}
            for column, definition in additions.items():
                if column not in present:
                    db.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
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
        "priorities": ("priorities", "code, percentage", "code"),
        "groups": ("customer_groups", "id, name, accumulated, active", "name"),
        "routes": ("routes", "id, name, active", "name"),
        "employees": ("employees", "id, name, position, area, active", "name"),
        "account_types": ("account_types", "id, name, kind, active", "id"),
        "movement_types": ("movement_types", "id, concept, kind, active", "id"),
        "packages": ("packages k JOIN customers c ON c.id=k.customer_id JOIN publications p ON p.id=k.publication_id",
                     "k.id, c.code customer_code, c.name customer, p.code publication_code, p.title, k.quantity, k.distribution_date", "c.name,p.title"),
    }
    if entity not in config:
        return jsonify({"error": "Catálogo desconocido"}), 404
    table, fields, ordering = config[entity]
    term = request.args.get("q", "").strip()
    limit = min(int(request.args.get("limit", 250)), 1000)
    where, params = "", []
    if term:
        searchable = {"customers": "name", "suppliers": "name", "publications": "title",
                      "editions": "p.title", "operations": "party_name", "priorities": "code",
                      "groups": "name", "routes": "name", "employees": "name", "account_types": "name",
                      "movement_types": "concept", "packages": "c.name"}[entity]
        where, params = f" WHERE {searchable} LIKE ?", [f"%{term}%"]
    with connection() as db:
        rows = db.execute(f"SELECT {fields} FROM {table}{where} ORDER BY {ordering} LIMIT ?", (*params, limit)).fetchall()
    return jsonify([dict(row) for row in rows])


@app.post("/api/<entity>")
def save_entity(entity: str):
    body = request.get_json(force=True)
    specs = {
        "customers": ("customers", ["code", "name", "rfc", "phone", "email", "address", "city", "credit_limit", "balance", "discount", "priority", "group_id", "legal_name", "postal_code", "state", "fax", "classification", "zone", "payment_condition", "payment_term", "first_payment_day", "second_payment_day", "buyer", "payer", "representative", "return_percentage", "route_id", "distribution_order"], "name"),
        "suppliers": ("suppliers", ["code", "name", "rfc", "phone", "email", "address", "balance", "legal_name", "city", "state", "postal_code", "mobile", "payment_condition", "supplier_return_days", "customer_return_days"], "name"),
        "publications": ("publications", ["code", "title", "supplier_id", "barcode", "tax", "supplier_publication_code", "top25"], "title"),
        "operations": ("operations", ["kind", "folio", "operation_date", "party_code", "party_name", "total", "notes"], "folio"),
        "priorities": ("priorities", ["code", "percentage"], "code"),
        "groups": ("customer_groups", ["name", "accumulated", "active"], "name"),
        "routes": ("routes", ["name", "active"], "name"),
        "employees": ("employees", ["name", "position", "area", "active"], "name"),
        "account_types": ("account_types", ["name", "kind", "active"], "name"),
        "movement_types": ("movement_types", ["concept", "kind", "active"], "concept"),
    }
    if entity not in specs:
        return jsonify({"error": "Operación no disponible"}), 404
    table, fields, required = specs[entity]
    if not str(body.get(required, "")).strip():
        return jsonify({"error": f"El campo {required} es obligatorio"}), 400
    values = [body.get(field, "") for field in fields]
    placeholders = ",".join("?" for _ in fields)
    try:
        with connection() as db:
            cursor = db.execute(f"INSERT INTO {table} ({','.join(fields)}) VALUES ({placeholders})", values)
            new_id = cursor.lastrowid
        return jsonify({"ok": True, "id": new_id})
    except sqlite3.IntegrityError as exc:
        return jsonify({"error": str(exc)}), 409


@app.post("/api/editions")
def save_edition():
    body = request.get_json(force=True)
    with connection() as db:
        publication = db.execute("SELECT id FROM publications WHERE code=?", (str(body.get("publication_code", "")),)).fetchone()
        if not publication:
            return jsonify({"error": "La revista no existe"}), 404
        cursor = db.execute(
            """INSERT INTO editions
            (publication_id,number,name,barcode,arrival_date,return_deadline,price,stock,stock_returns,reserved,
             active,legacy_code,supplier_deadline,customer_discount)
            VALUES(?,?,?,?,?,?,?,?,?,0,1,?,?,?)""",
            (publication["id"], str(body.get("number", "")), body.get("name", ""), body.get("barcode", ""),
             body.get("arrival_date", ""), body.get("return_deadline", ""), number(body.get("price")),
             number(body.get("stock")), number(body.get("stock_returns")), body.get("legacy_code", ""),
             body.get("supplier_deadline", ""), number(body.get("customer_discount"))),
        )
    return jsonify({"ok": True, "id": cursor.lastrowid})


@app.post("/api/packages")
def save_package():
    body = request.get_json(force=True)
    customer_code = str(body.get("customer_code", "")).strip()
    publication_code = str(body.get("publication_code", "")).strip()
    quantity = int(number(body.get("quantity")))
    if quantity < 0:
        return jsonify({"error": "La cantidad no puede ser negativa"}), 400
    with connection() as db:
        customer = db.execute("SELECT id FROM customers WHERE code=?", (customer_code,)).fetchone()
        publication = db.execute("SELECT id FROM publications WHERE code=?", (publication_code,)).fetchone()
        if not customer or not publication:
            return jsonify({"error": "Cliente o revista inexistente"}), 404
        current = db.execute("SELECT id FROM packages WHERE customer_id=? AND publication_id=?", (customer["id"], publication["id"])).fetchone()
        if current:
            db.execute("UPDATE packages SET quantity=?,distribution_date=?,active=1 WHERE id=?",
                       (quantity, body.get("distribution_date", ""), current["id"]))
            package_id = current["id"]
        else:
            package_id = (db.execute("SELECT COALESCE(MAX(id),0)+1 FROM packages").fetchone()[0])
            db.execute("INSERT INTO packages VALUES(?,?,?,?,?,1)",
                       (package_id, customer["id"], publication["id"], quantity, body.get("distribution_date", "")))
    return jsonify({"ok": True, "id": package_id})


@app.post("/api/account-entry")
def account_entry():
    body = request.get_json(force=True)
    ledger = str(body.get("ledger", "receivable"))
    party_code = str(body.get("party_code", "")).strip()
    account_type = int(number(body.get("account_type")))
    amount = number(body.get("amount"))
    if amount <= 0:
        return jsonify({"error": "El importe debe ser mayor que cero"}), 400
    with connection() as db:
        account = db.execute("SELECT kind FROM account_types WHERE id=? AND active=1", (account_type,)).fetchone()
        if not account:
            return jsonify({"error": "El tipo de cuenta no existe"}), 404
        is_charge = str(account["kind"]).upper() == "CARGO"
        entry_date = body.get("entry_date", date.today().isoformat())
        if ledger == "receivable":
            party = db.execute("SELECT id FROM customers WHERE code=?", (party_code,)).fetchone()
            if not party:
                return jsonify({"error": "El cliente no existe"}), 404
            cursor = db.execute(
                """INSERT INTO accounts_receivable(customer_id,account_type,charge,payment,entry_date,reference,status)
                   VALUES(?,?,?,?,?,?,1)""",
                (party["id"], account_type, amount if is_charge else 0, 0 if is_charge else amount,
                 entry_date, body.get("reference", "")),
            )
            db.execute("UPDATE customers SET balance=balance+? WHERE id=?", (amount if is_charge else -amount, party["id"]))
        else:
            party = db.execute("SELECT id FROM suppliers WHERE code=?", (party_code,)).fetchone()
            if not party:
                return jsonify({"error": "El proveedor no existe"}), 404
            signed = amount if is_charge else -amount
            cursor = db.execute(
                """INSERT INTO accounts_payable(supplier_id,account_type,amount,balance,entry_date,reference,status)
                   VALUES(?,?,?,?,?,?,1)""",
                (party["id"], account_type, signed, signed, entry_date, body.get("reference", "")),
            )
            db.execute("UPDATE suppliers SET balance=balance+? WHERE id=?", (signed, party["id"]))
    return jsonify({"ok": True, "id": cursor.lastrowid})


@app.post("/api/cash")
def save_cash():
    body = request.get_json(force=True)
    with connection() as db:
        customer = db.execute("SELECT id FROM customers WHERE code=?", (str(body.get("customer_code", "")),)).fetchone()
        if not customer:
            return jsonify({"error": "El cliente no existe"}), 404
        cash = number(body.get("cash")); charged = number(body.get("charged")); change = max(cash - charged, 0)
        cash_id = db.execute("SELECT COALESCE(MAX(id),0)+1 FROM cash_register").fetchone()[0]
        db.execute(
            """INSERT INTO cash_register
               (id,employee_id,customer_id,charged,cash,change_amount,withdrawal,status,entry_date,notes)
               VALUES(?,1,?,?,?,?,?,1,?,?)""",
            (cash_id, customer["id"], charged, cash, change, number(body.get("withdrawal")),
             body.get("entry_date", date.today().isoformat()), body.get("notes", "")),
        )
        if charged > 0:
            db.execute("INSERT INTO cash_details VALUES(NULL,?,?,?,2)", (cash_id, None, charged))
            db.execute("""INSERT INTO accounts_receivable
                (customer_id,account_type,charge,payment,entry_date,reference,status)
                VALUES(?,2,0,?,?,?,1)""", (customer["id"], charged, body.get("entry_date", date.today().isoformat()), f"CAJA {cash_id}"))
            db.execute("UPDATE customers SET balance=balance-? WHERE id=?", (charged, customer["id"]))
    return jsonify({"ok": True, "id": cash_id, "change": change})


@app.post("/api/cancellations")
def cancel_legacy_document():
    body = request.get_json(force=True)
    category = str(body.get("category", "")).upper()
    folio = str(body.get("folio", "")).strip()
    allowed = {"PURCHASE", "SALE", "CUSTOMER_RETURN", "SUPPLIER_RETURN"}
    if category not in allowed or not folio:
        return jsonify({"error": "Tipo de documento o folio inválido"}), 400
    if not LEGACY_DB_PATH.exists():
        return jsonify({"error": "No se encontró el historial migrado"}), 404
    try:
        with legacy_connection() as old, connection() as db:
            if db.execute("SELECT 1 FROM legacy_cancellations WHERE category=? AND folio=?", (category, folio)).fetchone():
                raise ValueError("El documento ya fue cancelado")
            if category == "PURCHASE":
                header = old.execute("SELECT * FROM FACTCOMP WHERE CAST(FOLIINTEFACTCOMP AS TEXT)=?", (folio,)).fetchone()
                if not header: raise ValueError("No existe la compra")
                if header["STATFACTCOMP"] == 2: raise ValueError("La compra ya estaba cancelada")
                pending = old.execute("SELECT COUNT(*) FROM PEDIDOS WHERE FOLICOMPPEDI=? AND STATPEDI<>2", (int(folio),)).fetchone()[0]
                if pending: raise ValueError("La compra tiene pedidos; cancela primero esos pedidos")
                lines = old.execute("""SELECT CLAVREVIDETAFACTCOMP revista,CLAVEDICDETAFACTCOMP edicion,
                    CANTREVIDETAFACTCOMP cantidad FROM DETAFACTCOMP WHERE FOLIDETAFACTCOMP=? AND STATDETAFACTCOMP<>2""", (int(folio),)).fetchall()
                movement, store, sign = "CANCELACION DE COMPRA", "BODEGA", -1
                party_table, party_id, balance = "suppliers", str(header["CLAVPROVFACTCOMP"]), -number(header["TOTAFACTCOMP"])
            elif category == "SALE":
                header = old.execute("SELECT * FROM FACTVENT WHERE CAST(FOLIFACTVENT AS TEXT)=?", (folio,)).fetchone()
                if not header: raise ValueError("No existe la venta")
                if header["STATFACTVENT"] == 2: raise ValueError("La venta ya estaba cancelada")
                lines = old.execute("""SELECT CLAVREVIDETAFACTVENT revista,CLAVEDICDETAFACTVENT edicion,
                    CANTREVIDETAFACTVENT cantidad FROM DETAFACTVENT WHERE FOLIDETAFACTVENT=? AND STATREVIDETAFACTVENT<>2""", (int(folio),)).fetchall()
                movement, store, sign = "CANCELACION DE VENTA", "BODEGA", 1
                party_table, party_id = "customers", str(header["CLAVCLIEFACTVENT"])
                balance = -number(header["TOTAFACTVENT"]) if str(header["TIPOVENTFACTVENT"]).strip().upper()=="CREDITO" else 0
            elif category == "CUSTOMER_RETURN":
                header = old.execute("SELECT * FROM DEVOCLIE WHERE CAST(FOLIDEVOCLIE AS TEXT)=?", (folio,)).fetchone()
                if not header: raise ValueError("No existe la devolución del cliente")
                if header["STATDEVOCLIE"] == 2: raise ValueError("La devolución ya estaba cancelada")
                lines = old.execute("""SELECT CLAVREVIDETADEVOCLIE revista,CLAVEDICDETADEVOCLIE edicion,
                    CANTREVIDETADEVOCLIE cantidad FROM DETADEVOCLIE WHERE FOLIDETADEVOCLIE=? AND STATREVIDETADEVOCLIE<>2""", (int(folio),)).fetchall()
                movement, sign = "CANCELACION DE DEVOLUCION CLIENTE", -1
                store = "BODEGA" if str(header["TIPODEVOCLIE"]).strip().upper()=="CANCELACION" else "DEVOLUCIONES"
                party_table, party_id, balance = "customers", str(header["CLAVCLIEDEVOCLIE"]), number(header["TOTADEVOCLIE"])
            else:
                header = old.execute("SELECT * FROM DEVOPROV WHERE CAST(FOLIDEVOPROV AS TEXT)=?", (folio,)).fetchone()
                if not header: raise ValueError("No existe la devolución al proveedor")
                if header["STATDEVOPROV"] == 2: raise ValueError("La devolución ya estaba cancelada")
                lines = old.execute("""SELECT CLAVREVIDETADEVOPROV revista,CLAVEDICDETADEVOPROV edicion,
                    CANTREVIDETADEVOPROV cantidad FROM DETADEVOPROV WHERE FOLIDETADEVOPROV=? AND STATDETADEVOPROV<>2""", (int(folio),)).fetchall()
                movement, sign = "CANCELACION DE DEVOLUCION PROVEEDOR", 1
                store = "DEVOLUCIONES" if str(header["FOLICOMPDEVOPROV"] or "").upper().startswith("D") else "BODEGA"
                party_table, party_id, balance = "suppliers", str(header["CLAVPROVDEVOPROV"]), number(header["TOTADEVOPROV"])

            resolved = []
            for line in lines:
                edition = db.execute("""SELECT e.id,e.stock,e.stock_returns,p.title FROM editions e
                    JOIN publications p ON p.id=e.publication_id WHERE p.code=? AND e.legacy_code=?""",
                    (str(line["revista"]).strip(), str(line["edicion"]).strip())).fetchone()
                if not edition: raise ValueError(f"No se encontró la edición {line['revista']}/{line['edicion']}")
                quantity = int(line["cantidad"] or 0) * sign
                available = edition["stock_returns"] if store=="DEVOLUCIONES" else edition["stock"]
                if quantity < 0 and available < -quantity:
                    raise ValueError(f"Existencia insuficiente para cancelar: {edition['title']}")
                resolved.append((edition["id"], quantity))
            cancellation_id = db.execute("INSERT INTO legacy_cancellations(category,folio,canceled_at,reason) VALUES(?,?,?,?)",
                (category, folio, date.today().isoformat(), body.get("reason", ""))).lastrowid
            for edition_id, quantity in resolved:
                column = "stock_returns" if store=="DEVOLUCIONES" else "stock"
                db.execute(f"UPDATE editions SET {column}={column}+? WHERE id=?", (quantity, edition_id))
                db.execute("INSERT INTO stock_ledger VALUES(NULL,?,?,?,?,?,?)",
                           (-cancellation_id, edition_id, store, quantity, movement, date.today().isoformat()))
            if balance:
                db.execute(f"UPDATE {party_table} SET balance=balance+? WHERE code=?", (balance, party_id))
        return jsonify({"ok": True, "id": cancellation_id, "lines": len(resolved)})
    except (ValueError, sqlite3.IntegrityError) as exc:
        return jsonify({"error": str(exc)}), 400


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


@app.post("/api/documents/<int:document_id>/generate-orders")
def generate_orders(document_id: int):
    with connection() as db:
        document = db.execute("SELECT * FROM documents WHERE id=? AND kind='COMPRA' AND status=1", (document_id,)).fetchone()
        if not document:
            return jsonify({"error": "No existe una compra activa con ese folio interno"}), 404
        if db.execute("SELECT 1 FROM orders WHERE purchase_id=?", (-document_id,)).fetchone():
            return jsonify({"error": "Los pedidos de esta compra ya fueron generados"}), 409
        order_ids = {}
        allocated_total = 0
        for line in db.execute("""SELECT i.*,e.publication_id FROM document_items i
                                  JOIN editions e ON e.id=i.edition_id WHERE i.document_id=?""", (document_id,)).fetchall():
            remaining = int(line["quantity"])
            packages = db.execute("""SELECT k.*,c.priority,c.distribution_order FROM packages k
                JOIN customers c ON c.id=k.customer_id WHERE k.publication_id=? AND k.active=1 AND c.active=1
                ORDER BY c.priority,c.distribution_order,c.id""", (line["publication_id"],)).fetchall()
            for package in packages:
                quantity = min(int(package["quantity"]), remaining)
                if quantity <= 0: continue
                customer_id = package["customer_id"]
                if customer_id not in order_ids:
                    order_id = db.execute("SELECT COALESCE(MAX(id),0)+1 FROM orders").fetchone()[0]
                    db.execute("INSERT INTO orders VALUES(?,?,?,?,2)",
                               (order_id, customer_id, document["document_date"], -document_id))
                    order_ids[customer_id] = order_id
                item_id = db.execute("SELECT COALESCE(MAX(id),0)+1 FROM order_items").fetchone()[0]
                db.execute("INSERT INTO order_items VALUES(?,?,?,?,?)",
                           (item_id, order_ids[customer_id], line["publication_id"], line["edition_id"], quantity))
                db.execute("UPDATE editions SET reserved=reserved+? WHERE id=?", (quantity, line["edition_id"]))
                remaining -= quantity; allocated_total += quantity
                if remaining == 0: break
    return jsonify({"ok": True, "orders": len(order_ids), "copies": allocated_total})


@app.get("/api/reports/<slug>")
def report(slug: str):
    if not LEGACY_DB_PATH.exists():
        return jsonify({"error": "Todavía no se ha migrado el historial del sistema original"}), 404
    start = request.args.get("start", "1900-01-01")
    end = request.args.get("end", "2999-12-31")
    code = request.args.get("code", "").strip()
    limit = min(max(int(request.args.get("limit", 1000)), 1), 10000)
    reports = {
        "purchases": ("""SELECT F.FOLIINTEFACTCOMP Folio,F.FOLIFACTCOMP Factura,
            substr(F.FECHENTRFACTCOMP,1,10) Fecha,F.CLAVPROVFACTCOMP Clave,P.NOMBPROV Proveedor,
            F.EXENFACTCOMP Exento,F.GRABFACTCOMP Gravado,F.IVAFACTCOMP IVA,F.TOTAFACTCOMP Total,
            CASE F.STATFACTCOMP WHEN 2 THEN 'CANCELADA' ELSE 'ACTIVA' END Estado
            FROM FACTCOMP F JOIN PROVEEDORES P ON P.CLAVPROV=F.CLAVPROVFACTCOMP
            WHERE substr(F.FECHENTRFACTCOMP,1,10) BETWEEN ? AND ?""", "F.CLAVPROVFACTCOMP", "F.FECHENTRFACTCOMP DESC"),
        "sales": ("""SELECT F.FOLIFACTVENT Folio,substr(F.FECHFACTVENT,1,10) Fecha,
            F.CLAVCLIEFACTVENT Clave,C.NOMBCLIE Cliente,F.TIPOVENTFACTVENT Tipo,
            F.EXENFACTVENT Exento,F.GRABFACTVENT Gravado,F.IVAFACTVENT IVA,F.TOTAFACTVENT Total,
            CASE F.STATFACTVENT WHEN 2 THEN 'CANCELADA' ELSE 'ACTIVA' END Estado
            FROM FACTVENT F JOIN CLIENTES C ON C.CLAVCLIE=F.CLAVCLIEFACTVENT
            WHERE substr(F.FECHFACTVENT,1,10) BETWEEN ? AND ?""", "F.CLAVCLIEFACTVENT", "F.FECHFACTVENT DESC"),
        "customer-returns": ("""SELECT D.FOLIDEVOCLIE Folio,substr(D.FECHDEVOCLIE,1,10) Fecha,
            D.CLAVCLIEDEVOCLIE Clave,C.NOMBCLIE Cliente,D.TIPODEVOCLIE Tipo,D.TOTADEVOCLIE Total,
            CASE D.STATDEVOCLIE WHEN 2 THEN 'CANCELADA' ELSE 'ACTIVA' END Estado
            FROM DEVOCLIE D JOIN CLIENTES C ON C.CLAVCLIE=D.CLAVCLIEDEVOCLIE
            WHERE substr(D.FECHDEVOCLIE,1,10) BETWEEN ? AND ?""", "D.CLAVCLIEDEVOCLIE", "D.FECHDEVOCLIE DESC"),
        "supplier-returns": ("""SELECT D.FOLIDEVOPROV Folio,D.FOLICOMPDEVOPROV Referencia,
            substr(D.FECHDEVOPROV,1,10) Fecha,D.CLAVPROVDEVOPROV Clave,P.NOMBPROV Proveedor,
            D.TOTADEVOPROV Total,D.STATDEVOPROV Estado
            FROM DEVOPROV D JOIN PROVEEDORES P ON P.CLAVPROV=D.CLAVPROVDEVOPROV
            WHERE substr(D.FECHDEVOPROV,1,10) BETWEEN ? AND ?""", "D.CLAVPROVDEVOPROV", "D.FECHDEVOPROV DESC"),
        "receivables": ("""SELECT X.NOCUENCOBR Movimiento,substr(X.FECHENTRCUENCOBR,1,10) Fecha,
            X.CLAVCLIECUENCOBR Clave,C.NOMBCLIE Cliente,T.NOMBCUEN Concepto,X.DOCUCUENCOBR Documento,
            X.CARGCUENCOBR Cargo,X.ABONCUENCOBR Abono,X.REFECUENCOBR Referencia
            FROM CUENXCOBR X JOIN CLIENTES C ON C.CLAVCLIE=X.CLAVCLIECUENCOBR
            JOIN CUENTAS T ON T.CLAVCUEN=X.CLAVCUENCUENCOBR
            WHERE X.STATCUENCOBR<>2 AND substr(X.FECHENTRCUENCOBR,1,10) BETWEEN ? AND ?""", "X.CLAVCLIECUENCOBR", "X.FECHENTRCUENCOBR DESC"),
        "payables": ("""SELECT X.FOLICUENPORPAGA Movimiento,substr(X.FECHENTRCUENPORPAGA,1,10) Fecha,
            X.CLAVPROVCUENPORPAGA Clave,P.NOMBPROV Proveedor,T.NOMBCUEN Concepto,
            X.NUMEDOCUCUENPORPAGA Documento,X.CANTCUENPORPAGA Importe,X.SALDCUENPORPAGA Saldo
            FROM CUENPORPAGA X JOIN PROVEEDORES P ON P.CLAVPROV=X.CLAVPROVCUENPORPAGA
            JOIN CUENTAS T ON T.CLAVCUEN=X.CLAVCUENCUENPORPAGA
            WHERE X.STATCUENPORPAGA<>2 AND substr(X.FECHENTRCUENPORPAGA,1,10) BETWEEN ? AND ?""", "X.CLAVPROVCUENPORPAGA", "X.FECHENTRCUENPORPAGA DESC"),
        "cash": ("""SELECT R.NOPARTCAJAREGI Movimiento,substr(R.FECHCAJAREGI,1,10) Fecha,
            R.CLAVCLIECAJAREGI Clave,C.NOMBCLIE Cliente,R.TOTACOBRCAJAREGI Cobrado,
            R.EFECCAJAREGI Efectivo,R.CAMBCAJAREGI Cambio,R.RETICAJAREGI Retiro,R.OBSEVALECAJAREGI Observaciones
            FROM CAJAREGI R JOIN CLIENTES C ON C.CLAVCLIE=R.CLAVCLIECAJAREGI
            WHERE R.STATCAJAREGI<>2 AND substr(R.FECHCAJAREGI,1,10) BETWEEN ? AND ?""", "R.CLAVCLIECAJAREGI", "R.FECHCAJAREGI DESC"),
        "orders": ("""SELECT P.FOLIPEDI Folio,substr(P.FECHPEDI,1,10) Fecha,P.CLAVCLIEPEDI Clave,
            C.NOMBCLIE Cliente,P.FOLICOMPPEDI Compra,P.STATPEDI Estado,
            COALESCE(SUM(D.CANTDETAPEDI),0) Revistas
            FROM PEDIDOS P JOIN CLIENTES C ON C.CLAVCLIE=P.CLAVCLIEPEDI
            LEFT JOIN DETAPEDI D ON D.FOLIDETAPEDI=P.FOLIPEDI
            WHERE substr(P.FECHPEDI,1,10) BETWEEN ? AND ?""", "P.CLAVCLIEPEDI", "P.FECHPEDI DESC", " GROUP BY P.FOLIPEDI"),
        "distribution": ("""SELECT P.CLAVCLIEPAQU Clave,C.NOMBCLIE Cliente,C.RUTACLIE Ruta,
            P.CLAVREVIPAQU Revista,R.TITUREVI Titulo,P.CANTREVIPAQU Cantidad,
            substr(P.FECHREVIREPA,1,10) Fecha
            FROM PAQUETES P JOIN CLIENTES C ON C.CLAVCLIE=P.CLAVCLIEPAQU
            JOIN REVISTAS R ON R.CLAVREVI=P.CLAVREVIPAQU
            WHERE P.STATREVIPAQU<>2 AND substr(COALESCE(P.FECHREVIREPA,'2999-01-01'),1,10) BETWEEN ? AND ?""", "P.CLAVCLIEPAQU", "C.RUTACLIE,P.CLAVCLIEPAQU,R.TITUREVI"),
        "inventory": ("""SELECT X.CLAVREVIEXIS Revista,R.TITUREVI Titulo,X.CLAVEDICEXIS Edicion,
            X.NUMEEDICEXIS Numero,E.PRECEDIC Precio,X.EXISACTUBODEEXIS Bodega,
            X.EXISACTUDEVOEXIS Devoluciones,(X.EXISACTUBODEEXIS+X.EXISACTUDEVOEXIS) Total
            FROM EXISTENCIAS X JOIN REVISTAS R ON R.CLAVREVI=X.CLAVREVIEXIS
            JOIN EDICIONES E ON E.CLAVEDIC=X.CLAVEDICEXIS AND E.CLAVREVIEDIC=X.CLAVREVIEXIS
            WHERE 1=1""", "X.CLAVREVIEXIS", "R.TITUREVI,X.NUMEEDICEXIS DESC", "", False),
        "transfers": ("""SELECT A.FOLIAJUS Folio,substr(A.FECHAJUS,1,10) Fecha,A.ORIGAJUS Origen,
            A.DESTAJUS Destino,T.CONCTIPO Concepto,A.OBSERVACION Observaciones,
            COALESCE(SUM(D.CANTDETAAJUS),0) Revistas,A.STATAJUS Estado
            FROM AJUSTES A JOIN TIPOMOVI T ON T.CLAVTIPO=A.TIPOMOVIAJUS
            LEFT JOIN DETAAJUS D ON D.FOLIAJUSDETAAJUS=A.FOLIAJUS
            WHERE substr(A.FECHAJUS,1,10) BETWEEN ? AND ?""", "A.FOLIAJUS", "A.FECHAJUS DESC", " GROUP BY A.FOLIAJUS"),
    }
    if slug not in reports:
        return jsonify({"error": "Reporte desconocido"}), 404
    specification = reports[slug]
    sql, code_column, ordering = specification[:3]
    group = specification[3] if len(specification) > 3 else ""
    uses_dates = specification[4] if len(specification) > 4 else True
    params = [start, end] if uses_dates else []
    if code:
        sql += f" AND CAST({code_column} AS TEXT)=?"
        params.append(code)
    sql += group + f" ORDER BY {ordering} LIMIT ?"
    params.append(limit)
    with legacy_connection() as db:
        cursor = db.execute(sql, params)
        result = [dict(row) for row in cursor.fetchall()]
        columns = [item[0] for item in cursor.description]
    numeric_columns = {"Exento", "Gravado", "IVA", "Total", "Cargo", "Abono", "Saldo", "Importe", "Precio", "Cobrado", "Efectivo", "Cambio", "Retiro"}
    totals = {column: round(sum(number(row.get(column)) for row in result), 2) for column in columns if column in numeric_columns}
    return jsonify({"columns": columns, "rows": result, "totals": totals, "count": len(result)})


if __name__ == "__main__":
    initialize_database()
    threading.Timer(1.0, lambda: webbrowser.open("http://127.0.0.1:5000")).start()
    app.run(host="127.0.0.1", port=5000, debug=False)
