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
| `RegisterRamReset` | Reset por flags de RAM/registros/modelos GBA; preserva pila/heap/globals nativos, ROM y los últimos 0x200 bytes de IWRAM. Detalles y pruebas en T19 abajo. |
| `SoftReset` | En el normal relanza mediante CreateProcessW y termina con cleanup; fallo devuelve código 1 con error. Diagnóstico termina su recorrido. Detalles en `reset.md`. |
| `MultiBoot` | **Stub seguro** adicional: devuelve error; el cable/link GBA no existe en PC. |

Las variantes `Vram` escriben los mismos bytes descomprimidos que las variantes `Wram`; no reproducen restricciones eléctricas del bus VRAM. Los decodificadores comprueban el byte de tipo y rechazan una referencia LZ77 hacia antes del comienzo de la salida. No validan el tamaño total de la entrada comprimida porque la API GBA no proporciona ese tamaño; se usarán con los recursos del juego. `RegisterRamReset` actúa sobre las regiones GBA seleccionadas; las esperas usan un modelo cooperativo sin ejecutar instrucciones ARM ni prometer precisión de CPU.

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

## T18: copia, cálculo y matrices

Inventario reproducible: [bios-inventory.md](bios-inventory.md), 28 entradas
revisadas, 15 con consumidores C detectados. Es léxico: no prueba que RFU o
e-Reader sean alcanzables en el host ni sustituye la revisión de ensamblador.
Los SWI no usados no reciben stubs que falsifiquen éxito.

Cambios comprobados:

- `CpuFastSet` redondea hacia arriba a bloques de ocho palabras; conteo cero
  no copia. Copias de 32 bits alinean ambas direcciones hacia abajo.
  CpuSet de 16 bits mantiene el contrato de direcciones alineadas; no emula
  lecturas ARM desalineadas ni el guard de región BIOS para punteros host.
- `ArcTan2` usa un evaluador entero propio de la aproximación fija,
  conservando cuadrantes y truncamiento. Trece vectores numéricos se
  evaluaron también compilando la referencia abierta de mGBA en
  `build/bios-reference/`; los CSV coinciden con los asserts públicos.
- `Sqrt`: 131.070 comprobaciones de cuadrados y su valor anterior, además
  de cero y UINT32_MAX. Div prueba signos y INT_MIN/-1. Div por cero sigue
  devolviendo cero con aviso: es una política host, no exactitud BIOS.
- Matrices: solo byte alto del ángulo, muestras matemáticas 1.14 generadas
  con sin (sin copiar una tabla BIOS), desplazamiento aritmético de los
  productos y wrap de 16 bits. Traslación con wrap definido de 32 bits.
  Fixtures de 45° (181,-182,181,181), 90°, escalas negativas, extremos,
  stride 2/8, canarios y conteo cero. Offset OBJ cero conserva escrituras
  solapadas; offset negativo se rechaza por seguridad host.
- Descompresión: fixtures propios LZ solapado, distancia inválida, RLE
  literal/comprimido y canarios. Un token que excede la longitud declarada
  se limita a ella; no reproduce sobrescrituras de entradas malformadas
  de hardware. VRAM usa bytes host, sin restricciones de bus ni bug de
  distancia 1. No hay comprobación de entrada truncada sin longitud fuente.

Fuentes: [GBATEK, contrato BIOS](https://rust-console.github.io/gbatek-gbaonly/#bios-functions),
[mGBA, HLE abierto](https://github.com/mgba-emu/mgba/blob/master/src/gba/bios.c),
[referencia de comportamiento CpuFastSet](https://retrointernals.github.io/gba-bios-reference/swi_0C_CpuFastSet/),
[referencia de matrices OBJ](https://retrointernals.github.io/gba-bios-reference/swi_0F_ObjAffineSet/).
Se compararon contratos y resultados públicos, no una BIOS Nintendo. Las
matrices se contrastaron con las fórmulas documentadas; no se ejecutó un
test físico en una GBA ni se declara exactitud universal bit a bit de todos
los ángulos. Los límites de precisión de tiempo están en video-calendar.md.

Evidencia local: `build/t18-copy-before.log`, `t18-math-before.log` y
`t18-affine-before.log` reproducen los tres fallos previos. Sus respectivos
logs `*-build.log` y `build/t18-final-build.log` verifican las correcciones;
la suite completa contenía 17 ejecutables. T19 se verificó después, abajo.

## T19 — RegisterRamReset (2026-10-11)

Implementado en `port_ram_reset.c`: flags 01 EWRAM, 02 IWRAM excepto sus
últimos 0x200 bytes, 04 paletas, 08 VRAM y 10 OAM. Cada región se pone a
cero. Siempre se fuerza blank (DISPCNT=0x80) y se limpia SIODATA32 bajo.
20 restablece serie/joybus y RCNT=0x8000; 40 restablece sonido/PSG y
SOUNDBIAS=0x200; 80 vídeo, DMA, timers e IRQ, con matrices identidad.
KEYINPUT se conserva como entrada de solo lectura. La palabra BIOS de
espera en IWRAM excluida se conserva aunque se reinicie el modelo IRQ.

Los globals C, heap y pila nativos no están en EWRAM: este servicio no los
borra. Los inicializadores normales del juego y SoftReset (proceso nuevo)
se encargan de ellos. No se escribe la ROM. La prueba ram_reset compara
cada byte de regiones solicitadas/no solicitadas, canarios host/ROM,
flags individuales/0/FF y dispositivos armados antes del reset.
18 suites PASS y reset real teclado/juego/error de CreateProcess PASS:
`build/t19-build.log`, `build/t19-reset-game.log`. No se simula ejecución
ARM ni reinicialización de accesorios reales.
