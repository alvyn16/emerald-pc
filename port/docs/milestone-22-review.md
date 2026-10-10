# Revisión del hito 22

Base: main `8ee4a7f`; cambios revisados hasta `9374f5a`.

- Corrección: 0017 copia el recurso sin comprimir con la ruta existente;
  0018 retira VBlank antes de liberar; 0019/0020 sirven DMA mediante el
  servicio cooperativo dentro de cargas síncronas. Ningún parche cambia GBA.
- Legibilidad/arquitectura: cambios pequeños por consumidor; no se silencian
  errores en BIOS ni se añaden retornos que omitan operaciones del juego.
  El inventario léxico se declara una lista de candidatos, no una prueba.
- Seguridad/datos: pruebas y capturas en build/, saves aislados; no se
  incorporan recursos ni fuentes upstream. Watchdog termina solo el árbol
  del proceso de prueba que creó. Save original con SHA-256 intacto:
  `B5A41C3758763BBEC72769FAB4A2533BF2DB0B6312D93D25A695F9E4B9E02260`.
- Rendimiento: metadata cada 600 frames solo en diagnóstico; los frames
  adicionales se limitan a las dos cargas afectadas. Sin nueva dependencia.

Verificación: 13 suites host PASS; combate posterior a 0020 gana en 33.365,
regresa al mapa y sale en 37.000; equipo/resumen abren y cierran con B.
Almacenamiento sirve VBlank tras liberar sin SIGSEGV. Binario normal sin
símbolos de script/frame de diagnóstico. GBA `make compare` OK.
Checkout aislado con los 20 parches recompilado y enlazado; árbol idéntico:
`0bb32861903f5d16ce9aa3eff53a8f2cb52ca92c`.

Resultado: apto para integrar localmente. Persisten límites explícitos:
pruebas con fixtures GDB, no una validación completa de todas las pantallas;
watchdog identifica el último progreso pero no obtiene automáticamente
backtrace de un bloqueo. Guardado semántico y reset real son T06/T07.
No se autoriza ni realiza publicación en esta revisión.
