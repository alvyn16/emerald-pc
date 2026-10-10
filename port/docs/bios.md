# BIOS host para el primer ejecutable i686

`port/bios.c` define los **14 nombres BIOS** que faltaban en el enlace de prueba y tres entradas adicionales (`DivArm`, `IntrWait`, `Halt`). No usa ni distribuye código de la BIOS GBA. Se compila con GCC i686 MINGW32; las declaraciones y tipos vienen de los headers del checkout upstream ignorado.

| Funciones | Estado en este hito |
| --- | --- |
| `CpuSet`, `CpuFastSet` | Copia/llenado de unidades de 16 o 32 bits según flags y conteo GBA. |
| `LZ77UnCompWram`, `LZ77UnCompVram` | Descompresión LZ77 tipo `0x10` con referencias solapadas. |
| `RLUnCompWram`, `RLUnCompVram` | Descompresión RLE tipo `0x30`. |
| `Div`, `DivArm`, `Sqrt`, `ArcTan2` | Cálculo host; división por cero devuelve 0 y registra diagnóstico. `DivArm` invierte el orden de argumentos. |
| `BgAffineSet`, `ObjAffineSet` | Matrices afines en punto fijo 8.8 a partir de escala y ángulo. |
| `VBlankIntrWait`, `IntrWait`, `Halt` | Sirven eventos/frames hasta cumplir la condición IRQ. IntrWait fuerza IME=1, descarta opcionalmente flags previos y consume solo los coincidentes. VBlankIntrWait solicita un VBlank nuevo. Halt espera IE&IF o una nueva solicitud habilitada, sin requerir IME. |
| `RegisterRamReset` | Stub de reset por flags pendiente de T19. No limpia RAM en mitad de ejecución. El arranque host inicializa memoria, teclas liberadas y DISPCNT forced blank. |
| `SoftReset` | En el normal relanza mediante CreateProcessW y termina con cleanup; fallo devuelve código 1 con error. Diagnóstico termina su recorrido. Detalles en `reset.md`. |
| `MultiBoot` | **Stub seguro** adicional: devuelve error; el cable/link GBA no existe en PC. |

Las variantes `Vram` escriben los mismos bytes descomprimidos que las variantes `Wram`; no reproducen restricciones eléctricas del bus VRAM. Los decodificadores comprueban el byte de tipo y rechazan una referencia LZ77 hacia antes del comienzo de la salida. No validan el tamaño total de la entrada comprimida porque la API GBA no proporciona ese tamaño; se usarán con los recursos del juego. `RegisterRamReset` sigue pendiente; las esperas usan un modelo cooperativo sin ejecutar instrucciones ARM ni prometer precisión de CPU.

Verificación focalizada (MINGW32):

```sh
make -C port ../build/tests/bios.exe ../build/tests/irq.exe
build/tests/bios.exe
build/tests/irq.exe
```

Resultado: código de salida **0**. Cubre copia/llenado, LZ77/RLE, rechazo de
cabecera malformada, cálculo y matrices identidad. Los fixtures IRQ/BIOS
añaden espera diferida, discard 0/1, consumo parcial, IRQ distinta, fuente
enmascarada, IME, pending/ack, prioridad y reentrada.

El cierre durante una espera sin objetivo se prueba con un pump sintético
que sale mediante longjmp; la suite frame prueba SDL_QUIT en el pump real.
Halt detecta solicitudes ya reconocidas dentro del frame mediante
PortIrq_WakeCounter; no acepta cualquier frame como motivo de retorno.
Declaraciones adicionales propias en `port_bios.h`.
