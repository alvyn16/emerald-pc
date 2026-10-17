# Toolchain del port PC (Windows)

El objetivo PC se compila con **MSYS2 MINGW32 / i686**. `HOST_ARCH=i686` es el valor por defecto de `port/Makefile`. El checkout de `pokeemerald` queda fijado por `setup.ps1` al commit `731ad5bfd6e6f265508d0efcca0ba42f9dcf5881` y permanece ignorado por Git.

## Versiones medidas en esta máquina

Salida de `pacman -Q` en esta instalación de MSYS2:

| Entorno | Paquete | Versión |
| --- | --- | --- |
| MINGW32 | `mingw-w64-i686-gcc` | `16.2.0-4` |
| MINGW32 | `mingw-w64-i686-binutils` | `2.47-3` |
| MINGW32 | `mingw-w64-i686-SDL2` | `2.32.10-1` |
| MINGW32 | `mingw-w64-i686-pkgconf` | `1~3.0.7-1` |
| MINGW32 | `mingw-w64-i686-gdb` | `18.1-3` |
| MINGW32 | `mingw-w64-i686-crt` | `14.0.0.r426.g4564ee4b5-1` |
| MINGW64 | `mingw-w64-x86_64-gcc` | `16.2.0-4` |
| MINGW64 | `mingw-w64-x86_64-binutils` | `2.47-3` |
| MINGW64 | `mingw-w64-x86_64-SDL2` | `2.32.10-1` |
| MINGW64 | `mingw-w64-x86_64-pkgconf` | `1~3.0.7-1` |
| MINGW64 | `mingw-w64-x86_64-crt` | `14.0.0.r426.g4564ee4b5-1` |
| MINGW64 | `mingw-w64-x86_64-libpng` | `1.6.59-1` |
| MINGW64 | `mingw-w64-x86_64-zlib` | `1.3.2-2` |
| MSYS | `make` | `4.4.1-3` |
| MSYS | `git` | `2.56.0-1` |

El build GBA usa `agbcc` de `pokeemerald/tools/agbcc` y un **Binutils ARM 2.43.1-1 aislado** en `pokeemerald/.toolchains/arm-binutils-2.43.1/mingw64/bin`; `arm-none-eabi-ld --version` indica `2.43.1`. El paquete original es `mingw-w64-x86_64-arm-none-eabi-binutils 2.43.1-1` (SHA-256 del archivo `.pkg.tar.zst` local: `557a00cbc60740a185e6c7d847cf06e4e5d06401fb179d699fd4fbc898ec5a18`). No usar el Binutils ARM 2.47 actual para el build GBA de este commit: el script `memory.ld` falla con esa versión. `agbcc`, recursos y `tools/preproc.exe` se generan siguiendo `pokeemerald/INSTALL.md` y el build GBA original.

## Reproducción desde cero

1. Instalar MSYS2 en Windows. En el shell **MINGW64**, instalar herramientas para construir pokeemerald y su preprocesador: `pacman -S --needed make git mingw-w64-x86_64-gcc mingw-w64-x86_64-binutils mingw-w64-x86_64-libpng mingw-w64-x86_64-zlib mingw-w64-x86_64-pkgconf mingw-w64-x86_64-SDL2`. Seguir `pokeemerald/INSTALL.md` para cualquier otra dependencia del build GBA.
2. En el shell **MINGW32**, instalar `pacman -S --needed mingw-w64-i686-gcc mingw-w64-i686-binutils mingw-w64-i686-SDL2 mingw-w64-i686-pkgconf mingw-w64-i686-gdb`. `pacman -Q` permite verificar las versiones instaladas; el repositorio puede publicar otras versiones en el futuro.
3. Desde PowerShell, ejecutar `./setup.ps1`; clona el commit upstream fijado y aplica los parches locales en orden. Conservar la ROM legal propia en `roms/`; para el build GBA, copiarla a `pokeemerald/baserom.gba` según `INSTALL.md`, sin mover el original.
4. Construir `agbcc` y el GBA con el Binutils ARM 2.43.1 aislado antepuesto a `PATH`, y verificar `make compare` → `OK`. Esto también genera `tools/preproc.exe` y `build/assets`. El shell MINGW32 necesita la DLL x86-64 de `preproc.exe`; `port/Makefile` antepone `/mingw64/bin` **solo** al ejecutar esa herramienta.
5. Para el PC, entrar en **MINGW32** y ejecutar `make -C port exe`. Los resultados quedan en `build/`, ignorado por Git.

El ejecutable carga `SDL2.dll` **después** de reservar las direcciones de memoria GBA con `VirtualAlloc`. `make -C port exe` copia la DLL i686 instalada en `build/SDL2.dll`, junto al `.exe`, para permitir abrirlo desde el Explorador o PowerShell sin configurar `PATH`. La DLL permanece en `build/`, ignorado por Git. El linker fija la imagen en `0x10000000` y desactiva ASLR para dejar libres las direcciones GBA. GDB i686 es una herramienta de diagnóstico opcional, instalada aquí para la primera ejecución.

MINGW32 y MINGW64 deben mantenerse separados: el `.exe` PC, SDL2 y todas sus DLL se compilan en 32 bits; el preprocesador upstream ya construido es x86-64. El repositorio público no incluye ninguna ROM, recurso ni toolchain upstream.

## Pruebas y diagnóstico

Desde la raíz del proyecto, en MINGW32:

```sh
make -C port exe
make -C port test
make -C port diagnostic-exe
python port/tests/gameplay_smoke.py build/gameplay-smoke.txt
EMERALD_PC_INPUT_SCRIPT=build/gameplay-smoke.txt \
EMERALD_PC_FAST=1 EMERALD_PC_STOP_FRAME=30500 \
EMERALD_PC_AUDIO_DUMP=build/audio.wav ./build/emerald-pc-diagnostic.exe
```

El generador del guion requiere Python 3; puede ejecutarse también desde
PowerShell antes del comando MSYS2. `test` compila con `-Wall -Wextra
-Werror` y ejecuta 21 suites: BIOS, DMA, frame, memoria, flash, entrada por
guion, PPU, bitmap, prioridad, afines, menú de velocidad, temporizadores,
reinicio, reinicio de RAM, m4a, PSG, audio, IRQ, RTC, entrada y entrada SDL.
Los binarios quedan en `build/tests/` y sus archivos temporales en `build/`.
Las pruebas unitarias no usan la ROM; construir el ejecutable y el motor
m4a requiere los recursos locales de pokeemerald.

La entrada por guion, el modo sin limitación de FPS, la parada por frame y
el volcado WAV existen solo en `emerald-pc-diagnostic.exe`. El ejecutable
normal usa el teclado y conserva el temporizador de ~59,7275 FPS (o el
multiplicador elegido con P). El WAV se finaliza al cerrar normalmente el
proceso; una terminación forzada puede dejar la cabecera incompleta.
