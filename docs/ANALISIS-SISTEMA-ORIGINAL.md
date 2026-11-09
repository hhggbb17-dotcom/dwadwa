# Análisis funcional del sistema SADYV original

Este documento registra la lógica obtenida mediante análisis estático de `Distribuidora.exe` versión 1.5.6.197 y lectura de sólo consulta de la estructura de `CARLOSE.FDB`. El ejecutable antiguo no se utiliza en tiempo de ejecución por la aplicación nueva.

## Arquitectura encontrada

- Aplicación Win32 creada con Delphi.
- Base Firebird con 39 tablas de negocio, 7 procedimientos almacenados y 11 disparadores propios.
- 229 recursos DFM válidos: 188 ventanas visibles del negocio, 24 módulos de datos y 17 diálogos internos o de terceros. El inventario se puede volver a obtener con `tools/inventariar_ventanas_originales.py`.
- Dos almacenes independientes: **Bodega** y **Devoluciones**.
- Los registros no se borran físicamente: usan estados para activos, cancelados, pagados y etapas del reparto.

## Flujo principal

1. Una compra registra encabezado y partidas de revistas/ediciones.
2. Las partidas compradas incrementan la existencia de Bodega.
3. Los paquetes definen cuántos ejemplares de cada revista recibe cada cliente.
4. A partir de la compra y los paquetes se generan pedidos de reparto.
5. Los pedidos se convierten en ventas; las existencias de Bodega disminuyen.
6. Una venta de contado afecta caja. Una venta a crédito genera un cargo en cuentas por cobrar.
7. Las devoluciones normales o extemporáneas del cliente ingresan al almacén de Devoluciones.
8. La cancelación de una venta restituye los ejemplares a Bodega.
9. Las devoluciones al proveedor salen de Bodega o de Devoluciones según su origen.
10. Los traspasos mueven revistas entre Bodega, Devoluciones y Ajustes sin crear o destruir existencia.

## Entidades originales

- `CLIENTES`: prioridad, grupo, ruta, supervisor, condición contado/crédito, plazo, días de pago, límite, saldo, porcentaje de devolución y control de liquidaciones.
- `PROVEEDORES`: contactos, condiciones, saldo y días límite de devolución.
- `REVISTAS` y `EDICIONES`: proveedor, códigos de barras, IVA, precio, descuentos y vencimientos para proveedor y cliente.
- `EXISTENCIAS`: acumuladores separados de compras, ventas, devoluciones y traspasos para ambos almacenes.
- `PAQUETES`: cantidad de una revista asignada a un cliente.
- `PEDIDOS` y `DETAPEDI`: reparto generado para el cliente.
- `FACTCOMP` / `DETAFACTCOMP`: compras.
- `FACTVENT` / `DETAFACTVENT`: ventas de contado o crédito.
- `DEVOCLIE` / `DETADEVOCLIE`: devoluciones normales, cancelaciones y extemporáneas.
- `DEVOPROV` / `DETADEVOPROV`: devolución al proveedor desde Bodega o Devoluciones.
- `CUENXCOBR`, `CUENPORPAGA`, `CAJAREGI` y `DETACAJAREGI`: cartera, proveedores y caja.
- `AJUSTES` / `DETAAJUS`: traspasos y movimientos extraordinarios.

## Reglas verificadas

- Los folios se administran por tipo de documento.
- Una factura de compra no puede cancelarse si sus revistas ya tienen ventas o pedidos.
- Los documentos cancelados permanecen en la base con estado `2`.
- Las ventas manejan `CONTADO` y `CREDITO`.
- Los pedidos encontrados usan estados `2`, `4` y `6`, que representan etapas diferentes del reparto/facturación.
- La devolución de cliente maneja `NORMAL`, `CANCELACION` y `EXTEMPORANEA`.
- Los movimientos de inventario incluyen entrada/salida, faltante de remesa, sobrante de despacho, cambio de edición y devolución errónea.
- La cartera distingue cargos y abonos; incluye pagos en efectivo, transferencia, devolución, saldo inicial y traspaso de saldo.

## Estrategia de reconstrucción

La interfaz se reproduce con las capturas y los recursos DFM. El comportamiento se reconstruye desde las tablas, relaciones, procedimientos y consultas SQL compiladas. Cada operación nueva se guarda en una transacción SQLite y genera su movimiento de inventario y, cuando corresponde, su movimiento de cartera.

Las funciones se implementarán en este orden para conservar las dependencias reales:

1. catálogos completos;
2. existencia por almacén;
3. compras y cuentas por pagar;
4. paquetes y pedidos;
5. ventas, caja y cuentas por cobrar;
6. devoluciones de cliente y proveedor;
7. traspasos, cancelaciones y conciliación;
8. reportes y formatos de impresión.
