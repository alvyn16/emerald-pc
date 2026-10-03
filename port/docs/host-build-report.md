# Diagnóstico de compilación x86-64 — hito 1

## Alcance y reproducción

El build GBA original sigue pasando `make compare`: `pokeemerald.gba: OK`, usando GNU Binutils ARM 2.43.1. El checkout de pret/pokeemerald es `731ad5bfd6e6f265508d0efcca0ba42f9dcf5881` y no se modificó para este diagnóstico.

En MSYS2 **MINGW64** se usaron GCC 16.2.0 (`x86_64-w64-mingw32`) y SDL2 2.32.10. Desde la raíz del proyecto:

```sh
mkdir -p build
make -C port -k syntax > build/host-syntax.log 2>&1
```

`port/Makefile` intenta los 310 archivos `.c` de `pokeemerald/src` con `-std=gnu11 -fsyntax-only -fmax-errors=5 -DMODERN=0 -DPORT_PC`, las cabeceras de pokeemerald y los flags de SDL2 obtenidos con `pkg-config`. `make -k` continúa tras cada error. La salida esperada del diagnóstico actual es código 2: **191 unidades pasan sintaxis y 119 fallan**, con 540 líneas `error:` y 617 `warning:`. El log queda en `build/`, ignorado por Git.

Los conteos de abajo son **archivos `.c` distintos**, no ocurrencias, y los grupos se solapan. “Diagnóstico” cuenta unidades que GCC señaló en el log; “referencia” cuenta archivos con una coincidencia directa en su fuente. `-fmax-errors=5` limita lo que GCC muestra por unidad, y `-fsyntax-only` no ensambla ni enlaza: pasar sintaxis no demuestra que un objeto o ejecutable x86-64 funcione. Los 307 archivos que incluyen `global.h` o `gba/...` no fallan por cabecera ausente; esa cifra mide dependencia de la interfaz GBA.

## Grupos de problemas

| Grupo | Archivos afectados | Evidencia y ejemplos | Propuesta para un hito posterior |
| --- | ---: | --- | --- |
| Punteros de 32 bits y `sizeof` | **59** unidades con diagnóstico: 58 con 615 avisos de cast puntero/entero de distinto tamaño, más 1 aserción de tamaño | `src/agb_flash.c:44` convierte punteros a `u32`; `src/battle_anim.c:369` convierte un entero en puntero; `src/list_menu.c:18` falla `ListMenuTooLargeForTaskData` porque la estructura contiene punteros de tamaño host. | Inventariar cada cast y usar `uintptr_t` para direcciones host; separar direcciones GBA de punteros del proceso. Para estructuras GBA que dependen del tamaño de puntero, almacenar identificadores o estado host fuera de la estructura bajo `PORT_PC`, conservando el layout GBA original. |
| Ensamblador ARM inline | **5** archivos con `asm`/`asm_unified` directo; **4** fallaron en una prueba adicional de compilación a objeto | `src/librfu_intr.c:405` (`bx r2`), `src/m4a.c:330` (`swi 0x2A`) y `src/multiboot.c:442` (`.syntax unified`, instrucciones ARM) fallan con el ensamblador x86-64. `src/script.c:106` (`svc 2`) también falla. `src/libisagbprn.c` usa `.hword`: produjo objeto, pero eso no valida su comportamiento en PC. | Aislar esas rutinas por plataforma y proporcionar equivalentes C/host en `port/`; reservar parches mínimos protegidos con `#ifdef PORT_PC` cuando sea imprescindible tocar el código upstream. |
| Registros de hardware y direcciones GBA | **124** archivos con referencias directas a `REG_*` o literales de memoria GBA | `src/agb_flash.c:85` lee `REG_IME`; `src/gpu_regs.c:75` lee `REG_DISPCNT`; `src/main.c:309` escribe `REG_IME`. `include/gba/io_reg.h:4` define `REG_BASE` como `0x4000000` (0x04000000). Estas expresiones pueden pasar sintaxis pero apuntarían a direcciones inválidas en PC. | Crear una interfaz de registros en `port/` con almacenamiento host y accesores; sustituir el acceso directo bajo `PORT_PC` por parches delimitados. La semántica de video, VRAM, paletas y OAM pertenece a hitos posteriores. |
| Llamadas a la BIOS GBA | **48** archivos con llamadas directas a funciones BIOS seleccionadas | `src/main.c:437` llama `SoftReset`; `src/battle_transition.c:1776` llama `CpuSet`; `src/battle_transition_frontier.c:227` llama `LZ77UnCompVram`. Sus declaraciones están en `include/gba/syscall.h`, pero el host no tiene BIOS GBA. | Definir contratos host para reset, copia/descompresión, espera y matemáticas; implementar equivalentes en `port/` y verificar su semántica antes de enlazar. |
| Cabeceras y tipos propios de GBA | **307** archivos incluyen directamente `global.h` o `gba/...`; ninguno falló por cabecera ausente en esta pasada | `src/main.c:1` incluye `global.h`; `src/agb_flash.c` incluye cabeceras `gba/...`; `src/m4a.c:2` incluye `gba/m4a_internal.h`. Tipos como `u32`, `bool8` y estructuras de GBA llegan transitivamente desde esas cabeceras. | Mantener tipos de ancho fijo y una fachada de plataforma en `port/`; definir cuidadosamente qué declaraciones del GBA siguen siendo datos y cuáles requieren implementación host. Evitar copiar cabeceras o código upstream al repo público. |
| Otros: macros de recursos/texto y biblioteca C | **116** unidades con errores de `INCGFX`/`INCBIN`/`_`/`__`; **4** unidades con declaración implícita de `abs` (1 se solapa con las 116) | `src/anim_mon_front_pics.c:3` usa `INCGFX_U32`; `src/battle_anim_water.c:59` usa `INCBIN_U8`; `src/battle_message.c:55` usa `_`. `src/battle_anim_effects_3.c:1655` usa `abs`. El Makefile GBA pasa por `tools/preproc` y `charmap.txt` antes de `agbcc`; el diagnóstico host todavía no reproduce esa etapa. | Reproducir la transformación de recursos y texto para GCC host, generando resultados solo en `build/` o dentro de `pokeemerald/`, ambos ignorados. Resolver después las pocas declaraciones estándar faltantes con includes o adaptadores mínimos. No publicar assets generados. |

## Orden de ataque propuesto

1. **Preprocesamiento host de recursos y texto.** Es el bloqueo de sintaxis más amplio: 116 de las 119 unidades fallidas muestran esas macros. Reutilizar el significado de `tools/preproc` y generar datos locales ignorados desbloquearía la mayoría sin alterar el build GBA.
2. **Aserción de layout y declaraciones estándar.** Investigar `ListMenu` frente a `Task.data` en 64 bits y resolver `abs`; son cambios pequeños que permiten separar fallos reales de ruido del primer paso.
3. **Tipos, punteros y direcciones.** Clasificar los 615 avisos de cast de 58 unidades antes de ejecutar código host. Mantener punteros x86-64 de ancho completo y representar las direcciones GBA como direcciones emuladas.
4. **Ensamblador ARM.** Reemplazar las cuatro rutinas que el ensamblador x86-64 rechaza y revisar la quinta que produjo objeto, sin cambiar la ruta ARM.
5. **Interfaz GBA de ejecución.** Encapsular los registros usados directamente en 124 archivos y las llamadas BIOS de 48 archivos; enlazar únicamente cuando existan implementaciones host. La emulación y SDL2 funcional corresponden a hitos siguientes.

Este informe es un mapa de bloqueos, no un port. No se modificaron `pokeemerald/src`, `include` ni `data`, ni se incorporaron ROMs o assets al repositorio público.
