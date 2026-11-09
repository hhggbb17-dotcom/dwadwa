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

Desde el módulo lateral **Configuración**, ubicado antes de Ayuda, se personalizan el nombre de la empresa, el nombre del sistema, la moneda, el color principal y su fotografía o logotipo.

## Productos y códigos de barras

- Registra una publicación y su edición en una sola pantalla.
- Guarda código de barras, precio, impuesto, fechas y existencia inicial.
- Admite lectores USB que funcionan como teclado, sin instalar controladores especiales.
- Permite escanear en compras, ventas, devoluciones y traspasos.
- Si se escanea nuevamente el mismo producto, aumenta su cantidad automáticamente.
- Asigna folios consecutivos separados para cada tipo de operación.

## Catálogos, reparto y devoluciones

- Los catálogos permiten crear, consultar, modificar y desactivar registros sin borrar el historial.
- Las búsquedas consideran claves, nombres, teléfonos, RFC, códigos de barras, categorías, rutas y proveedores.
- Las rutas de reparto incluyen nombre, repartidor, indicaciones y selección de tiendas; pueden imprimirse en una hoja ordenada para entrega y firma.
- Los clientes pueden clasificarse por categorías y consultarse por categoría y ruta.
- Las devoluciones de clientes y las devoluciones a proveedor son operaciones separadas, con categoría, almacén de origen y notas para aclaraciones de inventario.
- Las operaciones nuevas generan un ticket imprimible de 80 mm y los reportes se imprimen en un documento limpio, sin incluir la interfaz de la aplicación.

## Respaldo y migración

El módulo **Respaldo** permite:

- descargar un respaldo completo comprimido, con un archivo de Excel independiente por cada módulo;
- descargar un formato vacío con instrucciones para trasladar información de otra plataforma;
- importar ese formato para agregar o actualizar clientes, proveedores, publicaciones, ediciones, existencias y paquetes.

El respaldo no modifica la información. Debido al volumen del historial, su preparación puede tardar aproximadamente dos o tres minutos.

La instalación local contiene una migración completa de las 41 tablas del sistema anterior. Incluye catálogos, existencias por almacén, compras, paquetes, pedidos, ventas, devoluciones, cartera y caja. La aplicación diaria no ejecuta ni se conecta al programa antiguo o a Firebird.

La reconstrucción funcional se basa en el análisis de la base y de los recursos compilados del programa, no únicamente en las capturas. Consulta [el análisis funcional](docs/ANALISIS-SISTEMA-ORIGINAL.md) para ver los flujos y reglas identificados.

La réplica 1 a 1 se controla contra las **188 ventanas visibles del negocio** encontradas dentro del ejecutable original. El [inventario completo](docs/INVENTARIO-VENTANAS-ORIGINALES.md) y la [matriz de aceptación](docs/MATRIZ-REPLICA-1-A-1.md) impiden contar alias, paneles genéricos o componentes internos como ventanas terminadas.

Para consultar la especificación recuperada de una ventana concreta sin ejecutar el sistema antiguo:

```powershell
python tools\extraer_estructura_ventanas.py --ventana FActuExis
```

## Preparar otra computadora

```powershell
cd PublicacionesEspindola
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Después se puede usar el iniciador de Windows normalmente.

## Pruebas externas por internet

GitHub Pages no ejecuta Flask. Para compartir una versión gratuita con evaluadores se utiliza GitHub como repositorio y PythonAnywhere como servidor con una base SQLite de demostración. Consulta la [guía completa de publicación](docs/PRUEBAS-EXTERNAS-GRATIS.md).

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
"# dwadwa" 
