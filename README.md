# Gestión de Publicaciones

Sistema web local para administrar compras, distribución, inventario, ventas, devoluciones, cartera y caja de una distribuidora de publicaciones. Conserva la lógica recuperada de SADYV, con una interfaz moderna que puede configurarse para cualquier empresa y abre directamente, sin inicio de sesión.

## Uso en Windows 11

Haz doble clic en **`Iniciar Publicaciones Espindola.cmd`**. El servidor sólo escucha en `127.0.0.1` y abre la aplicación en:

`http://127.0.0.1:5000`

No requiere conexión a internet para funcionar una vez instalado. La consola debe permanecer abierta durante el uso; al cerrarla se detiene la aplicación.

## Tecnología

- Python 3
- Flask
- HTML, CSS y JavaScript sin dependencias externas
- SQLite local

Desde el botón **Configuración** se personalizan el nombre de la empresa, el nombre del sistema, la moneda y el color principal.

## Respaldo y migración

El módulo **Respaldo** permite:

- descargar un respaldo completo comprimido, con un archivo de Excel independiente por cada módulo;
- descargar un formato vacío con instrucciones para trasladar información de otra plataforma;
- importar ese formato para agregar o actualizar clientes, proveedores, publicaciones, ediciones, existencias y paquetes.

El respaldo no modifica la información. Debido al volumen del historial, su preparación puede tardar aproximadamente dos o tres minutos.

La instalación local contiene una migración completa de las 41 tablas del sistema anterior. Incluye catálogos, existencias por almacén, compras, paquetes, pedidos, ventas, devoluciones, cartera y caja. La aplicación diaria no ejecuta ni se conecta al programa antiguo o a Firebird.

La reconstrucción funcional se basa en el análisis de la base y de los recursos compilados del programa, no únicamente en las capturas. Consulta [el análisis funcional](docs/ANALISIS-SISTEMA-ORIGINAL.md) para ver los flujos y reglas identificados.

## Preparar otra computadora

```powershell
cd PublicacionesEspindola
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Después se puede usar el iniciador de Windows normalmente.

## Desarrollo

```powershell
cd PublicacionesEspindola
python app.py
```

## Migración verificable

`tools/import_legacy.py` crea `data/legacy.db` desde una copia de Firebird y `tools/sync_catalogs.py` prepara los catálogos operativos. Las dependencias de esa tarea están separadas en `requirements-migration.txt`; no son necesarias para el uso diario.

La migración local validada contiene, entre otros datos, 51,456 ediciones, 60,573 ventas, 18,283 devoluciones de clientes, 5,143 devoluciones a proveedor, 64,067 movimientos de caja y 69,547 movimientos de cartera.

## Datos y seguridad

La base `data/sadyv.db`, el archivo de migración y los respaldos reales se excluyen de Git. Nunca se deben publicar bases de clientes, credenciales, licencias o archivos Firebird en un repositorio público.
