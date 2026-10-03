# Inventario no C necesario para el port

Conteo reproducible sobre archivos **seguidos por Git** del checkout upstream `731ad5bfd6e6f265508d0efcca0ba42f9dcf5881` (por ejemplo, `git -C pokeemerald ls-files 'src/*.s' 'asm/*.s' 'data/*.s' '*.ld'`). No se copia ninguno al repositorio del port.

| Grupo | Cantidad | Función | ARM ejecutable |
| --- | ---: | --- | --- |
| `src/*.s` | **4** | Arranque, cabecera ROM, m4a, multiboot GameCube | **4** contienen instrucciones ARM; en `rom_header.s` es solo el salto `b Init` |
| `asm/*.s` | **0** | No hay unidades ensambladas aquí | Ninguna |
| `data/*.s` | **15** | Scripts/tablas del juego, mapas, sonido y blobs multiboot | **0**; usan directivas y macros de datos, no rutinas ARM |
| Scripts `*.ld` de la raíz | **2** | Asignan secciones y símbolos a ROM/EWRAM/IWRAM GBA | No son ensamblador |

## `src/`: cuatro unidades

* `crt0.s`: modo CPU, stacks IRQ/sistema, vector de interrupción, inicialización y entrada. Requiere un arranque host nuevo.
* `m4a_1.s`: rutinas ARM/Thumb del motor de sonido m4a (mezcla, temporización y utilidades). Requiere implementación o sustitución de audio host; no se puede enlazar a x86-64.
* `libgcnmultiboot.s`: protocolo de multiboot por JOY Bus con rutinas ARM. Requiere decidir su comportamiento en PC.
* `rom_header.s`: campos de cabecera de cartucho, espacio para el logo y un `b Init`. El formato de cabecera no forma parte de un ejecutable PC.

`asm/` contiene **24 archivos `.inc`** de macros (eventos, batalla, mapas, m4a y otras tablas); son dependencias del ensamblado de datos y código GBA, no unidades `.s` independientes. Las macros de scripts codifican instrucciones de la *máquina virtual del juego* como bytes; eso no las convierte en instrucciones ARM.

## `data/`: quince unidades

* Scripts/tablas: `battle_ai_scripts.s`, `battle_anim_scripts.s`, `battle_scripts_1.s`, `battle_scripts_2.s`, `contest_ai_scripts.s`, `event_scripts.s`, `field_effect_scripts.s`, `mystery_event_script_cmd_table.s`, `mystery_gift.s` (**9**). Predominan `.include`, `.byte`, `.2byte`, `.4byte` y macros de script.
* Mapas: `map_events.s`, `maps.s` (**2**). Agregan cabeceras, eventos y referencias a layouts; sus `.4byte` codifican punteros GBA de 32 bits.
* Multiboot: `multiboot_berry_glitch_fix.s`, `multiboot_ereader.s`, `multiboot_pokemon_colosseum.s` (**3**). Incorporan blobs con `.incbin`; no son código fuente ARM que pueda ensamblarse para x86-64.
* Sonido: `sound_data.s` (**1**). Incluye tablas de voces, samples y canciones. `sound/MPlayDef.s` (**1 adicional fuera de `data/`**) define constantes/macros de secuencias, no rutinas ARM.

Los `.inc` de mapas y sonido, binarios de layouts y samples son otras entradas del build original. El port tendrá que **leer o transformar sus representaciones**, especialmente las referencias `.4byte`; este inventario no propone distribuir esos assets.

## Enlace

`ld_script.ld` y `ld_script_modern.ld` (**2**) son scripts específicos de GBA: entrada `Start`, secciones de ROM y RAM y `INCLUDE "memory.ld"`. El Makefile genera `build/.../memory.ld` desde `memory.txt`; el script clásico también usa los `sym_*.ld` generados. Un ejecutable Windows necesita el linker del host y su propio mapa de memoria, no estos scripts. Los archivos `.ld` generados no se cuentan como fuente seguida por Git.
