# Revisión y correcciones T19–T22

Fecha: 2026-10-11. Rama: `codex/review-t19-t22`.
Revisión de reset BIOS, RTC, PCM/PSG, contratos de MMIO y su integración
con build, pruebas y juego. No constituye una certificación de toda la campaña.

## Hallazgos corregidos

| Prioridad | Hallazgo | Corrección y evidencia |
| --- | --- | --- |
| P1 | RTC sumaba offsets sin comprobar overflow; ante fechas posteriores a 2099 dejaba la salida sin inicializar, aunque rtc.c ignora algunos errores de transporte. | Operaciones acotadas, última fecha válida y flag de fallo; INT64_MIN/MAX, año 2100 y recuperación en unidad. Fixture real sin días/bayas falsos. Commit 8ab0dfe. |
| P2 | Un hook PSG copiaba la sombra de todos los registros y podía consumir un trigger escrito directamente, sin ejecutarlo. | Reconocer solo escritura/efectos; preservar wave RAM antes de cambiar banco. Trigger directo + hook no relacionado ahora produce sonido. Commit 554d06c. |
| P2 | Cambiar un header propio no recompilaba las suites host. | Dependencias de headers para los ejecutables de pruebas. Dry-run con `-W port_rtc.h` antes/después demuestra la recompilación. Commit 9aa3404. |
| P2 | La referencia ARM no distinguía retorno real de agotamiento del presupuesto de instrucciones. | Exigir PC de retorno y mixer desbloqueado antes de comparar. 1.134 muestras coinciden de nuevo. Commit d936439. |

Los fallos RTC y PSG se reprodujeron antes de corregirlos:
`build/review-rtc-before.log`, `build/review-psg-before.log`.
Dependencias: `build/review-headers-before.log`, `build/review-headers-after.log`.
Todas las modificaciones de implementación viven en port/; no hay nuevo parche
ni cambio a src/include/data upstream en esta revisión.

## Verificación después de corregir

| Comprobación | Resultado / evidencia privada |
| --- | --- |
| Exe normal y diagnóstico, 19 suites y guard del exe normal | PASS, build/review-final-build.log |
| Checkout base + 31 parches existente, actualizado con estas fuentes propias; ambos exe y 19 suites | PASS, build/review-clean-build.log |
| RTC dentro del juego: dormitorio, bayas, día, rollback y reloj 2100 | PASS, build/review-rtc-game.log; build/rtc-game-regression/gdb.log |
| SoundMain original ARM: referencia termina y muestras coinciden | PASS, build/review-arm.log |
| Música título, efecto selección y grito Torchic | PASS, build/review-audio-scenes.log |
| Combate salvaje 4×, victoria frame 33.365, vuelta al mapa y salida limpia | PASS, build/review-battle.log |
| Build GBA make compare | pokeemerald.gba: OK, build/review-gba.log |
| Archivos públicos seguidos por Git | Solo port/, patches/, scripts/ y archivos raíz permitidos; sin binarios/ROM/saves/assets |

Árbol upstream y checkout limpio:
`299f542a9c0d1a6d82ebd7645556e49bdc409692` (idéntico; cambios tracked upstream: cero).
El save normal conserva SHA256
`B5A41C3758763BBEC72769FAB4A2533BF2DB0B6312D93D25A695F9E4B9E02260`.
Los fixtures usan ROM/save aislados bajo build/, ignorado por Git.

## Límites y pendientes

No se repitió toda la campaña ni se afirma fidelidad de audio de hardware.
Sigue el límite del fallback PSG: stores repetidos del mismo valor necesitan
hook para observar eventos. RTC no implementa alarmas IRQ y las rutas Win32
siguen limitadas a ANSI/MAX_PATH. T23 (salida SDL, pausa y velocidad) y las
pruebas amplias de juego continúan pendientes; no se marcan completadas aquí.
Los archivos preexistentes no seguidos en port/docs/plans/ se conservan.
Commits locales pequeños; sin merge ni push.
