# Ejecución del sistema original en Windows 11

El ejecutable original es una aplicación Delphi de 32 bits que usa Firebird ODS 10.1. En Windows 11 logra iniciar con Firebird 2.5 x86 ejecutado como aplicación local.

La preparación local se encuentra en `Proyecto\legado-local` y no se versiona en Git porque contiene binarios de terceros, la licencia comercial y configuración específica del equipo.

Para ejecutarlo en este equipo, abre `Iniciar sistema original.cmd`. El lanzador:

1. solicita autorización de administrador mediante el aviso UAC de Windows;
2. coloca temporalmente el INI en `C:\Windows\newruta.ini`, que es la ruta fija buscada por el programa;
3. permite que la aplicación sincronice fecha/hora, operación que el programa exige al iniciar;
4. inicia Firebird 2.5 de forma oculta, sin instalar un servicio;
5. abre `Distribuidora.exe`, detiene el Firebird iniciado por el lanzador y retira el INI al cerrar.

El bloqueo después de iniciar sesión aparece cuando la aplicación no puede completar su sincronización de fecha/hora y se combina con la redirección VirtualStore. El lanzador evita esa configuración inconsistente. No abras directamente `Distribuidora.exe`; usa siempre el archivo CMD.

La base `CARLOSE.FDB` permanece en su ubicación original. Antes de operaciones reales conviene trabajar con un respaldo verificado.
