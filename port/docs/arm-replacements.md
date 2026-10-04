# Sustitutos host para ensamblador ARM

Se inspeccionaron las cuatro unidades C que no producían objeto i686 y los cuatro
`src/*.s`. Ningún archivo `src/`, `include/` o `data/` entra en el repositorio
público. El host usa código propio en `port/`, más dos guardas `PORT_PC` en
parches `git format-patch`.

| Fuente ignorada | Trabajo ARM concreto | Decisión para este hito |
| --- | --- | --- |
| `src/librfu_intr.c` | Tres callbacks `NAKED` terminan con `bx r2`, `bx r1` y `bx r0`: salto al callback pasado por registro, según ABI ARM. El archivo también despacha interrupciones serie RFU. | Excluir la unidad del host; `port/arm_stubs.c` proporciona `IntrSIO32` sin usar hardware serie. |
| `src/m4a.c` | Un `swi 0x2A` en `MusicPlayerJumpTableCopy` invoca un servicio BIOS; el resto es el mezclador y control m4a GBA. | Excluir la unidad; `port/audio_silent.c` define las entradas m4a usadas y estado musical vacío. El audio queda silencioso. |
| `src/multiboot.c` | `MultiBootWaitCycles` es ARM `NAKED`: lee `pc`, selecciona una constante según región y hace un bucle de ciclos con `subs`/`bgt`. | Excluir la unidad; las entradas multiboot de `port/arm_stubs.c` avisan y devuelven fallo o estado incompleto. |
| `src/script.c` | Solo `asm("svc 2")` en un bucle infinito cuando el intérprete ve `gNullScriptPtr`: HALT de BIOS. | Compilar el intérprete C completo; parche `0001` sustituye solo ese HALT bajo `PORT_PC` por una trampa host. |
| `src/crt0.s` | Arranque ARM (pilas, salto a `AgbMain`) y despachador de IRQ `IntrMain`. | `port/main.c` proporciona `main`; `port/arm_stubs.c` declara un bloque `IntrMain` no ejecutable de 0x800 bytes. No hay IRQ emuladas aún. |
| `src/m4a_1.s` | Mezclador de muestras y handlers `ply_*` en ARM/Thumb. | Entradas `ply_*` silenciosas en `port/audio_silent.c`. |
| `src/libgcnmultiboot.s` | Transferencia serial GameCube multiboot, íntegramente Thumb. | Funciones host seguras que no afirman completar un enlace. |
| `src/rom_header.s` | Cabecera y constantes ROM, además de símbolos GPIO próximos a `0x080000C4`; solo datos salvo el salto inicial ARM. | `port/arm_stubs.c` da `RomHeaderGameCode`, versión y variable GPIO. El hito 3 mapea los accesos numéricos RTC a `0x080000C4`–`0x080000C8` y declara RTC ausente. |

`src/link_rfu_2.c` no contiene asm, pero `InitRFU` llama a
`AgbRFU_SoftReset`, que espera a que avance `REG_TMCNT_L`. Sin emular el timer
se bloquea en el arranque. El parche `0002` hace que solo `InitRFU` vuelva
inmediatamente bajo `PORT_PC`; la ruta GBA es idéntica. Un intento de redirigir
la llamada con `ld --wrap` no cambió la referencia COFF en este enlace.

Evolución medida de símbolos **distintos** sin definir:

| Etapa del enlace i686 | Pendientes | Categorías resueltas |
| --- | ---: | --- |
| 306 objetos C, sin datos | 2614 | Punto de partida del informe anterior. |
| Más 15 `data/*.s` | 666 | Tablas, mapas, textos y scripts de datos. |
| Más 530 canciones y `port/bios.c` | 122 | Música generada y BIOS. |
| Más `script.c` compilado con parche `0001` | 89 | Intérprete de scripts. |
| Más `port/audio_silent.c` | 14 | 75 nombres de m4a, handlers ARM y estado de audio. |
| Más `port/arm_stubs.c` | **0** | Arranque, GPIO y link/multiboot. |

En la etapa de 89 pendientes había 358 referencias. El enlace final
`make -C port exe` termina con **cero símbolos sin definir**.
