"""Extrae controles y propiedades de los formularios Delphi originales.

La salida sirve como especificación de interfaz: tamaño de la ventana, nombres,
clases, textos, posiciones y dimensiones de sus controles. No ejecuta código
del programa anterior.
"""

from __future__ import annotations

import argparse
import json
import struct
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from inventariar_ventanas_originales import extraer  # noqa: E402


class ErrorDFM(ValueError):
    pass


class LectorDFM:
    def __init__(self, datos: bytes):
        if not datos.startswith(b"TPF0"):
            raise ErrorDFM("El bloque no empieza con TPF0")
        self.datos = datos
        self.posicion = 4

    def tomar(self, cantidad: int) -> bytes:
        fin = self.posicion + cantidad
        if fin > len(self.datos):
            raise ErrorDFM("Fin inesperado del recurso")
        valor = self.datos[self.posicion:fin]
        self.posicion = fin
        return valor

    def entero(self, formato: str) -> int | float:
        cantidad = struct.calcsize(formato)
        return struct.unpack(formato, self.tomar(cantidad))[0]

    def cadena_corta(self) -> str:
        longitud = self.entero("<B")
        return self.tomar(int(longitud)).decode("latin-1", errors="replace")

    def cadena_larga(self, codificacion: str = "latin-1", factor: int = 1) -> str:
        longitud = int(self.entero("<I"))
        return self.tomar(longitud * factor).decode(codificacion, errors="replace")

    def valor(self) -> Any:
        tipo = int(self.entero("<B"))
        if tipo in (0, 13):
            return None
        if tipo == 1:  # lista
            valores = []
            while self.datos[self.posicion] != 0:
                valores.append(self.valor())
            self.posicion += 1
            return valores
        if tipo == 2:
            return self.entero("<b")
        if tipo == 3:
            return self.entero("<h")
        if tipo == 4:
            return self.entero("<i")
        if tipo == 5:  # Extended de 80 bits; se conserva para auditoría
            return {"tipo": "número extendido", "hexadecimal": self.tomar(10).hex()}
        if tipo == 6:
            return self.cadena_corta()
        if tipo == 7:
            return self.cadena_corta()
        if tipo == 8:
            return False
        if tipo == 9:
            return True
        if tipo == 10:
            longitud = int(self.entero("<I"))
            self.tomar(longitud)
            return {"tipo": "datos binarios", "bytes": longitud}
        if tipo == 11:
            valores = []
            while True:
                item = self.cadena_corta()
                if not item:
                    return valores
                valores.append(item)
        if tipo == 12:
            return self.cadena_larga()
        if tipo == 14:  # colección de objetos con propiedades
            elementos = []
            while self.datos[self.posicion] != 0:
                marcador = int(self.entero("<B"))
                if marcador != 1:
                    raise ErrorDFM(f"Marcador de colección inesperado: {marcador}")
                propiedades = self.propiedades()
                elementos.append(propiedades)
            self.posicion += 1
            return elementos
        if tipo == 15:
            return self.entero("<f")
        if tipo == 16:
            return self.entero("<q") / 10000
        if tipo == 17:
            return self.entero("<d")
        if tipo == 18:
            return self.cadena_larga("utf-16-le", 2)
        if tipo == 19:
            return self.entero("<q")
        if tipo == 20:
            return self.cadena_larga("utf-8")
        if tipo == 21:
            return self.entero("<d")
        raise ErrorDFM(f"Tipo de valor desconocido {tipo} en {self.posicion - 1}")

    def propiedades(self) -> dict[str, Any]:
        resultado: dict[str, Any] = {}
        while True:
            nombre = self.cadena_corta()
            if not nombre:
                return resultado
            resultado[nombre] = self.valor()

    def objeto(self) -> dict[str, Any]:
        clase = self.cadena_corta()
        nombre = self.cadena_corta()
        if not clase.startswith("T"):
            raise ErrorDFM(f"Clase inesperada {clase!r} en {self.posicion}")
        resultado = {
            "clase": clase,
            "nombre": nombre,
            "propiedades": self.propiedades(),
            "controles": [],
        }
        while self.posicion < len(self.datos) and self.datos[self.posicion] != 0:
            resultado["controles"].append(self.objeto())
        if self.posicion < len(self.datos):
            self.posicion += 1
        return resultado


def bloques(ruta: Path) -> list[tuple[dict[str, object], bytes]]:
    datos = ruta.read_bytes()
    inventario = extraer(ruta)
    posiciones = [int(registro["posicion_en_ejecutable"]) for registro in inventario]
    resultado = []
    for indice, registro in enumerate(inventario):
        inicio = posiciones[indice]
        fin = posiciones[indice + 1] if indice + 1 < len(posiciones) else len(datos)
        resultado.append((registro, datos[inicio:fin]))
    return resultado


def simplificar(objeto: dict[str, Any]) -> dict[str, Any]:
    propiedades = objeto["propiedades"]
    conservar = (
        "Caption", "Text", "Hint", "Left", "Top", "Width", "Height",
        "ClientWidth", "ClientHeight", "Align", "Visible", "Enabled",
        "TabOrder", "MaxLength", "Items.Strings", "Columns", "DataField",
        "DataSource", "OnClick", "OnChange", "OnExit", "OnKeyPress",
    )
    return {
        "clase": objeto["clase"],
        "nombre": objeto["nombre"],
        "propiedades": {k: v for k, v in propiedades.items() if k in conservar},
        "controles": [simplificar(control) for control in objeto["controles"]],
    }


def main() -> None:
    predeterminado = Path(__file__).resolve().parents[1] / "legado-local" / "Distribuidora.exe"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ejecutable", nargs="?", type=Path, default=predeterminado)
    parser.add_argument("--ventana", help="Nombre original de una ventana; sin este dato se extraen todas")
    parser.add_argument("--completo", action="store_true", help="Incluye todas las propiedades")
    argumentos = parser.parse_args()

    resultados = []
    errores = []
    for registro, bloque in bloques(argumentos.ejecutable):
        if argumentos.ventana and registro["nombre_original"].lower() != argumentos.ventana.lower():
            continue
        try:
            arbol = LectorDFM(bloque).objeto()
            resultados.append({"inventario": registro, "estructura": arbol if argumentos.completo else simplificar(arbol)})
        except (ErrorDFM, IndexError, struct.error) as error:
            errores.append({"ventana": registro["nombre_original"], "error": str(error)})

    if argumentos.ventana and not resultados:
        raise SystemExit(f"No se pudo extraer {argumentos.ventana}: {errores}")
    salida = {"ventanas_extraidas": len(resultados), "errores": errores, "ventanas": resultados}
    print(json.dumps(salida, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
