"""Pasa catálogos e inventario completos de legacy.db a la base de trabajo."""

from __future__ import annotations

import argparse
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path


def rows(db, sql):
    db.row_factory = sqlite3.Row
    return db.execute(sql).fetchall()


def sync(app_db_path: Path, legacy_db_path: Path, force: bool) -> None:
    import sys
    sys.path.insert(0, str(app_db_path.parent.parent))
    import app

    app.DB_PATH = app_db_path
    app.initialize_database()
    app_db = sqlite3.connect(app_db_path)
    app_db.row_factory = sqlite3.Row
    legacy = sqlite3.connect(legacy_db_path)
    legacy.row_factory = sqlite3.Row
    try:
        documents = app_db.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
        if documents and not force:
            raise SystemExit("Hay documentos nuevos. No se reemplazarán catálogos sin --force.")
        backup = app_db_path.with_name(f"{app_db_path.stem}.before-full-sync.db")
        app_db.commit()
        shutil.copy2(app_db_path, backup)

        with app_db:
            for table in ("order_items", "orders", "packages", "editions", "publications", "suppliers", "customers",
                          "priorities", "customer_groups", "routes", "employees", "account_types", "movement_types",
                          "cash_details", "cash_register"):
                app_db.execute(f"DELETE FROM {table}")

            app_db.executemany(
                """INSERT INTO customers
                (id,code,name,rfc,phone,address,city,credit_limit,balance,discount,active,priority,group_id,
                 legal_name,postal_code,state,fax,classification,zone,payment_condition,payment_term,
                 first_payment_day,second_payment_day,buyer,payer,representative,return_percentage,route_id,distribution_order)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                [(r["CLAVCLIE"], str(r["CLAVCLIE"]), r["NOMBCLIE"] or "SIN NOMBRE", r["RFCCLIE"] or "",
                  r["TELECLIE"] or "", r["DIRECLIE"] or "", r["CIUDCLIE"] or "", r["LIMICREDCLIE"] or 0,
                  r["SALDACTUCLIE"] or 0, r["DESCCLIE"] or 0, int((r["STATCLIE"] or 0)==1), r["PRIOCLIE"] or "",
                  r["CLAVGRUPCLIE"], r["RAZOSOCICLIE"] or "", r["CODIPOSTCLIE"] or "", r["ESTACLIE"] or "",
                  r["FAXCLIE"] or "", r["CLASCLIE"] or "", r["ZONACLIE"] or "", r["TIPOCONDCLIE"] or "",
                  r["PLAZCLIE"] or 0, r["DIAPAGOCLIE"] or "", r["SEGDIAPAGOCLIE"] or "", r["PERSENCACOMPCLIE"] or "",
                  r["PERSENCAPAGOCLIE"] or "", r["REPRCLIE"] or "", r["PORCDEVO"] or 100, r["RUTACLIE"], r["REPACLIE"] or 1)
                 for r in rows(legacy, "SELECT * FROM CLIENTES")],
            )
            app_db.executemany(
                """INSERT INTO suppliers
                (id,code,name,rfc,phone,email,address,balance,active,legal_name,city,state,postal_code,mobile,
                 payment_condition,supplier_return_days,customer_return_days) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                [(r["CLAVPROV"], str(r["CLAVPROV"]), r["NOMBPROV"] or "SIN NOMBRE", r["RFCPROV"] or "",
                  r["TELEPROV"] or "", r["EMAIPROV"] or "", r["DIREPROV"] or "", r["SALDPROV"] or 0,
                  int((r["STATPROV"] or 0)==1), r["RAZOSOCIPROV"] or "", r["CIUDPROV"] or "", r["ESTAPROV"] or "",
                  r["CODIPOSTPROV"] or "", r["CELUPROV"] or "", r["CONDPAGOPROV"] or "",
                  r["DIASLIMIDEVOPROV"] or 0, r["DIASLIMIDEVOCLIEPROV"] or 0)
                 for r in rows(legacy, "SELECT * FROM PROVEEDORES")],
            )
            publications = rows(legacy, "SELECT * FROM REVISTAS ORDER BY CLAVREVI")
            publication_ids = {r["CLAVREVI"]: index for index, r in enumerate(publications, 1)}
            app_db.executemany(
                """INSERT INTO publications
                (id,code,title,supplier_id,barcode,tax,monitored,active,supplier_code,supplier_publication_code,top25)
                VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                [(publication_ids[r["CLAVREVI"]], r["CLAVREVI"], r["TITUREVI"] or "SIN TITULO", r["CLAVPROVREVI"],
                  r["CODIBARRREVI"] or "", 16 if r["IVAREVI"]==1 else 0,
                  int(str(r["MONIREVI"] or "").upper()=="SI"), int((r["STATREVI"] or 0)==1),
                  str(r["CLAVPROVREVI"]), r["CLAVREVIPROV"] or "", r["TOP25REVI"] or 0) for r in publications],
            )
            edition_sql = """SELECT E.*, X.EXISACTUBODEEXIS, X.EXISACTUDEVOEXIS
                             FROM EDICIONES E LEFT JOIN EXISTENCIAS X
                             ON X.CLAVEDICEXIS=E.CLAVEDIC AND X.CLAVREVIEXIS=E.CLAVREVIEDIC
                             ORDER BY E.CLAVREVIEDIC,E.NUMEEDIC"""
            app_db.executemany(
                """INSERT INTO editions
                (id,publication_id,number,name,barcode,arrival_date,return_deadline,price,stock,stock_returns,
                 reserved,active,legacy_code,supplier_deadline,customer_discount)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                [(index, publication_ids[r["CLAVREVIEDIC"]], str(r["NUMEEDIC"] or ""), r["NOMBEDIC"] or r["CLAVEDIC"],
                  r["CODIBARREDIC"] or "", r["FECHENTREDIC"] or "", r["FECHVENCCLIEEDIC"] or "", r["PRECEDIC"] or 0,
                  r["EXISACTUBODEEXIS"] or 0, r["EXISACTUDEVOEXIS"] or 0, 0, int((r["STATEDIC"] or 0)==1),
                  r["CLAVEDIC"], r["FECHVENCPROVEDIC"] or "", r["DESCCLIEEDIC"] or 0)
                 for index, r in enumerate(rows(legacy, edition_sql), 1)],
            )
            simple = [
                ("priorities", "INSERT INTO priorities VALUES(?,?)", "SELECT PRIOCLIE,PORCREVICLIE FROM PRIORIDAD"),
                ("customer_groups", "INSERT INTO customer_groups VALUES(?,?,?,?)", "SELECT CLAVGRUPCLIE,NOMBGRUPCLIE,ACUMGRUPCLIE,ESTAGRUPCLIE FROM GRUPCLIE"),
                ("routes", "INSERT INTO routes VALUES(?,?,?)", "SELECT RUTA,NOMBRE,STATUS FROM RUTAS"),
                ("employees", "INSERT INTO employees VALUES(?,?,?,?,?)", "SELECT CLAVEMPL,NOMBEMPL,PUESEMPL,AREATRABEMPL,STATEMPL FROM EMPLEADOS"),
                ("account_types", "INSERT INTO account_types VALUES(?,?,?,?)", "SELECT CLAVCUEN,NOMBCUEN,TIPOCUEN,STATCUEN FROM CUENTAS"),
                ("movement_types", "INSERT INTO movement_types VALUES(?,?,?,?)", "SELECT CLAVTIPO,CONCTIPO,TIPOTIPO,STATTIPO FROM TIPOMOVI"),
            ]
            for _, statement, query in simple:
                app_db.executemany(statement, [tuple(r) for r in rows(legacy, query)])

            package_rows = rows(legacy, "SELECT * FROM PAQUETES")
            app_db.executemany(
                "INSERT INTO packages VALUES(?,?,?,?,?,?)",
                [(r["NOPARTPAQU"], r["CLAVCLIEPAQU"], publication_ids[r["CLAVREVIPAQU"]], r["CANTREVIPAQU"] or 0,
                 r["FECHREVIREPA"] or "", int((r["STATREVIPAQU"] or 0)!=2)) for r in package_rows],
            )
            edition_ids = {(r["publication_code"], r["legacy_code"]): r["id"] for r in app_db.execute(
                """SELECT e.id,p.code publication_code,e.legacy_code FROM editions e
                   JOIN publications p ON p.id=e.publication_id""").fetchall()}
            order_rows = rows(legacy, "SELECT * FROM PEDIDOS")
            app_db.executemany(
                "INSERT INTO orders VALUES(?,?,?,?,?)",
                [(r["FOLIPEDI"], r["CLAVCLIEPEDI"], r["FECHPEDI"] or "", r["FOLICOMPPEDI"], r["STATPEDI"] or 1) for r in order_rows],
            )
            items = []
            for r in rows(legacy, "SELECT * FROM DETAPEDI"):
                edition_id = edition_ids.get((r["CLAVREVIDETAPEDI"], r["CLAVEDICDETAPEDI"]))
                if edition_id:
                    items.append((r["NOPARTDETAPEDI"], r["FOLIDETAPEDI"], publication_ids[r["CLAVREVIDETAPEDI"]], edition_id, r["CANTDETAPEDI"] or 0))
            app_db.executemany("INSERT INTO order_items VALUES(?,?,?,?,?)", items)
        print(f"Sincronización terminada. Respaldo: {backup}")
        print(f"Clientes: {len(rows(legacy,'SELECT CLAVCLIE FROM CLIENTES')):,}")
        print(f"Revistas: {len(publications):,}; ediciones: {app_db.execute('SELECT COUNT(*) FROM editions').fetchone()[0]:,}")
    finally:
        app_db.close()
        legacy.close()


if __name__ == "__main__":
    cli = argparse.ArgumentParser()
    cli.add_argument("app_db", type=Path)
    cli.add_argument("legacy_db", type=Path)
    cli.add_argument("--force", action="store_true")
    options = cli.parse_args()
    sync(options.app_db.resolve(), options.legacy_db.resolve(), options.force)
