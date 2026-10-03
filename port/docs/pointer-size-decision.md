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

## Comparación

| Opción | Esfuerzo estimado | Riesgo principal | Problemas que evita |
| --- | --- | --- | --- |
| A: i686 | Medio para arrancar, alto a largo plazo | Dependencias y distribución de 32 bits; direcciones GBA aún sin soporte | Ensanchamiento de punteros/layouts como `ListMenu` |
| B: x86-64 y adaptación | Alto inicial | Auditoría extensa de casts, save y datos ROM | Dependencia de direcciones fijas; truncamientos implícitos; layout host confundido con serializado |
| C: x86-64 y `VirtualAlloc` fijo | Bajo para el experimento, alto para hacerlo correcto | Colisiones de direcciones y falsa sensación de compatibilidad | Algunos accesos directos a RAM/IO y casts de direcciones realmente mapeadas |

**Recomendación: B.** El dato decisivo es que tanto el save como los mapas/scripts ROM contienen representaciones de 32 bits, mientras que el host tendrá también punteros a objetos fuera de las regiones GBA. A reduce algunos síntomas de layout pero no la separación de memoria ni la emulación; C solo cubre una parte de la memoria. B establece esa separación desde el principio y permite conservar intacto el build GBA mediante `PORT_PC`. Esta decisión es propuesta; aquí no se implementa.
