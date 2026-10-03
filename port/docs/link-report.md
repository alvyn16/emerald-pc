# Enlace de prueba x86-64

Checkout upstream: `731ad5bfd6e6f265508d0efcca0ba42f9dcf5881`. Entorno: MSYS2 MINGW64, GCC 16.2.0, SDL2 2.32.10. `port/Makefile` agrega objetivos diagnósticos que ejecutan `GCC -E | tools/preproc | GCC -c` y luego intentan un enlace MinGW. Los objetos y logs quedan en `build/`, ignorado por Git; el enlace usa solo objetos C host, `-nostartfiles -Wl,-e,AgbMain` y SDL2. La entrada es solo para pedir diagnóstico al linker, **no** para ejecutar el programa.

```sh
mkdir -p build
make -C port -k objects > build/host-objects.log 2>&1
make -C port link-probe > build/host-link.log 2>&1
```

De 310 fuentes `.c`, **305** generaron objeto. Fallaron `list_menu.c` por `ListMenuTooLargeForTaskData`, y `librfu_intr.c`, `m4a.c`, `multiboot.c`, `script.c` porque el ensamblador x86-64 no acepta su ARM inline (`bx`, `swi`, `.syntax`, `svc`). `libisagbprn.c` produjo objeto, pero eso no demuestra que su asm tenga semántica correcta en PC. El enlace devolvió **exit 2 de make / exit 1 de ld**; no generó un ejecutable válido.

Se contaron las líneas `undefined reference to` de `build/host-link.log` y se deduplicó por nombre exacto. Resultado: **3.956 referencias a 2.630 símbolos distintos**. Para atribuir **definiciones reales**, se ejecutó `arm-none-eabi-nm -A -g --defined-only` de Binutils 2.43.1 sobre los 15 objetos ARM originales `build/emerald/data/*.o`, los cuatro objetos de `src/*.s` y los cinco objetos ARM correspondientes a los `.c` que no produjeron objeto host. Este índice solo se lee desde `pokeemerald/`, que está ignorado. Las clases siguientes son disjuntas y se asignan por proveedor en ese orden.

| Proveedor en el build ARM | Símbolos distintos | Referencias | Ejemplos |
| --- | ---: | ---: | --- |
| Datos definidos en `data/*.s` | **2.478** | 2.551 | `gText_ApprenticePleaseTeach0` (`event_scripts.o`), `BattleScript_AbilityCuredStatus` (`battle_scripts_1.o`), `gMapGroups` (`maps.o`); también datos de sonido. |
| Otros `.s` (`src/*.s`) | **33** | 44 | `IntrMain` (`crt0.o`), `GameCubeMultiBoot_Init` (`libgcnmultiboot.o`), `ply_goto` y `SoundMainBTM` (`m4a_1.o`). |
| BIOS GBA | **14** | 447 | `CpuSet`, `LZ77UnCompVram`, `SoftReset`, `VBlankIntrWait`; sin proveedor en esos objetos, declarados en `include/gba/syscall.h`. |
| m4a C no compilado | **51** | 201 | `m4aSoundMain`, `m4aMPlayStop`, `gMPlayInfo_BGM`; definidos en el objeto ARM `src/m4a.o`. |
| Plataforma C no compilada | **5** | 6 | `IntrSIO32` (`librfu_intr.o`) y `MultiBootInit`, `MultiBootMain`, `MultiBootStartMaster`, `MultiBootCheckComplete` (`multiboot.o`). |
| Otros C no compilados | **49** | 707 | `ScriptContext_Enable`, `RunOnLoadMapScript` (`script.o`) y `ListMenuInit`, `DestroyListMenuTask` (`list_menu.o`). |
| **Total** | **2.630** | **3.956** | |

Los **14** símbolos sin proveedor en los objetos inspeccionados coinciden con funciones BIOS de `include/gba/syscall.h`. No hay símbolos externos `REG_*`: `REG_IME`, `REG_DISPCNT` y similares se expanden a direcciones fijas y serán un problema de ejecución, no de enlace. La clasificación anterior por *nombre* mezclaba `ply_*` e `IntrMain` con m4a/plataforma; esta tabla usa el objeto ARM que realmente los define. El recuento cambiará al incorporar datos u otros objetos host.

## Comparación i686

En MINGW32 con GCC i686 16.2.0 y SDL2 i686 2.32.10, `make -C port -k objects HOST_ARCH=i686` produjo **306/310** objetos. Fallan solo los cuatro `.c` con asm ARM inline: `librfu_intr.c`, `m4a.c`, `multiboot.c` y `script.c`; `list_menu.c` sí produce objeto. `make -C port link-probe HOST_ARCH=i686` falla con **4.008 referencias a 2.614 símbolos distintos**. El conjunto i686 es el de x86-64 menos **exactamente 16** símbolos definidos por `list_menu.o`; no introduce nombres nuevos. Logs completos: `build/host-objects-i686.log` y `build/host-link-i686.log` (ignorados).

El resultado muestra que el obstáculo principal para un enlace completo no es solo la BIOS: también hacen falta una estrategia para los datos/recursos y sustitutos de código ARM. No se agregó ninguno en esta tarea.
