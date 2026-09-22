# Publicaciones Espindola

Renovación del sistema de administración, distribución y venta de revistas para Windows 11.

## Estado actual

La primera versión funcional incluye:

- inicio de sesión con perfiles Administrador y Operador;
- panel de ventas, cartera e inventario;
- clientes, proveedores, publicaciones, ediciones y rutas;
- ventas, compras y devoluciones con actualización automática de existencias;
- ventas a crédito y abonos con actualización del saldo del cliente;
- historial de movimientos y alertas de inventario;
- almacenamiento local sin dependencia de BDE o Firebird;
- importador de catálogos y existencias desde `CARLOSE.FDB`.

Los datos reales no se guardan en Git. La instalación local contiene 445 clientes, 42 proveedores, 3,729 publicaciones y 12,102 ediciones con existencia migradas desde Firebird.

## Ejecutar en Windows 11

Requisito: [.NET 10 SDK](https://dotnet.microsoft.com/download).

Haz doble clic en `Iniciar Publicaciones Espindola.cmd`. El sistema abre `http://127.0.0.1:5188` en el navegador. La consola debe permanecer abierta durante el uso; al cerrarla se detiene el servidor local.

Las cuentas iniciales corresponden a los usuarios del sistema anterior. Sus contraseñas se almacenan como hashes PBKDF2, nunca en texto plano.

## Desarrollo

```powershell
cd PublicacionesEspindola
dotnet run
```

Para verificar la compilación:

```powershell
dotnet build --configuration Release
```

## Migrar nuevamente desde Firebird

Cierra la aplicación nueva y ejecuta:

```powershell
.\scripts\Importar-Datos.ps1
```

El importador crea `store.pre-import.json` antes de reemplazar el archivo de datos. En esta etapa se migran clientes, proveedores, publicaciones y ediciones con existencia. El historial contable permanece intacto en Firebird hasta validar folios, cancelaciones y saldos de apertura.

## Sistema original

En esta computadora también puede iniciarse con `Iniciar sistema original.cmd`. Acepta el aviso UAC de Windows y no abras directamente el EXE heredado. Consulta [docs/LEGADO.md](docs/LEGADO.md) para conocer sus limitaciones.

## Seguridad

- El servidor escucha únicamente en `127.0.0.1`.
- Los archivos de datos, respaldos y binarios heredados están excluidos mediante `.gitignore`.
- No se deben subir `CARLOSE.FDB`, respaldos `.fbk`, licencias ni credenciales a un repositorio público.
