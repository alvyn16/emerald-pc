# RTC host — T20

La capa propia port_rtc usa segundos UTC de Windows (FILETIME), aplica un
desfase persistente y entrega fechas BCD 2000–2099 mediante siirtc (0030).
Probe indica presencia solo si hay una configuración válida. Protect y
Unprotect conservan su bloqueo; no se escribe GPIO ni la ROM. El formato
siirtc de estado conserva IRQ flags y fuerza 24 horas. Los flags de alarma
se almacenan, pero no se generan IRQ de alarma/frecuencia: Emerald usa
fecha/hora/estado, no esas interrupciones. Reset restablece el estado, no
borra la fecha. Entradas BCD y fechas imposibles se rechazan.

## Persistencia y reloj

`saves/emerald-pc.rtc` junto al proyecto resuelto desde el exe; diagnóstico
usa emerald-pc-diagnostic.rtc. Texto versionado: offset UTC en segundos,
último instante entregado y estado. Flush, _commit y reemplazo con
MoveFileEx; configuración inválida preservada y RTC ausente con aviso.
No cambia el formato del .sav ni se escribe el save del usuario en tests.
Rutas Win32 ANSI/MAX_PATH son el límite actual.

La primera creación toma la zona horaria/DST actual como desfase fijo.
Después el contador avanza en segundos reales: ni cambiar zona/DST ni
acelerar frames a 2×–4× cambia su ritmo. El reloj del dormitorio ajusta el
offset local guardado por el juego, tal como en GBA. Un retroceso del reloj
del sistema congela el RTC hasta alcanzar el último instante observado;
no repite días. Un ajuste explícito SetDateTime sí permite moverlo atrás.
Close persiste el último instante; matar el proceso puede perder el último
avance. Un salto adelante se acepta y produce eventos offline normales.
Si el reloj supera 2099, retorna error y marca el flag de fallo de energía,
pero entrega la última fecha válida: rtc.c ignora algunos errores de transporte.
Así no quedan campos sin inicializar ni se inventan eventos diarios. Las sumas
y restas del desfase se validan antes de operar; SetDateTime rechaza offsets
fuera del rango persistible. No simula una batería física ni alarmas.

## Saves anteriores

Se cargan sin conversión. Se conservan localTimeOffset y lastBerryTreeUpdate
del .sav. Los saves creados cuando RTC estaba ausente partían de la fecha
ficticia 2000: al activar fecha real, el juego puede consumir un intervalo
largo y actualizar bayas/eventos diarios. Es comportamiento upstream, no
una reescritura host del save. Conservar backup y ajustar el reloj en el
juego si procede; no borramos ni corregimos silenciosamente ese progreso.

## Verificación

Suite rtc: 29 febrero→1 marzo, +61 segundos, reapertura, set de hora,
retroceso del sistema, fechas/BCD inválidos, configuración corrupta y
40.000 lecturas agrupadas por 1×–4× sin avance artificial. La hora inyectada
PortRtc_DiagnosticSetTime solo existe en el ejecutable diagnóstico.
`build/t20-integration.log`: 19 suites PASS; build normal/diagnóstico.
`build/t20-gba-compare.log`: pokeemerald.gba: OK.
La prueba de juego aislada rtc_game_smoke verifica la ruta real del reloj
del dormitorio, PlantBerryTree/DoTimeBasedEvents y VAR_DAYS con tiempo
inyectado. PASS: reloj confirmado en frame 19.531, baya Cheri plantada→brote a +3h,
VAR_DAYS=1 a +24h, retroceso de 48h sin repetir eventos ni alterar la fecha
de actualización de bayas; salida limpia en 30.500. Evidencia:
`build/t20-game.log`, `build/rtc-game-regression/gdb.log`.

Revisión posterior: INT64_MIN/MAX, salto a 2100 y recuperación PASS en
rtc_test; el fixture de juego confirma fecha segura y ningún evento diario
falso a 2100 (`build/review-rtc-game.log`, marker INVALID CLOCK en gdb.log).
