# emerald-pc

Port nativo experimental a PC con SDL2 de Pokémon Emerald, basado en la decompilación de [pret/pokeemerald](https://github.com/pret/pokeemerald). Aún no es jugable: dibuja fondos de texto y afines, sprites regulares y afines, y aplica WIN0/WIN1 y mezcla de color en la introducción. Faltan la ventana de objetos, el mosaico y el audio, entre otras funciones de la GBA.

Cada usuario debe aportar su propia ROM legal de Pokémon Emerald en inglés. Este repositorio no distribuye ROMs, saves, assets ni código de pokeemerald. Es un proyecto de fans no afiliado a Nintendo, Game Freak ni The Pokémon Company.

## Preparación en Windows

1. Clona este repositorio y entra en su carpeta.
2. Ejecuta `pwsh -File .\setup.ps1` en PowerShell. El script descarga pret/pokeemerald en `pokeemerald/`, fija el commit usado por este proyecto y aplica los parches de `patches/` en orden.
3. Coloca tu ROM legal original en `roms/` y conserva ese archivo intacto. Ambas carpetas están ignoradas por Git.

El build GBA de referencia requiere las dependencias descritas en `pokeemerald/INSTALL.md`. La preparación de este repositorio se verificó en MSYS2 MINGW64 con `agbcc` y GNU Binutils ARM 2.43.1 mediante `make compare`. El script de preparación no instala la toolchain ni distribuye la ROM.

## Ejecutable de diagnóstico

Después de compilar el GBA original según `pokeemerald/INSTALL.md` y preparar
MSYS2 MINGW32 como indica `port/docs/toolchain.md`, ejecuta desde la raíz:

```sh
make -C port exe
./build/emerald-pc.exe
```

La compilación copia `SDL2.dll` junto al ejecutable en `build/`. Después
puedes abrir `build/emerald-pc.exe` directamente desde el Explorador de
Windows; conserva ambos archivos en la misma carpeta.

El ejecutable carga solo en memoria el único `.gba` de `roms/`; nunca modifica
el archivo original. El guardado experimental usa `saves/emerald-pc.sav`,
ignorado por Git. El estado del arranque y el siguiente bloqueo medido con
GDB están en `port/docs/first-run-report.md`.

## Velocidad de juego

Pulsa **P** durante el juego para abrir el menú de velocidad. El juego se
pausa mientras está abierto. Usa **↑/↓** para elegir **1×, 2×, 3× o 4×** y
**Enter** para activar la opción. **Esc** o **P** cierran el menú sin cambiar
la velocidad. La opción queda activa hasta cerrar el programa.
