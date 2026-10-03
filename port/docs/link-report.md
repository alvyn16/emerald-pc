# Enlace de prueba x86-64

Checkout upstream: `731ad5bfd6e6f265508d0efcca0ba42f9dcf5881`. Entorno: MSYS2 MINGW64, GCC 16.2.0, SDL2 2.32.10. `port/Makefile` agrega objetivos diagnósticos que ejecutan `GCC -E | tools/preproc | GCC -c` y luego intentan un enlace MinGW. Los objetos y logs quedan en `build/`, ignorado por Git; el enlace usa solo objetos C host, `-nostartfiles -Wl,-e,AgbMain` y SDL2. La entrada es solo para pedir diagnóstico al linker, **no** para ejecutar el programa.

```sh
mkdir -p build
make -C port -k objects > build/host-objects.log 2>&1
make -C port link-probe > build/host-link.log 2>&1
```

De 310 fuentes `.c`, **305** generaron objeto. Fallaron `list_menu.c` por `ListMenuTooLargeForTaskData`, y `librfu_intr.c`, `m4a.c`, `multiboot.c`, `script.c` porque el ensamblador x86-64 no acepta su ARM inline (`bx`, `swi`, `.syntax`, `svc`). `libisagbprn.c` produjo objeto, pero eso no demuestra que su asm tenga semántica correcta en PC. El enlace devolvió **exit 2 de make / exit 1 de ld**; no generó un ejecutable válido.

Se contaron las líneas `undefined reference to` de `build/host-link.log` y se deduplicó por nombre exacto. Resultado: **3.956 referencias a 2.630 símbolos distintos**. Las clases son disjuntas; la clasificación es diagnóstica, no una lista de implementaciones.

| Categoría | Símbolos distintos | Referencias | Ejemplos / origen |
| --- | ---: | ---: | --- |
| BIOS GBA | **14** | 447 | `CpuSet`, `CpuFastSet`, `LZ77UnCompVram`, `SoftReset`, `VBlankIntrWait`; declaraciones en `include/gba/syscall.h` sin implementación host. |
| Registros `REG_*` | **0** | 0 | `REG_IME`, `REG_DISPCNT` y similares se expanden a accesos a direcciones fijas en headers. Son un riesgo de ejecución, no símbolos externos de linker. |
| Motor m4a / audio | **58** | 211 | `m4aSoundMain`, `m4aMPlayStop`, `ply_goto`, `SoundMainBTM`, `gMPlayInfo_BGM`; faltan `m4a.c`, `src/m4a_1.s` y datos de sonido. |
| Plataforma / arranque y comunicación | **10** | 12 | `IntrMain`, `GameCubeMultiBoot_Init`, `MultiBootMain`; provienen de arranque/IRQ y multiboot ARM, no de SDL2. |
| Otros | **2.548** | 3.286 | `gText_ApprenticePleaseTeach0`, `BattleScript_AbilityCuredStatus`, `EventScript_RepelWoreOff`, `gMapGroups`, `ScriptContext_Enable`, `ListMenuInit`. Predominan tablas/scripts/texto no enlazados porque los `.s` de datos no se convirtieron; también faltan funciones de las unidades C que no produjeron objeto. |
| **Total** | **2.630** | **3.956** | |

Reglas del conteo: BIOS es el conjunto de nombres declarados en `include/gba/syscall.h` que aparece sin definición (14; `MultiBoot` no se referencia). Audio abarca prefijos `m4a`, `ply_`, `gMPlayInfo_` y nombres `SoundMainBTM`, `gSoundInfo`. Plataforma abarca `IntrMain`, `GameCubeMultiBoot_*` y `MultiBoot*` excepto el nombre BIOS exacto `MultiBoot`. Registros es el prefijo `REG_`; el resto queda en «otros». Dentro de «otros» hay **538** nombres `gText_*`, **197** `BattleScript_*` y **60** `EventScript_*` (subconjuntos, no categorías adicionales). Este recuento depende de las 305 unidades incluidas: al incorporar datos y resolver errores de compilación aparecerán o desaparecerán símbolos.

El resultado muestra que el obstáculo principal para un enlace completo no es solo la BIOS: también hacen falta una estrategia para los datos/recursos y sustitutos de código ARM. No se agregó ninguno en esta tarea.
