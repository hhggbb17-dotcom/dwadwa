# Publicaciones Espindola — SADYV

Clon web local del **Sistema de Administración, Distribución y Venta de Revistas**. La interfaz conserva el aspecto y la estructura del sistema SADYV original y abre directamente, sin inicio de sesión.

## Uso en Windows 11

Haz doble clic en **`Iniciar Publicaciones Espindola.cmd`**. El servidor sólo escucha en `127.0.0.1` y abre la aplicación en:

`http://127.0.0.1:5000`

No requiere conexión a internet para funcionar una vez instalado. La consola debe permanecer abierta durante el uso; al cerrarla se detiene la aplicación.

## Tecnología

- Python 3
- Flask
- HTML, CSS y JavaScript sin dependencias externas
- SQLite local

Los catálogos recuperados del sistema anterior se importan automáticamente a SQLite la primera vez. La aplicación no ejecuta ni se conecta al programa antiguo o a Firebird.

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

## Datos y seguridad

La base `data/sadyv.db`, el archivo de migración y los respaldos reales se excluyen de Git. Nunca se deben publicar bases de clientes, credenciales, licencias o archivos Firebird en un repositorio público.
