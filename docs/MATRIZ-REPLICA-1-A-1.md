# Matriz de réplica 1 a 1

## Alcance comprobado

El número de ventanas no se toma de una estimación ni de las capturas. Se obtiene directamente de los recursos DFM de `Distribuidora.exe`:

| Tipo de recurso | Cantidad | Se replica como ventana |
|---|---:|:---:|
| Captura y proceso | 50 | Sí |
| Consulta y catálogo | 56 | Sí |
| Reporte e impresión | 82 | Sí |
| Módulo de datos no visible | 24 | No |
| Diálogo interno o de terceros | 17 | No |
| **Total de ventanas del negocio** | **188** | **Sí** |
| **Total de recursos DFM válidos** | **229** | — |

Por lo tanto, el objetivo verificable no son 150 nombres de menú: son **188 ventanas del negocio distintas**. El listado completo, con nombre interno, título original, tipo y orden dentro del ejecutable, está en [INVENTARIO-VENTANAS-ORIGINALES.md](INVENTARIO-VENTANAS-ORIGINALES.md).

## Cuándo una ventana cuenta como terminada

Una ventana sólo podrá marcarse como **Completa 1 a 1** cuando cumpla todos estos puntos:

1. Existe una entrada de navegación propia; no es un alias silencioso hacia otro panel.
2. Conserva el objetivo, campos, botones, tablas, filtros y pasos del formulario original.
3. Sus altas, consultas, modificaciones, cancelaciones y desactivaciones afectan los datos correctos.
4. Aplica las validaciones, estados, folios, existencias, cartera o caja que correspondan.
5. Sus botones de consulta e impresión producen el documento correcto, no una captura de pantalla.
6. Se comparó con el DFM, con las capturas disponibles y con la estructura o consultas de la base original.
7. Tiene una prueba repetible del flujo principal y otra de sus validaciones importantes.

Compartir el mismo código interno será válido cuando dos ventanas realicen operaciones comunes, pero cada ventana mantendrá su nombre, configuración, campos, permisos, navegación y resultado propios.

## Estado real al iniciar esta matriz

| Estado | Cantidad | Significado |
|---|---:|---|
| Completa 1 a 1 | 0 | Todavía no se ha validado ninguna contra todos los criterios anteriores. |
| Parcial o equivalente moderno | Varias funciones base | Hay catálogos, compras, ventas, devoluciones, traspasos, rutas, caja, cartera, respaldo y reportes operativos, pero aún no equivalen individualmente a todos los formularios originales. |
| Pendiente de validación 1 a 1 | 188 | Cada formulario debe pasar por extracción, implementación y prueba individual. |

Este estado evita afirmar que el clon está completo únicamente porque un menú abre una pantalla genérica.

## Orden de reconstrucción

La implementación se realizará por dependencias funcionales, sin omitir ventanas:

| Bloque | Familias principales | Resultado esperado |
|---|---|---|
| 1. Catálogos | Clientes, proveedores, revistas, ediciones, empleados, rutas, cuentas y tipos de movimiento | Altas, consultas y modificaciones con todos los campos originales. |
| 2. Compras e inventario | Compras, existencias, códigos de barras, monitoreo, traspasos y ajustes | Movimientos y saldos separados de Bodega y Devoluciones. |
| 3. Distribución | Paquetes, grupos, pedidos, reparto y rutas | Generación, consulta, entrega e impresión del reparto. |
| 4. Ventas y caja | Ventas, facturación, caja, cortes y cancelaciones | Contado, crédito, cobro, impresión y reversión completa. |
| 5. Devoluciones | Cliente, extemporánea y proveedor | Flujo por origen, categoría, inventario, proveedor y notas. |
| 6. Cartera | Cuentas por cobrar y pagar, estados de cuenta y liquidaciones | Cargos, abonos, saldos y conciliación por persona. |
| 7. Reportes | Los 82 formularios de reporte e impresión | Cada formato con filtros, totales y salida imprimible propios. |
| 8. Cierre de paridad | Permisos sin inicio de sesión, respaldo, restauración y utilidades | Validación cruzada de las 188 ventanas y sus recorridos. |

## Evidencia y control

- `tools/inventariar_ventanas_originales.py` vuelve a obtener el inventario desde el ejecutable sin abrirlo ni modificarlo.
- `tools/extraer_estructura_ventanas.py` recupera la jerarquía, dimensiones, controles, textos, botones, enlaces de datos y eventos de cada DFM. En total se identificaron 6,442 componentes y 3,658 enlaces a eventos.
- El script falla si no encuentra exactamente 229 recursos válidos o si aparece un formulario sin clasificar.
- El DOCX aporta 115 capturas y sirve como evidencia visual, pero no sustituye el inventario del ejecutable.
- Los módulos de datos y diálogos de componentes no se presentarán artificialmente como pantallas para inflar el avance.
- La aplicación seguirá funcionando localmente en Flask, sin internet y sin inicio de sesión, como se solicitó.

## Regla de entrega

El proyecto se considerará clon funcional terminado cuando la suma sea:

`188 completas + 0 parciales + 0 pendientes`

Hasta llegar a ese resultado, la documentación y la interfaz deberán mostrar el avance real y no declarar una réplica completa.

## Comandos de verificación

```powershell
python tools\inventariar_ventanas_originales.py --formato markdown
python tools\extraer_estructura_ventanas.py --ventana FActuExis
python -m unittest discover -s tests -v
```
