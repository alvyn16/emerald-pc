# emerald-pc

Port nativo experimental para Windows i686 con SDL2 de Pokémon Emerald,
basado en la decompilación de [pret/pokeemerald](https://github.com/pret/pokeemerald).
El recorrido de prueba llega a una partida nueva y al mundo exterior. Incluye
guardado a disco, audio PCM/PSG, reinicio suave, velocidad ajustable y PPU de
modos 0–5 con fondos, sprites, ventanas, mezcla de color y mosaico. Todavía
pueden aparecer fallos fuera del recorrido probado.

Cada usuario debe aportar su propia ROM legal de Pokémon Emerald en inglés. Este repositorio no distribuye ROMs, saves, assets ni código de pokeemerald. Es un proyecto de fans no afiliado a Nintendo, Game Freak ni The Pokémon Company.

## Preparación en Windows

1. Clona este repositorio y entra en su carpeta.
2. Ejecuta `pwsh -File .\setup.ps1` en PowerShell. El script descarga pret/pokeemerald en `pokeemerald/`, fija el commit usado por este proyecto y aplica los parches de `patches/` en orden.
3. Coloca tu ROM legal original en `roms/` y conserva ese archivo intacto. Ambas carpetas están ignoradas por Git.

El build GBA de referencia requiere las dependencias descritas en `pokeemerald/INSTALL.md`. La preparación de este repositorio se verificó en MSYS2 MINGW64 con `agbcc` y GNU Binutils ARM 2.43.1 mediante `make compare`. El script de preparación no instala la toolchain ni distribuye la ROM.

## Compilar y jugar

Después de compilar el GBA original según `pokeemerald/INSTALL.md` y preparar
MSYS2 MINGW32 como indica `port/docs/toolchain.md`, ejecuta desde la raíz:

```sh
make -C port exe
make -C port test
./build/emerald-pc.exe
```

La compilación copia `SDL2.dll` junto al ejecutable en `build/`. Después
puedes abrir `build/emerald-pc.exe` directamente desde el Explorador de
Windows; conserva ambos archivos en la misma carpeta.

Para jugar usa **`build/emerald-pc.exe`**. El otro ejecutable,
`emerald-pc-diagnostic.exe`, se identifica con **DIAGNOSTIC - TEST ONLY**
y guarda en `saves/emerald-pc-diagnostic.sav`, separado de tu partida.
Las pruebas automatizadas no abren ventanas visibles.

El ejecutable carga solo en memoria el único `.gba` de `roms/`; nunca modifica
el archivo original. El guardado experimental usa `saves/emerald-pc.sav`,
ignorado por Git. El estado del arranque y el siguiente bloqueo medido con
GDB están en `port/docs/first-run-report.md`. Las 13 suites host de `test`
usan datos sintéticos y no necesitan una ROM; la compilación sí requiere
las herramientas y recursos locales generados por el build GBA.

## Controles

| Tecla PC | Botón GBA |
| --- | --- |
| Flechas | Cruceta |
| Z / X | A / B |
| Enter / Retroceso | Start / Select |
| A / S | L / R |

Pulsa **Z + X + Enter + Retroceso** para el reinicio suave. Relanza el
ejecutable y restablece la velocidad a 1×. Cerrar la ventana termina el
proceso y cierra el archivo de guardado.

## Velocidad de juego

Pulsa **P** durante el juego para abrir el menú de velocidad. El juego se
pausa mientras está abierto. Usa **↑/↓** para elegir **1×, 2×, 3× o 4×** y
**Enter** para activar la opción. **Esc** o **P** cierran el menú sin cambiar
la velocidad. La opción queda activa hasta cerrar el programa. A 2×–4×,
el audio también se acelera y sube de tono. Si Windows no puede abrir un
dispositivo de audio, el juego continúa en silencio.

## Limitaciones

Están implementados los modos 0–5, IRQ/timers, calendario de vídeo, DMA,
BIOS por flags y RTC persistente. Los contratos y límites medidos están en
`port/docs/ppu-model.md`, `video-calendar.md`, `bios.md` y `rtc.md`.
Los writes m4a de PSG ya capturan bancos y triggers entre frames; PCM tiene
vectores contrastados con el mezclador ARM original. Consulta
`port/docs/audio-model.md` para pruebas, escucha y límites de audio.

Enlace/RFU/multiboot y campaña completa siguen pendientes. No se garantiza
precisión por ciclo, filtro de sonido analógico ni compatibilidad total con
accesorios. El soporte actual es Windows de 32 bits; x86-64 queda como
trabajo futuro. T24–T26 tienen regresiones de combate y almacenamiento;
T27 tiene segmentos medidos, pero sigue pendiente de campaña continua.
El estado completo está en `port/docs/tasks/todo.md`.

Consulta `port/docs/toolchain.md` para reproducir el entorno. ROMs, saves,
recursos, capturas/WAV y binarios generados permanecen en carpetas ignoradas
por Git. El RTC guarda su configuración separada en saves/; un save antiguo
puede avanzar eventos al activar la fecha real, según `port/docs/rtc.md`.

Teclado y mandos SDL compatibles están disponibles. El remapeo se guarda en
`saves/controls.cfg`; consulta [controles y pruebas](port/docs/controller-input.md).
La tecla P abre el menú de velocidad. La validación física de mandos queda
pendiente; se probaron el backend y un mando virtual SDL real.
