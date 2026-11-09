import sys
import tempfile
import unittest
from pathlib import Path


RAIZ = Path(__file__).resolve().parents[1]
APLICACION = RAIZ / "PublicacionesEspindola"
sys.path.insert(0, str(APLICACION))

import app as aplicacion  # noqa: E402


class PublicacionWebTest(unittest.TestCase):
    def setUp(self):
        self.temporal = tempfile.TemporaryDirectory()
        self.valores_originales = (
            aplicacion.DATA_DIR,
            aplicacion.DB_PATH,
            aplicacion.LEGACY_DB_PATH,
            aplicacion.COMPANY_IMAGE_PATH,
        )
        datos = Path(self.temporal.name)
        aplicacion.DATA_DIR = datos
        aplicacion.DB_PATH = datos / "sadyv.db"
        aplicacion.LEGACY_DB_PATH = datos / "historial_que_no_existe.db"
        aplicacion.COMPANY_IMAGE_PATH = datos / "imagen_empresa"
        aplicacion.initialize_database()
        aplicacion.app.config.update(TESTING=True)
        self.cliente = aplicacion.app.test_client()

    def tearDown(self):
        (
            aplicacion.DATA_DIR,
            aplicacion.DB_PATH,
            aplicacion.LEGACY_DB_PATH,
            aplicacion.COMPANY_IMAGE_PATH,
        ) = self.valores_originales
        self.temporal.cleanup()

    def test_inicio_y_estado_del_servicio(self):
        self.assertEqual(200, self.cliente.get("/").status_code)
        respuesta = self.cliente.get("/api/estado")
        self.assertEqual(200, respuesta.status_code)
        self.assertEqual("disponible", respuesta.get_json()["estado"])
        self.assertFalse(respuesta.get_json()["historial_original"])

    def test_catalogos_funcionan_con_base_nueva(self):
        respuesta = self.cliente.post("/api/suppliers", json={"code": "PROV-1", "name": "Proveedor de prueba"})
        self.assertEqual(200, respuesta.status_code)
        respuesta = self.cliente.post("/api/customers", json={"code": "CLI-1", "name": "Cliente de prueba"})
        self.assertEqual(200, respuesta.status_code)
        self.assertEqual(1, len(self.cliente.get("/api/suppliers?q=prueba").get_json()))
        self.assertEqual(1, len(self.cliente.get("/api/customers?q=prueba").get_json()))

    def test_reportes_abren_sin_base_del_sistema_anterior(self):
        reportes = (
            "inventory", "purchases", "sales", "customer-returns",
            "supplier-returns", "receivables", "payables", "cash",
            "orders", "distribution", "transfers",
        )
        for reporte in reportes:
            with self.subTest(reporte=reporte):
                respuesta = self.cliente.get(f"/api/reports/{reporte}")
                self.assertEqual(200, respuesta.status_code)
                self.assertIn("rows", respuesta.get_json())

    def test_cancelar_un_solo_producto_y_una_cantidad_parcial(self):
        with aplicacion.connection() as db:
            customer_id = db.execute(
                "INSERT INTO customers(code,name,active) VALUES('CLI-VENTA','Cliente venta',1)"
            ).lastrowid
            publication_id = db.execute(
                "INSERT INTO publications(code,title,tax,active) VALUES('REV-1','Revista uno',0,1)"
            ).lastrowid
            edition_id = db.execute(
                """INSERT INTO editions(publication_id,number,name,price,stock,active)
                   VALUES(?,'1','Primera',100,10,1)""",
                (publication_id,),
            ).lastrowid

        sale = self.cliente.post("/api/documents", json={
            "kind": "VENTA", "operation_date": "2026-11-09",
            "party_code": "CLI-VENTA", "sale_type": "CREDITO",
            "items": [{"edition_id": edition_id, "quantity": 2, "price": 100, "discount": 0}],
        })
        self.assertEqual(200, sale.status_code)
        sale_data = sale.get_json()

        detail = self.cliente.get(f"/api/sales/{sale_data['folio']}/items").get_json()
        self.assertEqual(2, detail["items"][0]["available_quantity"])
        item_id = detail["items"][0]["id"]

        cancellation = self.cliente.post(f"/api/sales/{sale_data['folio']}/cancel-items", json={
            "reason": "Producto capturado por error",
            "items": [{"item_id": item_id, "quantity": 1}],
        })
        self.assertEqual(200, cancellation.status_code)
        self.assertEqual("PARCIAL", cancellation.get_json()["document_status"])
        self.assertEqual(100, cancellation.get_json()["document_total"])

        with aplicacion.connection() as db:
            edition = db.execute("SELECT stock FROM editions WHERE id=?", (edition_id,)).fetchone()
            customer = db.execute("SELECT balance FROM customers WHERE id=?", (customer_id,)).fetchone()
            document = db.execute("SELECT total,status FROM documents WHERE id=?", (sale_data["id"],)).fetchone()
            item = db.execute("SELECT quantity,cancelled_quantity FROM document_items WHERE id=?", (item_id,)).fetchone()
            audit = db.execute("SELECT quantity,reason FROM item_cancellations WHERE item_id=?", (item_id,)).fetchone()
        self.assertEqual(9, edition["stock"])
        self.assertEqual(100, customer["balance"])
        self.assertEqual(100, document["total"])
        self.assertEqual(1, document["status"])
        self.assertEqual(1, item["cancelled_quantity"])
        self.assertEqual("Producto capturado por error", audit["reason"])

        detail = self.cliente.get(f"/api/sales/{sale_data['folio']}/items").get_json()
        self.assertEqual(1, detail["items"][0]["available_quantity"])
        self.assertEqual(100, detail["items"][0]["available_amount"])
        sales_report = self.cliente.get("/api/reports/sales?start=2026-01-01&end=2026-12-31").get_json()
        current_sale = next(row for row in sales_report["rows"] if row["Folio"] == sale_data["folio"])
        self.assertEqual("PARCIAL", current_sale["Estado"])
        backup = self.cliente.get("/api/respaldo/completo")
        self.assertEqual(200, backup.status_code)
        self.assertEqual("application/zip", backup.mimetype)

        excessive = self.cliente.post(f"/api/sales/{sale_data['folio']}/cancel-items", json={
            "reason": "Intento inválido", "items": [{"item_id": item_id, "quantity": 2}],
        })
        self.assertEqual(400, excessive.status_code)

        final_cancellation = self.cliente.post(f"/api/sales/{sale_data['folio']}/cancel-items", json={
            "reason": "Cancelar la copia restante", "items": [{"item_id": item_id, "quantity": 1}],
        })
        self.assertEqual(200, final_cancellation.status_code)
        self.assertEqual("CANCELADA", final_cancellation.get_json()["document_status"])
        self.assertEqual(0, final_cancellation.get_json()["document_total"])

        with aplicacion.connection() as db:
            edition = db.execute("SELECT stock FROM editions WHERE id=?", (edition_id,)).fetchone()
            customer = db.execute("SELECT balance FROM customers WHERE id=?", (customer_id,)).fetchone()
            document = db.execute("SELECT total,status FROM documents WHERE id=?", (sale_data["id"],)).fetchone()
            item = db.execute("SELECT cancelled_quantity FROM document_items WHERE id=?", (item_id,)).fetchone()
            audit_count = db.execute("SELECT COUNT(*) total FROM item_cancellations WHERE item_id=?", (item_id,)).fetchone()
        self.assertEqual(10, edition["stock"])
        self.assertEqual(0, customer["balance"])
        self.assertEqual(0, document["total"])
        self.assertEqual(2, document["status"])
        self.assertEqual(2, item["cancelled_quantity"])
        self.assertEqual(2, audit_count["total"])


if __name__ == "__main__":
    unittest.main()
