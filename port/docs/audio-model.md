# Audio — T21/T22 (2026-10-11)

## PCM / secuenciador

Implementación propia en m4a_engine.c, datos y rutinas C del secuenciador
compilados desde el checkout ignorado. Se mantienen los frames m4a y su
MIDI pitch upstream. Las pruebas cubren tempo 150/120, gate/wait/FINE,
PATT/PEND/REPT y overflow de la pila de tres patrones, límite de comandos,
ADSR 64/128/192/255/127/63/32, release, sustain cero, pan, loop/fin,
interpolación a media frecuencia, reverse y DPCM con deltas no constantes
incluido wrap firmado. Se corrigen: sustain cero no finalizaba la voz,
contador DMA cero seleccionaba el bloque equivocado, reverb negativo no
reproducía el ajuste original y clipping saturado sustituía la suma de
bytes con wrap. Se limita un período PCM malformado a la capacidad del
buffer y se corta una voz cuyo índice ya no está dentro de su muestra.
SOUNDCNT_X apagado entrega silencio al dispositivo, aunque el secuenciador
C continúe avanzando igual que el código original.

### Referencia medida

m4a_arm_reference.py ejecuta SoundMain ARM original del .gba verificado en
Unicorn, con ondas sintéticas propias y callbacks sin efecto. No distribuye
su código, ROM, BIOS ni assets. Se comparan 224 muestras por vector para
PCM constante, DPCM, suma de tres voces, reverb positivo y negativo, más
14 muestras de interpolación a media frecuencia: **1.134 muestras iguales**
a la implementación host. El final de la onda interpolada usa clipping
host seguro en vez de leer un byte después de ella; no se declara igualdad
para ese extremo. Se instalaron Unicorn 2.1.4 para Python 3.14, solo para
esta referencia opcional. Ejecutar desde MINGW64 para las DLL de nm ARM:

```sh
make -C port test # MINGW32; genera vectores host bajo build/
# En MINGW64, desde la raíz:
PATH="$PWD/pokeemerald/.toolchains/arm-binutils-2.43.1/mingw64/bin:$PATH" python port/tests/m4a_arm_reference.py
```

Logs: build/t21-vectors.log, t21-arm-reference.log; resultados privados
m4a-host-vectors.csv y m4a-arm-vectors.json. Esto mide la aritmética de esos
vectores, no fidelidad completa de todas las canciones ni temporización ARM.

### Escenas reales / escucha

Audio_scene_smoke.py utiliza el ejecutable diagnóstico y funciones reales
m4a para MUS_TITLE=413, SE_SELECT=5 y PlayCry_Normal(Torchic=280). Sustituye
callbacks visuales con DummyFunc en GDB para aislar la secuencia; no cambia
el ejecutable normal ni el save del usuario. WAV stereo PCM16 48 kHz,
10,062354 s por escena, en build/audio-scene-regression/ (ignorado).

| Escena | Pico absoluto | RMS | Muestras saturadas |
| --- | ---: | ---: | ---: |
| Título | 18.942 | 2.812,421 | 0 |
| Selección | 2.304 | 169,575 | 0 |
| Grito Torchic | 9.978 | 538,878 | 0 |

El usuario escuchó las tres muestras y confirmó **«Se oyen reconocibles»**.
No se infiere equivalencia GBA del RMS, de que no haya clipping, ni de esta
escucha. No se dispone de una captura de audio de hardware para esas tres
escenas. WAV/mediciones quedan locales; nunca son parte del repo público.

## PSG / bancos y writes

0031 sustituye 42 stores directos/indirectos de m4a.c por wrappers; GBA
expande la misma asignación y conserva su ROM exacta. ply_port también
utiliza el hook host. Write8/16/32 procesa registros en orden little endian
sin esperar al siguiente frame. Triggers de igual valor reinician fase;
NR52 devuelve estado generado, DAC apagado desactiva el canal.
NR30 selecciona playback y el CPU escribe el banco opuesto. Ambos bancos
se conservan aunque haya varios cambios antes de renderizar. En modo 64
nibbles, el banco activo y la ventana CPU cambian al cruzar 32 muestras.
NR34 recarga reproducción; volumen, longitud y frecuencias corresponden
a los registros. El reloj de envolvente/longitud/sweep es 512 Hz, no FPS.
Se corrigió el reloj LFSR del ruido, anteriormente ocho veces lento.

Suite PSG: square ~1000 Hz/duty 50%, envolvente a cero, longitud un tick,
sweep negativo 1000→500 y overflow positivo, ruido 7-bit período 127 con
un shift/muestra a 524.288 Hz, routing izquierda, dos bancos con writes de
8/16/32 bits, cambio automático y edición del banco opuesto mientras
reproduce, trigger repetido y off/on/reset. La suite m4a ejecuta CgbSound
original con una onda propia (40→upload→00→80→trigger) y compara 32 muestras
exactas. CgbOscOff desactiva el canal inmediatamente. Power-off borra
osciladores/registros, conserva wave RAM como hardware; RegisterRamReset
sí limpia ambos bancos.

Fuentes: [GBATEK, canales GBA](https://rust-console.github.io/gbatek-gbaonly/#gba-sound-channel-3---wave-output)
y el m4a original local en src/m4a.c, src/m4a_1.s y constants/m4a_constants.inc.

## Límites

El fallback de sondeo solo ve valores distintos: los consumidores m4a
inventariados usan hooks para escrituras con efectos. No se modelan ciclos
de CPU, reproducción/lectura del shift-register wave RAM a nivel de bus,
filtro analógico/HP, todos los quirks de DAC/envelope ni latencia de writes
dentro de un buffer ya generado. Los tests documentan el contrato nativo
actual, no equivalencia universal de hardware. T23 (pausa, velocidad,
colas/dispositivo y discontinuidades) sigue como tarea separada.
