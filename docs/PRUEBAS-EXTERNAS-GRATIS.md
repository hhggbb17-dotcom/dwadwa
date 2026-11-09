# Publicar una versión gratuita para pruebas externas

## Plataforma recomendada

La combinación recomendada es:

- **GitHub:** conserva el código y permite actualizarlo.
- **PythonAnywhere:** ejecuta Flask y conserva la base SQLite de demostración.
- **Dirección para compartir:** `https://TU_USUARIO.pythonanywhere.com`

GitHub Pages no puede ejecutar esta aplicación porque sólo publica archivos estáticos y no admite Python en el servidor. PythonAnywhere ofrece una aplicación web gratuita, un trabajador y 512 MB de almacenamiento persistente. Las cuentas gratuitas nuevas deben renovar la aplicación cada mes desde su panel.

Documentación oficial:

- [GitHub Pages no admite Python de servidor](https://docs.github.com/en/pages/getting-started-with-github-pages/creating-a-github-pages-site)
- [Publicar Flask en PythonAnywhere](https://help.pythonanywhere.com/pages/Flask/)
- [Características de la cuenta gratuita](https://help.pythonanywhere.com/pages/FreeAccountsFeatures/)

## Seguridad de la demostración

La aplicación abre sin inicio de sesión, por solicitud del proyecto. En consecuencia, cualquier persona que reciba el enlace podrá crear, modificar o desactivar registros.

La publicación debe comenzar con una base vacía de demostración. No se deben subir a GitHub ni a PythonAnywhere:

- `CARLOSE.FDB`, archivos FBK o bases Firebird;
- `sadyv.db` o `legacy.db` con información real;
- respaldos de clientes;
- licencias, contraseñas o datos fiscales reales.

El archivo `.gitignore` ya excluye esos archivos.

## 1. Subir el proyecto a GitHub

Crear un repositorio llamado `Publicaciones-Espindola`. Desde la carpeta `Proyecto`:

```powershell
git remote add origin https://github.com/TU_USUARIO/Publicaciones-Espindola.git
git push -u origin main
```

Antes de publicar, comprobar que GitHub no muestre archivos `.db`, `.fdb`, `.fbk`, imágenes reales de la empresa o respaldos.

## 2. Crear la cuenta gratuita

1. Crear una cuenta en [PythonAnywhere](https://www.pythonanywhere.com/).
2. Abrir **Consoles** y crear una consola **Bash**.
3. Ejecutar:

```bash
git clone https://github.com/TU_USUARIO/Publicaciones-Espindola.git
mkvirtualenv --python=/usr/bin/python3.13 publicaciones-espindola
cd ~/Publicaciones-Espindola/PublicacionesEspindola
pip install -r requirements.txt
```

## 3. Crear la aplicación web

1. Abrir la sección **Web**.
2. Elegir **Add a new web app**.
3. Elegir **Manual configuration** y la misma versión de Python usada en el entorno virtual.
4. En **Virtualenv**, escribir:

```text
/home/TU_USUARIO/.virtualenvs/publicaciones-espindola
```

5. Abrir el archivo WSGI mostrado por PythonAnywhere y sustituir su contenido por:

```python
import sys

ruta = "/home/TU_USUARIO/Publicaciones-Espindola/PublicacionesEspindola"
if ruta not in sys.path:
    sys.path.insert(0, ruta)

from wsgi import application
```

6. Pulsar **Reload**.
7. Abrir `https://TU_USUARIO.pythonanywhere.com/api/estado`.

La respuesta correcta contiene:

```json
{
  "base_de_datos": "lista",
  "estado": "disponible",
  "historial_original": false
}
```

Después se puede compartir `https://TU_USUARIO.pythonanywhere.com` con los evaluadores.

## 4. Actualizar una versión publicada

En la consola Bash de PythonAnywhere:

```bash
cd ~/Publicaciones-Espindola
git pull
workon publicaciones-espindola
pip install -r PublicacionesEspindola/requirements.txt
```

Después, pulsar **Reload** en la sección **Web**. La base de demostración permanece en `PublicacionesEspindola/data/sadyv.db` y no se reemplaza con `git pull`.

## Lista mínima para los evaluadores

Cada evaluador debe registrar los siguientes resultados:

1. navegador y dispositivo utilizados;
2. ventana o módulo probado;
3. pasos realizados;
4. resultado esperado y resultado obtenido;
5. captura del error, si existe;
6. folio, cliente, producto o registro de prueba relacionado.

La versión pública sirve para pruebas funcionales con datos desechables. No debe utilizarse como sistema productivo mientras siga sin inicio de sesión, aislamiento por empresa, copias automáticas y las 188 ventanas terminadas.
