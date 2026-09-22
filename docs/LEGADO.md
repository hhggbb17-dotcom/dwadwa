# Ejecución del sistema original en Windows 11

El ejecutable original es una aplicación Delphi de 32 bits que usa Firebird ODS 10.1. En Windows 11 logra iniciar con Firebird 2.5 x86 ejecutado como aplicación local.

La preparación local se encuentra en `Proyecto\legado-local` y no se versiona en Git porque contiene binarios de terceros, la licencia comercial y configuración específica del equipo.

Para ejecutarlo en este equipo, abre `Iniciar sistema original.cmd`. El lanzador:

1. coloca el INI en el VirtualStore del usuario, porque el programa busca `C:\Windows\newruta.ini`;
2. inicia Firebird 2.5 de forma oculta, sin instalar un servicio;
3. abre `Distribuidora.exe` y detiene Firebird al cerrar.

El aviso “Error de cambio de fecha-hora” se debe a que el programa intenta modificar el reloj de Windows. Se puede cerrar con **OK** y continuar. No se recomienda ejecutar el programa como administrador solamente para evitar ese aviso.

La base `CARLOSE.FDB` permanece en su ubicación original. Antes de operaciones reales conviene trabajar con un respaldo verificado.
