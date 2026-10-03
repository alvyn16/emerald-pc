# Decisión de tamaño de punteros (diagnóstico, sin port)

Checkout inspeccionado: `731ad5bfd6e6f265508d0efcca0ba42f9dcf5881`. El diagnóstico x86-64 de 310 unidades pasa 309; el único error de sintaxis es `ListMenuTooLargeForTaskData`. Además hay 999 avisos de conversión puntero/entero en 97 unidades. `port/docs/list-menu-layout.md` mide `ListMenu` en 32 bytes GBA/i686 y 48 bytes x86-64 frente a los 32 bytes de `Task.data`.

## Datos del código que condicionan la decisión

* Hay **5 invocaciones explícitas** de `STATIC_ASSERT` en `src/` y `include/` (sin contar la definición de la macro): `include/battle.h:452`, `src/bard_music.c:121`, `src/battle_message.c:2310`, `src/list_menu.c:18`, `src/rotating_gate.c:226`. **2** usan `sizeof`; solo la de `ListMenu` falla en la pasada actual. Este conteo no pretende medir todas las dependencias de layout: también hay `offsetof`, tamaños fijos y casts sin aserción.
* `src/save.c:57-72` serializa tres raíces: `SaveBlock2`, `SaveBlock1` y `PokemonStorage`. Entre estas, **1 raíz (`SaveBlock1`) contiene al menos 1 tipo anidado con puntero**: `ObjectEventTemplate.script`, dentro de `objectEventTemplates[]` (`global.h:1019`, `global.fieldmap.h:92-110`). `SaveBlock2`, `PokemonStorage` y `BoxPokemon` no declaran punteros directos. Por tanto, la imagen del save requiere una representación de 32 bits y revisión de los tipos anidados; no basta con cambiar el tamaño del proceso.
* Como conjunto acotado y verificable de estructuras de mapa consumidas desde datos ROM, `global.fieldmap.h` define **8 tipos con punteros**: `Tileset`, `MapLayout`, `ObjectEventTemplate`, `CoordEvent`, `BgEvent`, `MapEvents`, `MapConnections` y `MapHeader`. `WarpEvent` y `MapConnection` no tienen punteros. El conteo es de *tipos de mapa*, no de todas las estructuras ROM del proyecto; hay más tablas ROM (sprites, scripts, sonido, etc.).
* Los datos de mapa expresan direcciones como palabras de **4 bytes**, por ejemplo `data/maps/AbandonedShip_Room_B1F/header.inc:6-9` usa `.4byte` para layout, eventos, scripts y conexiones. Las tablas de scripts también usan `.4byte` en `data/battle_scripts_1.s` y `data/battle_ai_scripts.s`. En C, `global.h:114-121` lee cuatro bytes (`T1_READ_32`, `T2_READ_32`) y los convierte en puntero (`T1_READ_PTR`, `T2_READ_PTR`). Una estructura nativa x86-64 no puede interpretarse directamente sobre esos bytes: sus punteros y offsets miden distinto.

## A. Proceso i686 de 32 bits

`pacman -Ss mingw-w64-i686-gcc` devuelve `mingw32/mingw-w64-i686-gcc 16.2.0-4`; está instalado. `/mingw32/bin/gcc --version` indica GCC 16.2.0. En MINGW32 (o usando la ruta explícita) se puede probar esta opción; el ejecutable no aparece automáticamente en el `PATH` de MINGW64. La prueba de layout de `ListMenu` dio 32 bytes con i686.

Ventaja: conserva ancho de puntero y muchos offsets originales, incluida la aserción de `ListMenu`. Límites: no aporta BIOS, PPU, registros, audio ni ensamblador ARM; tampoco garantiza que las direcciones GBA estén mapeadas ni que un archivo de ROM pueda cargarse en su dirección original. Condiciona la distribución del port a un proceso Windows de 32 bits y a dependencias SDL2 i686.

## B. x86-64 con representación GBA separada

Mantener punteros host de 64 bits para objetos del proceso y representar las direcciones de ROM/RAM/save de la GBA como `u32`, con traducción explícita a memoria host. Bajo `PORT_PC`, separar estructuras serializadas de estructuras de ejecución (incluyendo `ObjectEventTemplate` y el almacenamiento de `ListMenu`), y decodificar las palabras `.4byte` en lugar de reinterpretarlas como punteros host. El build ARM conservaría sus layouts originales.

Es la opción de mayor trabajo inicial, pero deja contratos de memoria y serialización explícitos. También permite validar rangos, distinguir ROM de RAM y detectar truncamientos. Los 999 avisos muestran que hay que auditar usos, no solo los dos `STATIC_ASSERT` ligados a `sizeof`.

## C. x86-64 con regiones GBA en direcciones originales

`port/experiments/virtualalloc_gba_regions.c` reserva con `VirtualAlloc(MEM_RESERVE | MEM_COMMIT)` las seis regiones pedidas y escribe/lee el primer y último byte de cada una. Compilado con GCC 16.2.0 MINGW64 (`-std=c11 -Wall -Wextra -Werror`) y ejecutado en esta máquina: **6/6 OK**:

| Región | Base | Tamaño probado | Resultado |
| --- | ---: | ---: | --- |
| EWRAM | `0x02000000` | `0x40000` | OK |
| IWRAM | `0x03000000` | `0x8000` | OK |
| IO | `0x04000000` | `0x400` | OK |
| Paletas | `0x05000000` | `0x400` | OK |
| VRAM | `0x06000000` | `0x18000` | OK |
| OAM | `0x07000000` | `0x400` | OK |

Esto haría válidos algunos accesos directos a direcciones de **RAM y registros** y algunos casts a `u32` cuando el objeto realmente esté en esas regiones. No arregla el layout de `ListMenu`, los punteros host guardados en `u32` hacia heap, código o datos fuera de ellas, las palabras `.4byte` de las tablas ROM, ni la BIOS/PPU. Tampoco reproduce la semántica de registros (DMA, interrupciones, modos de video) al escribir en memoria ordinaria. `VirtualAlloc` exige que los rangos estén libres en cada arranque; ASLR, reservas de otras bibliotecas, antivirus o versiones de Windows pueden cambiar el resultado. Además, estos rangos tienen espejos/alias GBA que una reserva simple no reproduce. El experimento demuestra viabilidad de reserva **en esta ejecución**, no un diseño de port completo.

## Medición completa i686 frente a x86-64

Se emplearon las **mismas 310 fuentes C** y GCC 16.2.0 con SDL2 2.32.10 en ambas arquitecturas. `pacman -Ss mingw-w64-i686-SDL2` confirmó `2.32.10-1`; se instalaron SDL2 i686 y `mingw-w64-i686-pkgconf` (más su dependencia `mingw-w64-i686-vulkan-loader`). El compilador i686 ya estaba instalado. El `preproc.exe` original es de 64 bits: desde MINGW32, `port/Makefile` antepone `/mingw64/bin` solo al ejecutar esa herramienta para cargar sus DLL. GCC y SDL2 del diagnóstico siguen siendo i686.

| Medición | x86-64 | i686 |
| --- | ---: | ---: |
| `.c` que pasan `-fsyntax-only` | **309/310** | **310/310** |
| Avisos de cast puntero↔entero de distinto tamaño | **999** | **3** |
| `ListMenuTooLargeForTaskData` | Falla | Pasa |
| Objetos C host obtenidos | **305/310** | **306/310** |
| Símbolos distintos sin definir al enlazar esos objetos | **2.630** | **2.614** |

Los **tres** avisos i686 están en `src/m4a.c:83,179,195`: la macro `NUM_MUSIC_PLAYERS` convierte una dirección a `u16`, menor incluso que un puntero i686. Los **16** símbolos que desaparecen del enlace i686 son exactamente los definidos por `list_menu.o`; la lista i686 no añade nombres nuevos. Cuatro unidades siguen sin producir objeto por asm ARM inline en ambas arquitecturas. Detalles y comandos: `port/docs/host-build-report.md` y `port/docs/link-report.md`.

## `.4byte`: ensamblado y enlace medidos

De los **15 `data/*.s`**, **8** escriben directamente `.4byte símbolo` en el archivo principal y **10** contienen esa forma literal al seguir `.include`. Los objetos ARM originales de **12/15** contienen relocaciones `R_ARM_ABS32`, incluidas `map_events.s` y `sound_data.s`, cuyas macros generan tablas de punteros. Los tres restantes son blobs multiboot. `arm-none-eabi-readelf -r` cuenta **37.325** entradas `R_ARM_ABS32` en las 12 unidades. Se trata de relocaciones absolutas de 32 bits; el conteo no afirma que cada una sea un puntero de juego.

Se pasó el **`data/maps.s` real** por su cadena de preprocesado `tools/preproc → GCC -E → tools/preproc -ie`, sin modificarlo. GAS lo ensambla tanto en i686 (`pe-i386`) como en x86-64 (`pe-x86-64`). `objdump -r` muestra `dir32` en i686 y `IMAGE_REL_AMD64_ADDR32` en x86-64, por ejemplo para `gTileset_General` y `gTileset_Petalburg`: **`.4byte` sigue ocupando 4 bytes en x86-64**. El enlace completo de `maps.o` requiere otros símbolos del juego, así que se aisló el comportamiento en `port/experiments/map_pointer_table.s`: dos `.4byte` hacia etiquetas propias y un `main` mínimo.

Reproducción de la muestra real, desde `pokeemerald/` en MINGW64; después se usa cada shell MinGW para ensamblar el mismo flujo:

```sh
tools/preproc/preproc.exe data/maps.s charmap.txt \
  | gcc -E -iquote include -Wno-trigraphs -DMODERN=0 \
      -I tools/agbcc/include -I tools/agbcc -nostdinc -undef -std=gnu89 - \
  | tools/preproc/preproc.exe -ie data/maps.s charmap.txt \
  > ../build/maps-preprocessed-original.s
gcc -c -x assembler -I. ../build/maps-preprocessed-original.s -o ../build/maps-ARQUITECTURA.o
objdump -r ../build/maps-ARQUITECTURA.o
```

Para el enlace aislado, desde la raíz y en cada shell: `gcc -c port/experiments/map_pointer_table.s -o build/map-pointer-ARQUITECTURA.o`, seguido de `gcc port/experiments/map_pointer_link_main.c build/map-pointer-ARQUITECTURA.o -o build/map-pointer-ARQUITECTURA.exe`. La tercera variante añade `-Wl,--image-base,0x10000000` al segundo comando x86-64.

| Enlace del experimento | Resultado |
| --- | --- |
| GCC i686, base PE normal | **OK**; `dir32` |
| GCC x86-64, base PE normal | **Falla** dos veces: `relocation truncated to fit: IMAGE_REL_AMD64_ADDR32 against .rdata` |
| GCC x86-64 con `-Wl,--image-base,0x10000000` | **OK** en esta prueba; `ImageBase=0x10000000` |

La base baja solo hace que **esas direcciones** quepan en 32 bits. No convierte una tabla `.4byte` en `void *[ ]` de x86-64: leer elementos de 8 bytes combinaría entradas vecinas. Tampoco sitúa ROM, heap, DLLs y datos host bajo 4 GB. El problema de x86-64 **sin solución barata** es la coexistencia de miles de palabras/relocaciones GBA de 32 bits con punteros host de 64 bits y estructuras/save que dependen de su ancho. Se necesita un formato host transformado o decodificar `u32` a punteros host en cada consumidor, además de corregir layouts y casts; un flag de compilador, `VirtualAlloc` o una base PE baja no bastan.

## Costes comprobados y decisión

| Opción | Evidencia medida | Desventaja concreta pendiente |
| --- | --- | --- |
| A: i686 | 310/310 sintaxis, 3 avisos, `ListMenu` pasa, tabla `.4byte` enlaza | Límite de direcciones virtuales; DLL SDL2 i686; dependencia del repositorio MINGW32; BIOS/ARM/hardware aún pendientes |
| B: x86-64 adaptado | 309/310, 999 avisos, tabla `.4byte` falla con base normal | Convertir o decodificar datos ROM de 32 bits y revisar layouts, save y casts |
| C: x86-64 con `VirtualAlloc` fijo | 6/6 regiones GBA reservadas y base baja enlaza la tabla mínima | No resuelve el layout, datos ROM fuera de esas regiones ni semántica de registros |

Un proceso i686 en Windows x64 tiene **2 GB** de espacio virtual por defecto o **4 GB** con `LARGEADDRESSAWARE` ([Microsoft](https://learn.microsoft.com/en-us/windows/win32/memory/memory-limits-for-windows-releases)); los recursos descomprimidos y caches compartirían ese límite. Se necesitan SDL2 y demás DLL **de 32 bits**; SDL2 i686 **2.32.10** está disponible hoy ([MSYS2](https://packages.msys2.org/packages/mingw-w64-i686-SDL2?repo=mingw32)). [MSYS2 inició en 2023 la retirada gradual de paquetes MINGW32](https://www.msys2.org/news/), así que no debe asumirse disponibilidad futura del mismo conjunto de dependencias. Son riesgos concretos de mantenimiento, no fallos actuales de esta prueba.

**Recomendación final para este hito: A, i686.** Es la única opción que hoy pasa las 310 fuentes sin adaptar layouts y permite enlazar una tabla GBA de punteros `.4byte` con la base normal. La mejora **999→3 avisos** y **309→310 archivos** justifica usarla para desbloquear un primer ejecutable PC. No elimina la necesidad de BIOS, memoria, PPU, sonido y asm host. Si más adelante se exige x86-64, hará falta B, con separación explícita de direcciones `u32` y punteros host. C puede servir como técnica auxiliar, pero los resultados no la respaldan como solución principal. Esta decisión documenta pruebas; no implementa todavía el port.
