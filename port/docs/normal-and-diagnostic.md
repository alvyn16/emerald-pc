# Juego normal y pruebas

El ejecutable para jugar es `build/emerald-pc.exe`. Su ventana se llama
`emerald-pc`, usa teclado y `saves/emerald-pc.sav`. `make -C port exe`
comprueba mediante `nm` que no contiene `PortInputScript_*`,
`sDiagnosticFrame` ni `sStopFrame`.

El ejecutable `build/emerald-pc-diagnostic.exe` incluye entrada por guion y
controles de frames. Su ventana muestra `DIAGNOSTIC - TEST ONLY` y usa
`saves/emerald-pc-diagnostic.sav`, incluso al abrirlo directamente.

Las pruebas GDB usan ejecutables, ROM local y saves dentro de su propia
subcarpeta ignorada de `build/`. Los drivers SDL dummy impiden que abran
ventanas visibles o reproduzcan sonido. No se comparte el save del jugador.

## Regresiones

Desde MINGW32, con GDB y Python disponibles:

```sh
make -C port exe diagnostic-exe test
python port/tests/normal_game_smoke.py
python port/tests/wild_battle_smoke.py
```

`normal_game_smoke.py` ejecuta el binario normal. Solo en el proceso de GDB,
inyecta teclas en KEYINPUT y sustituye la espera del temporizador por un
retorno para acelerar la prueba; no modifica el archivo ejecutable. Las
variables EMERALD_PC de diagnóstico apuntan deliberadamente a valores
inútiles: el juego normal debe ignorarlas. Vigila cualquier llamada a
`BattleSetup_StartWildBattle` y falla si se produce. Comprueba al final
Villa Raíz (mapa 0.9) después de salir de casa, tras 30.500 iteraciones de
ReadKeys, y termina usando el cierre normal.

`wild_battle_smoke.py` prepara una partida aislada mediante funciones del
juego en GDB. Comprueba Villa Raíz, carga Ruta 101 (mapa 0.16), espera hasta
el frame 31.000 y entonces prepara un combate. Exige victoria, regreso al
mapa, frame 37.000 y salida limpia. Un save normal con bytes centinela debe
permanecer intacto durante la ejecución del diagnóstico.

La segunda prueba sigue siendo un fixture controlado: no reproduce todo
el prólogo ni demuestra que se haya encontrado un Pokémon caminando por
la hierba. No se utiliza para justificar combates en Villa Raíz.
