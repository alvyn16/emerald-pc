# Diagnóstico de compilación x86-64 — hito 1

## Método y resultado

El build GBA original pasó `make compare` con `pokeemerald.gba: OK` y GNU Binutils ARM 2.43.1. El checkout de pret/pokeemerald sigue en `731ad5bfd6e6f265508d0efcca0ba42f9dcf5881`; no se modificó para este diagnóstico.

El build GBA procesa cada `.c` con `CPP | tools/preproc -i -g build/assets <fuente> charmap.txt | agbcc`. `scaninc` genera archivos de dependencias `.d`, pero no transforma el C entregado al compilador. `port/Makefile` reproduce la etapa `GCC -E | tools/preproc | GCC -fsyntax-only`, desde el directorio de pokeemerald para que funcionen las rutas a recursos y `charmap.txt`. Usa `tools/preproc/preproc.exe` y los recursos generados por el build original; solo los lee. No genera archivos dentro de pokeemerald.

Entorno: MSYS2 **MINGW64**, GCC 16.2.0 (`x86_64-w64-mingw32`) y SDL2 2.32.10. Reproducción desde la raíz del proyecto:

```sh
mkdir -p build
make -C port -k syntax > build/host-syntax-preproc.log 2>&1
```

Se intentaron los **310** archivos `.c` de `pokeemerald/src`. Antes de introducir `tools/preproc`, **191 pasaban y 119 fallaban** (540 diagnósticos `error:`). Con la tubería original de preprocesado, **300 pasan y 10 fallan** (10 diagnósticos `error:`). No queda ningún error de `INCGFX_*`, `INCBIN_*`, `_()` o `__()`. El código de salida de `make` sigue siendo 2 porque el objetivo diagnóstico incluye los diez fallos. El log completo está en `build/`, ignorado por Git.

Los conteos siguientes son archivos `.c` distintos. `-fmax-errors=5` limita los errores visibles por unidad, y `-fsyntax-only` no ensambla ni enlaza; pasar esta comprobación no demuestra que exista un ejecutable x86-64. Los grupos de referencias estáticas se solapan con los errores y entre sí.

## Errores de sintaxis restantes

| Tipo | Archivos | Ejemplos y causa | Solución propuesta; no aplicada |
| --- | ---: | --- | --- |
| `abs` sin declaración | **9** | `src/battle_anim_effects_3.c:1655`, `src/contest.c:3727` y `src/pokemon_storage_system.c:8364` llaman `abs` sin que GCC host vea su prototipo. | Probar la inclusión host de `<stdlib.h>` durante el diagnóstico y comprobar si revela errores adicionales. Mantener cualquier ajuste de código necesario tras `PORT_PC` y fuera del build GBA. |
| Layout dependiente de punteros de 32 bits | **1** | `src/list_menu.c:18` falla la aserción `ListMenuTooLargeForTaskData`; `include/list_menu.h:82` define `ListMenu` con punteros; `include/task.h:20` ofrece `Task.data` como almacenamiento fijo. En x86-64 la estructura ya no cabe. Es el único archivo que falla por este tipo en el log. | Diseñar almacenamiento host separado o una representación compatible bajo `PORT_PC`, sin cambiar el layout del juego GBA. Medir los tamaños antes de elegir la adaptación. |

## Riesgos adicionales que la sintaxis no resuelve

| Grupo | Archivos | Evidencia y ejemplos | Ruta posterior |
| --- | ---: | --- | --- |
| Casts entre punteros y enteros de distinto tamaño | **97** unidades; **999** avisos de GCC | `src/agb_flash.c:44`, `src/task.c:152` y `src/window.c:548`. Pueden truncar direcciones aunque la sintaxis pase. | Separar punteros host de direcciones GBA; usar tipos de ancho apropiado y revisar cada conversión antes de ejecutar. |
| Ensamblador ARM inline | **5** archivos con `asm` directo; **4** fallan al compilar una muestra a objetos x86-64 | `src/librfu_intr.c:405` (`bx r2`), `src/m4a.c:330` (`swi 0x2A`) y `src/multiboot.c:442` (`.syntax unified`). `src/script.c` también falla; `src/libisagbprn.c` produce objeto con `.hword`, sin validar su semántica. | Aislar las rutinas por plataforma y proporcionar equivalentes host en `port/`. |
| Registros y memoria GBA | **124** archivos con `REG_*` o literales de memoria GBA | `src/agb_flash.c:85` lee `REG_IME`; `src/gpu_regs.c:75` lee `REG_DISPCNT`; `src/main.c:309` escribe `REG_IME`. `include/gba/io_reg.h` fija la base de registros en 0x04000000. | Definir una interfaz host de registros. La emulación de video, VRAM, paletas y OAM corresponde a hitos posteriores. |
| Llamadas BIOS GBA | **48** archivos con llamadas directas seleccionadas | `src/main.c:437` llama `SoftReset`; `src/battle_transition.c:1776` llama `CpuSet`; `src/battle_transition_frontier.c:227` llama `LZ77UnCompVram`. | Definir contratos e implementaciones host verificadas antes del enlace. |
| Cabeceras y tipos GBA | **307** archivos incluyen directamente `global.h` o `gba/...` | `src/main.c:1`, `src/agb_flash.c` y `src/m4a.c:2`. Ninguno falló por cabecera ausente en esta pasada, pero siguen dependiendo de tipos y declaraciones GBA. | Mantener tipos de ancho fijo y aislar las interfaces de plataforma sin copiar código upstream al repositorio público. |

## Siguiente grupo recomendado

Resolvería primero **`abs` sin declaración**: concentra **9 de los 10** fallos actuales y podría comprobarse con un único ajuste de inclusión de cabecera en la compilación host. Eso deja aislada la aserción de tamaño de `ListMenu`, que requiere una decisión de representación en 64 bits. Después abordaría las conversiones de punteros, pues los 999 avisos son un riesgo de ejecución aunque GCC acepte la sintaxis. Ninguno de esos cambios de solución se hizo en esta sesión.

Este informe sigue siendo un diagnóstico: no hay port, ventana SDL2 ni ejecutable host. No se modificaron `pokeemerald/src`, `include` ni `data`, y no se incorporaron ROMs ni assets al repositorio público.
