# Revisión T19–T22

Fecha 2026-10-11. Ramas codex/milestone-27-bios → milestone-28-rtc →
milestone-29-audio; commits pequeños por módulo/fixture. No merge/main ni
push en esta sesión. Se mantienen tareas posteriores abiertas.

## Revisión del código

- Reset usa solo memoria GBA mapeada, nunca memset sobre pila/heap/global
  host. Exclusión IWRAM y KEYINPUT se prueban; módulos internos reiniciados.
- RTC valida formato/BCD/calendario, rechaza configuración corrupta sin
  reemplazarla, escribe temporal+flush+reemplazo. Hora de Windows, offset
  persistente y clamp de rollback explícitos. SetDateTime se distingue de
  cambio del OS. Formato .sav intacto; caveat de saves sin RTC documentado.
- MMIO PSG usa store hooks de ancho explícito; la vista CPU de wave RAM
  corresponde al banco opuesto, cambia también durante dual playback.
  Triggers del mismo valor son eventos. Sondas legacy son fallback limitado.
- PCM usa aritmética definida para wrap/ganancias e índices limitados.
  La corrección sustain=0 detiene la voz; reverb tiene referencia ARM
  ejecutada, no solo assertions que reproducen la fórmula host.
- Los parches 0030/31 mantienen caminos GBA y compare OK. setup aplica
  todos en orden sobre el commit fijado; el árbol reproducido coincide.
- Config de tiempo inyectado solo PORT_DIAGNOSTIC, normal auditado; tests
  de juego usan subdirectorios de build con save/ROM aislados. Save usuario
  preservado. Las nuevas dependencias de headers siirtc/m4a se declaran.

## Evidencia y límites

19 suites PASS en raíz y clon con 31 parches. Reset real T19 y RTC con
reloj del dormitorio/eventos PASS. PCM: 1.134 muestras iguales a ARM en
fixtures privados; otras pruebas pan/ADSR/reverse/patrones/fin. PSG: CgbSound
real, dos bancos/triggers/sweep/length/noise/power. WAV de tres escenas,
medidas y escucha confirmada por usuario, sin afirmación de equivalencia
universal de canciones. GBA compare OK. Normal sin batalla al salir;
combate 4× victoria/regreso y recovery de save PASS.

Logs enumerados en first-run-report.md y contratos en bios.md, rtc.md y
audio-model.md. Los mensajes esperados de fallo en suites RTC/audio/reset
son fixtures negativos, no fallos del recorrido normal.

No precisión ARM por ciclo, filtros analógicos ni accesorios RTC con IRQ;
la zona horaria inicial queda fija como desfase y se explican saltos y
saves anteriores. Campaña/enlace y T23 siguen pendientes. No se distribuye
ROM, save, WAV, asset, upstream completo ni ejecutable generado.
