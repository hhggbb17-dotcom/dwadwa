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


if __name__ == "__main__":
    unittest.main()
