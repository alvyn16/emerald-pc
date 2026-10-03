# Diagnóstico de compilación x86-64 — hito 1

## Método y resultado

El build GBA original pasó `make compare` con `pokeemerald.gba: OK` y GNU Binutils ARM 2.43.1. El checkout de pret/pokeemerald sigue en `731ad5bfd6e6f265508d0efcca0ba42f9dcf5881`; no se modificó para este diagnóstico.

El build GBA procesa cada `.c` con `CPP | tools/preproc -i -g build/assets <fuente> charmap.txt | agbcc`. `scaninc` genera archivos de dependencias `.d`, pero no transforma el C entregado al compilador. `port/Makefile` reproduce la etapa `GCC -E | tools/preproc | GCC -fsyntax-only`, desde el directorio de pokeemerald para que funcionen las rutas a recursos y `charmap.txt`. Usa `tools/preproc/preproc.exe` y los recursos generados por el build original; solo los lee. Añade `-include stdlib.h` en **GCC -E** para declarar `abs` una sola vez, antes de `tools/preproc`. No genera archivos dentro de pokeemerald.

Entorno: MSYS2 **MINGW64**, GCC 16.2.0 (`x86_64-w64-mingw32`) y SDL2 2.32.10. Reproducción desde la raíz del proyecto:

```sh
mkdir -p build
make -C port -k syntax > build/host-syntax-stdlib.log 2>&1
```

Se intentaron los **310** archivos `.c` de `pokeemerald/src`. Antes de introducir `tools/preproc`, **191 pasaban y 119 fallaban** (540 diagnósticos `error:`). Con el preprocesado, **300 pasaban y 10 fallaban**. Tras incluir `<stdlib.h>` en la fase host de preprocesado, **309 pasan y 1 falla** (un diagnóstico `error:`). No quedan errores de `INCGFX_*`, `INCBIN_*`, `_()`, `__()` ni `abs`. El código de salida de `make` sigue siendo 2 porque el objetivo diagnóstico incluye el fallo restante. El log completo está en `build/`, ignorado por Git.

Los conteos siguientes son archivos `.c` distintos. `-fmax-errors=5` limita los errores visibles por unidad, y `-fsyntax-only` no ensambla ni enlaza; pasar esta comprobación no demuestra que exista un ejecutable x86-64. Los grupos de referencias estáticas se solapan con los errores y entre sí.

## Errores de sintaxis restantes

| Tipo | Archivos | Ejemplos y causa | Solución propuesta; no aplicada |
| --- | ---: | --- | --- |
| Layout dependiente de punteros de 32 bits | **1** | `src/list_menu.c:18` falla la aserción `ListMenuTooLargeForTaskData`; `include/list_menu.h:82` define `ListMenu` con punteros; `include/task.h:20` ofrece `Task.data` como almacenamiento fijo. En x86-64 la estructura ya no cabe. Es el único archivo que falla por este tipo en el log. | Diseñar almacenamiento host separado o una representación compatible bajo `PORT_PC`, sin cambiar el layout del juego GBA. Medir los tamaños antes de elegir la adaptación. |

Los **9** fallos anteriores por `abs` desaparecieron. Ejemplos: `src/battle_anim_effects_3.c:1655`, `src/contest.c:3727` y `src/pokemon_storage_system.c:8364`. Una prueba de poner `-include stdlib.h` en la **segunda** invocación de GCC produjo redefiniciones de cabeceras CRT, porque el flujo ya estaba preprocesado; colocarlo en `GCC -E` corrigió eso sin tocar pokeemerald.

## Riesgos adicionales que la sintaxis no resuelve

| Grupo | Archivos | Evidencia y ejemplos | Ruta posterior |
| --- | ---: | --- | --- |
| Casts entre punteros y enteros de distinto tamaño | **97** unidades; **999** avisos de GCC | `src/agb_flash.c:44`, `src/task.c:152` y `src/window.c:548`. Pueden truncar direcciones aunque la sintaxis pase. | Separar punteros host de direcciones GBA; usar tipos de ancho apropiado y revisar cada conversión antes de ejecutar. |
| Ensamblador ARM inline | **5** archivos con `asm` directo; **4** fallan al compilar una muestra a objetos x86-64 | `src/librfu_intr.c:405` (`bx r2`), `src/m4a.c:330` (`swi 0x2A`) y `src/multiboot.c:442` (`.syntax unified`). `src/script.c` también falla; `src/libisagbprn.c` produce objeto con `.hword`, sin validar su semántica. | Aislar las rutinas por plataforma y proporcionar equivalentes host en `port/`. |
| Registros y memoria GBA | **124** archivos con `REG_*` o literales de memoria GBA | `src/agb_flash.c:85` lee `REG_IME`; `src/gpu_regs.c:75` lee `REG_DISPCNT`; `src/main.c:309` escribe `REG_IME`. `include/gba/io_reg.h` fija la base de registros en 0x04000000. | Definir una interfaz host de registros. La emulación de video, VRAM, paletas y OAM corresponde a hitos posteriores. |
| Llamadas BIOS GBA | **48** archivos con llamadas directas seleccionadas | `src/main.c:437` llama `SoftReset`; `src/battle_transition.c:1776` llama `CpuSet`; `src/battle_transition_frontier.c:227` llama `LZ77UnCompVram`. | Definir contratos e implementaciones host verificadas antes del enlace. |
| Cabeceras y tipos GBA | **307** archivos incluyen directamente `global.h` o `gba/...` | `src/main.c:1`, `src/agb_flash.c` y `src/m4a.c:2`. Ninguno falló por cabecera ausente en esta pasada, pero siguen dependiendo de tipos y declaraciones GBA. | Mantener tipos de ancho fijo y aislar las interfaces de plataforma sin copiar código upstream al repositorio público. |

## Siguiente grupo recomendado

El único error de sintaxis que queda es la aserción de `ListMenu`; requiere una decisión de representación en 64 bits. Después abordaría las conversiones de punteros, pues los 999 avisos son un riesgo de ejecución aunque GCC acepte la sintaxis. Aún no se implementó una adaptación de tamaño de punteros.

Este informe sigue siendo un diagnóstico: no hay port, ventana SDL2 ni ejecutable host. No se modificaron `pokeemerald/src`, `include` ni `data`, y no se incorporaron ROMs ni assets al repositorio público.

## Medición adicional i686 (MINGW32)

`pacman -Ss mingw-w64-i686-SDL2` confirmó el paquete **2.32.10-1**. Se instalaron `mingw-w64-i686-SDL2` y `mingw-w64-i686-pkgconf` (dependencia adicional: `mingw-w64-i686-vulkan-loader`); `mingw-w64-i686-gcc` **16.2.0-4** ya estaba instalado. `gcc -dumpmachine` en MINGW32 devuelve `i686-w64-mingw32`; `pkg-config --modversion sdl2` devuelve `2.32.10`.

```sh
# Dentro del shell MSYS2 MINGW32, desde la raíz del proyecto:
make -C port -k syntax HOST_ARCH=i686 > build/host-syntax-i686.log 2>&1
```

Resultado: **310/310** archivos pasan, **0** errores de sintaxis y salida `make` **0**. `src/list_menu.c` pasa `ListMenuTooLargeForTaskData` (su estructura mide 32 bytes en i686). Quedan **3** avisos `cast from pointer to integer of different size`, todos en `src/m4a.c:83,179,195`: `NUM_MUSIC_PLAYERS` convierte la dirección de `gNumMusicPlayers` a `u16`, que sigue siendo menor que un puntero i686. Hay un aviso adicional de trigraph en `src/strings.c`, ajeno al ancho de puntero. Comparación directa: **999** avisos puntero/entero en x86-64 frente a **3** en i686.

El `preproc.exe` original es x86-64 y necesita la DLL `libgcc_s_seh-1.dll` de MINGW64; al ejecutar desde MINGW32 sin ajustar su `PATH` sale con código 127 y rompe la tubería. `port/Makefile` antepone `/mingw64/bin` **solo** a ese proceso. GCC, `pkg-config` y SDL2 de la medición siguen siendo i686. La primera pasada fallida por DLL no se contó como diagnóstico C.
