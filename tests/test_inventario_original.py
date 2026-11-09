import sys
import unittest
from pathlib import Path


RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "tools"))

from extraer_estructura_ventanas import LectorDFM, bloques  # noqa: E402
from inventariar_ventanas_originales import extraer  # noqa: E402


EJECUTABLE = RAIZ / "legado-local" / "Distribuidora.exe"


@unittest.skipUnless(EJECUTABLE.exists(), "El ejecutable original sólo está disponible en el entorno local")
class InventarioOriginalTest(unittest.TestCase):
    def test_cantidad_de_recursos_y_ventanas_visibles(self):
        inventario = extraer(EJECUTABLE)
        self.assertEqual(229, len(inventario))
        self.assertEqual(188, sum(bool(x["visible_para_usuario"]) for x in inventario))
        self.assertNotIn("Sin clasificar", {x["categoria"] for x in inventario})

    def test_todos_los_dfm_se_pueden_extraer(self):
        extraidos = []
        for registro, contenido in bloques(EJECUTABLE):
            estructura = LectorDFM(contenido).objeto()
            self.assertEqual(registro["nombre_original"], estructura["nombre"])
            extraidos.append(estructura)
        self.assertEqual(229, len(extraidos))

    def test_ventana_de_actualizacion_conserva_su_especificacion(self):
        for registro, contenido in bloques(EJECUTABLE):
            if registro["nombre_original"] != "FActuExis":
                continue
            ventana = LectorDFM(contenido).objeto()
            self.assertEqual("Actualizacion de Existencias", ventana["propiedades"]["Caption"])
            panel = ventana["controles"][0]
            nombres = {control["nombre"] for control in panel["controles"]}
            self.assertIn("BBActuActuExis", nombres)
            self.assertIn("BBSaliActuExis", nombres)
            self.assertIn("EClavReviActuExis", nombres)
            return
        self.fail("No se encontró FActuExis")


if __name__ == "__main__":
    unittest.main()
