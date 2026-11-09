"""Inventaría los formularios Delphi compilados dentro de Distribuidora.exe.

El programa original guarda cada formulario como un recurso DFM binario que
empieza con la firma ``TPF0``. Este script no ejecuta el sistema antiguo ni
modifica sus archivos: únicamente lee esos recursos y genera un inventario
auditable en JSON o Markdown.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


CAPTURA = {
    "FActuExis", "FActuExisRevi", "FActuPaqu", "FActuPaquLocal",
    "FActuProv", "FActuSaldProv", "faltadecli", "FaltadeCuenCobr",
    "FaltadeCuenPaga", "faltadecuentas", "FaltadeDevoProv",
    "FaltadeDevoProvNew", "faltadeedic", "faltadeempl", "FaltadeFactComp",
    "Faltadeprov", "faltaderev", "FAltaPaqu", "FAltaPaquxGrup", "FBita",
    "FCajaRegi", "FCambFechVenc", "FCaptFoliRefe", "FCodiBarr",
    "FCodibarrEdic", "FContEntr", "FCortCaja", "FDatoEdicNuevTras",
    "FFactComp", "FFactDevo", "Ffactgrup", "FFactVent", "FFecha",
    "FGrupClie", "FKits", "fMenuPrin", "FPerm", "FPrioClie", "FRepaPedi",
    "FRepaReviNuev", "FRepClie", "FRepRuta", "FRespaldo", "FRestaura",
    "FResuDevoclie", "FReviMoni", "FReviTras", "FTipoMovi", "FTras",
    "FVerPedi",
}

CONSULTA = {
    "FbuscRevi", "FCataAsig", "FCataCuenporCobr", "FCataCuenporPaga",
    "FCataRuta", "FCataTipoMovi", "Fcatcli", "Fcatcuentas", "Fcatedic",
    "Fcatempl", "fCatprov", "Fcatrev", "FConsContDevoClie",
    "FConsContFactVent", "FConsCortCaja", "FConsCuenCobr", "FConsCuenPaga",
    "FConsDevoClie", "FConsDevoProv", "FConsDevoProvCons",
    "FConsDevoProvNew", "FConsDevoxFecha", "FConsEdicReviVenc",
    "FConsEstaCuenCobr", "FConsEstaCuenPaga", "FConsFactComp",
    "FConsFactVent", "FConsGrupEstaCuenCobr", "FConsGrupxVenta",
    "FConsPediGral", "FConsPreDevoClie", "FConsProdxComp", "FConsTipoMovi",
    "FConsTras", "FConsVentCont", "FConsVentxFecha", "FCuenCobrCons",
    "FCuenPagaCons", "FDetaConsPedi", "FDetaCuenPagaCons", "FDevoProvCons",
    "FDevoProvConsCons", "FDevoProvConsConsNew", "FFactCons", "FReviCons",
    "FReviDevoProvConsCons", "FTrasCons", "FVerConsContDetaFactVent",
    "FVerConsContFactVent", "FVerConsCortCaja", "FVerConsDetaDevoClie",
    "FVerConsDetaFactVent", "FVerConsDevoClie", "FVerConsFactVent",
    "FVerConsPedi", "FVistaFactura",
}

REPORTE = {
    "FConifReport", "FConsRepoSAT", "FExisConsRepo", "FImprCredEmpl",
    "FImprDevo", "FImprFact", "FImprFactRap", "FImprListVoce", "FImprTras",
    "FInveRevi", "FInveReviExcel", "FRepoChecaEmpl", "FRepoConsDevoxFecha",
    "FRepoConsVentxFecha", "FRepoCuen", "FRepoDistClie", "FRepoEmpl",
    "FRepoEstaCompDevoxProv", "FRepoEstaCuenCobr", "FRepoEstaCuenGral",
    "FRepoEstaCuenPaga", "FRepoEstaxProv", "FRepoExis", "FRepoExisExcel",
    "FRepoExisTop25", "FRepoFactComp", "FRepoGrupEstaCuenCobr",
    "FRepoInveRevi", "FRepoLiquProv", "FRepoLocaCerr", "FRepoPapeAbono",
    "FRepoPapeClie", "fRepoPapeConsFactVent", "fRepoPapeConsGrupxVenta",
    "FRepoPapeConsPedi", "FRepoPapeCortCxC", "FRepoPapeCortDevo",
    "FRepoPapeCortDevoxCanc", "FRepoPapeCortFactVent",
    "FRepoPapeCortFactVentPagaCaja", "FRepoPapeCortFactVentPendPago",
    "FRepoPapeCortMoviClie", "FRepoPapeCortMoviClieDeta",
    "FRepoPapeCortMoviClieGral", "FRepoPapeCortResuTota", "FRepoPapeCortReti",
    "FRepoPapeCortSaldCxC", "FRepoPapeCortVale", "FRepoPapeCuen",
    "FRepoPapeCuenPaga", "fRepoPapeDevoClie", "FRepoPapeDevoProv",
    "FRepoPapeDevoProvCons", "FRepoPapeDevoProvConsCons", "FRepoPapeEmpl",
    "FRepoPapeFactComp", "FRepoPapeFactCompRepo", "FRepoPapeFactCompRepoDevo",
    "FRepoPapeFactCompRepoTota", "FRepoPapeGeneCuenCobr",
    "FRepoPapeGeneCuenPaga", "FRepoPapeHojaDoblDevoClie", "FRepoPapeLiquProv",
    "FRepoPapeListVoce", "FRepoPapePaqu", "FRepoPapePreDevoClie",
    "FRepoPapeProv", "FRepoPapeRepoExis", "FRepoPapeRevi",
    "FRepoPapeReviNoRepa", "FRepoPapeReviTras", "FRepoPapeRuta",
    "FRepoPapeTodaDevoClie", "FRepoPapeTodaFactVent", "FRepoPapeTotaDevoProv",
    "FRepoPapeTotaFactComp", "FRepoPapeTras", "FRepoPaqu", "FRepoPaquClie",
    "FRepoProv", "FRepoRevi", "FRepoVentNetasxProv",
}

MODULOS_DATOS = {
    "DMConsPedi", "DMPaqu", "FDMAjus", "FDMCajaRegi", "FDMCli",
    "FDmConsDevoClie", "FDmConsFactVent", "FDmCortCaja", "FDMCuen",
    "FDMCuenPaga", "FDmCxC", "FDMDevoProv", "FDMEdic", "FdmEmpl",
    "FDMExistencias", "fdmfactcomp", "FDMFactDevo", "FDMFactVent", "FDMFoli",
    "FdmPedi", "fdmprincipal", "FDMProv", "FDMRev", "FDMReviNoRepa",
}

INTERNOS = {
    "CodeGenerateFrm", "EditProductFrm", "KeyGenerateFrm", "KeyMaintFrm",
    "LoginDialog", "PasswordDialog", "PasswordDlg", "QRAboutBox", "QRCompEd",
    "QREnvironmentEditor", "QRExprEditorForm", "QRExpressionBuilder",
    "QRLabelEditorForm", "QRProgressForm", "QRStandardPreview",
    "RzFrmCustomizeToolbar", "SplashForm",
}

CLASIFICACIONES = (
    ("Captura y proceso", CAPTURA),
    ("Consulta y catálogo", CONSULTA),
    ("Reporte e impresión", REPORTE),
    ("Módulo de datos no visible", MODULOS_DATOS),
    ("Diálogo interno o de terceros", INTERNOS),
)


def cadena_corta(datos: bytes, posicion: int) -> tuple[str, int] | None:
    if posicion >= len(datos):
        return None
    longitud = datos[posicion]
    fin = posicion + 1 + longitud
    if not longitud or fin > len(datos):
        return None
    texto = datos[posicion + 1 : fin].decode("latin-1", errors="replace")
    return texto, fin


def titulo_del_bloque(bloque: bytes) -> str:
    coincidencia = re.search(rb"Caption\x06(.)([^\x00]{0,250})", bloque, re.S)
    if not coincidencia:
        return ""
    longitud = coincidencia.group(1)[0]
    inicio = coincidencia.start(2)
    return bloque[inicio : inicio + longitud].decode("latin-1", errors="replace")


def clasificar(nombre: str) -> str:
    for categoria, nombres in CLASIFICACIONES:
        if nombre in nombres:
            return categoria
    return "Sin clasificar"


def extraer(ruta: Path) -> list[dict[str, object]]:
    datos = ruta.read_bytes()
    posiciones = [m.start() for m in re.finditer(re.escape(b"TPF0"), datos)]
    resultados: list[dict[str, object]] = []

    for indice, posicion in enumerate(posiciones):
        clase = cadena_corta(datos, posicion + 4)
        if clase is None:
            continue
        nombre = cadena_corta(datos, clase[1])
        if nombre is None:
            continue
        clase_texto, _ = clase
        nombre_texto, _ = nombre
        if not re.fullmatch(r"T[A-Za-z][A-Za-z0-9_]{1,80}", clase_texto):
            continue
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{1,80}", nombre_texto):
            continue

        siguiente = posiciones[indice + 1] if indice + 1 < len(posiciones) else len(datos)
        categoria = clasificar(nombre_texto)
        resultados.append(
            {
                "orden": len(resultados) + 1,
                "nombre_original": nombre_texto,
                "clase_original": clase_texto,
                "titulo_original": titulo_del_bloque(datos[posicion:siguiente]),
                "categoria": categoria,
                "visible_para_usuario": categoria in {
                    "Captura y proceso", "Consulta y catálogo", "Reporte e impresión"
                },
                "posicion_en_ejecutable": posicion,
            }
        )
    return resultados


def como_markdown(registros: list[dict[str, object]], ruta: Path) -> str:
    visibles = sum(bool(r["visible_para_usuario"]) for r in registros)
    lineas = [
        "# Inventario verificable de ventanas originales",
        "",
        f"Origen analizado: `{ruta.name}`.",
        "",
        f"- Recursos DFM válidos: **{len(registros)}**",
        f"- Ventanas visibles del negocio: **{visibles}**",
        f"- Módulos y diálogos internos: **{len(registros) - visibles}**",
        "",
        "| Núm. | Nombre original | Título original | Tipo | Visible |",
        "|---:|---|---|---|:---:|",
    ]
    for registro in registros:
        titulo = str(registro["titulo_original"]).replace("|", "\\|") or "—"
        lineas.append(
            f"| {registro['orden']} | `{registro['nombre_original']}` | {titulo} | "
            f"{registro['categoria']} | {'Sí' if registro['visible_para_usuario'] else 'No'} |"
        )
    return "\n".join(lineas) + "\n"


def main() -> None:
    predeterminado = Path(__file__).resolve().parents[1] / "legado-local" / "Distribuidora.exe"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ejecutable", nargs="?", type=Path, default=predeterminado)
    parser.add_argument("--formato", choices=("json", "markdown"), default="markdown")
    argumentos = parser.parse_args()

    registros = extraer(argumentos.ejecutable)
    sin_clasificar = [r["nombre_original"] for r in registros if r["categoria"] == "Sin clasificar"]
    if len(registros) != 229 or sin_clasificar:
        raise SystemExit(
            "El inventario no coincide con la versión analizada. "
            f"Recursos={len(registros)}; sin clasificar={sin_clasificar}"
        )

    if argumentos.formato == "json":
        print(json.dumps(registros, ensure_ascii=False, indent=2))
    else:
        print(como_markdown(registros, argumentos.ejecutable), end="")


if __name__ == "__main__":
    main()
