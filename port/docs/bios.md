# BIOS host para el primer ejecutable i686

`port/bios.c` define los **14 nombres BIOS** que faltaban en el enlace de prueba y tres entradas adicionales (`DivArm`, `IntrWait`, `Halt`). No usa ni distribuye código de la BIOS GBA. Se compila con GCC i686 MINGW32; las declaraciones y tipos vienen de los headers del checkout upstream ignorado.

| Funciones | Estado en este hito |
| --- | --- |
| `CpuSet`, `CpuFastSet` | Copia/llenado de unidades de 16 o 32 bits según flags y conteo GBA. |
| `LZ77UnCompWram`, `LZ77UnCompVram` | Descompresión LZ77 tipo `0x10` con referencias solapadas. |
| `RLUnCompWram`, `RLUnCompVram` | Descompresión RLE tipo `0x30`. |
| `Div`, `DivArm`, `Sqrt`, `ArcTan2` | Cálculo host; división por cero devuelve 0 y registra diagnóstico. `DivArm` invierte el orden de argumentos. |
| `BgAffineSet`, `ObjAffineSet` | Matrices afines en punto fijo 8.8 a partir de escala y ángulo. |
| `VBlankIntrWait`, `IntrWait`, `Halt` | Pasan a `PortHost_RunFrame`: procesan eventos SDL, actualizan `REG_KEYINPUT`, despachan VBlank y esperan **59,7275 Hz**. No renderizan el PPU. `IntrWait` todavía ignora las máscaras de otras IRQ. |
| `RegisterRamReset` | **Stub seguro**: no borra RAM/IO de Windows; la memoria GBA de `VirtualAlloc` nace a cero. Registra un aviso una vez. |
| `SoftReset` | **Stub seguro**: registra la petición y termina el proceso host, sin saltar a la cabecera GBA. |
| `MultiBoot` | **Stub seguro** adicional: devuelve error; el cable/link GBA no existe en PC. |

Las variantes `Vram` escriben los mismos bytes descomprimidos que las variantes `Wram`; no reproducen restricciones eléctricas del bus VRAM. Los decodificadores comprueban el byte de tipo y rechazan una referencia LZ77 hacia antes del comienzo de la salida. No validan el tamaño total de la entrada comprimida porque la API GBA no proporciona ese tamaño; se usarán con los recursos del juego. `RegisterRamReset` y las esperas no equivalen todavía a todas las interrupciones reales de GBA.

Verificación focalizada (MINGW32):

```sh
gcc -std=gnu11 -Wall -Wextra -Werror -DMODERN=0 -DPORT_PC \
  -iquote pokeemerald/include -Iport \
  port/bios.c port/tests/bios_test.c -lm -o build/bios-test-i686.exe
build/bios-test-i686.exe
```

Resultado: código de salida **0**. Cubre copia/llenado, LZ77 con referencia solapada, RLE, cálculo, matrices identidad y despacho de una espera de frame.
