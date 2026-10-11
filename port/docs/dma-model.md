# DMA del host (T13)

Inventario en upstream parcheado hasta 0027: 14 asignaciones C directas a
REG_DMA, todas en m4a.c y excluidas por sus bloques `#ifndef PORT_PC`.
Las transferencias generales usan DmaSet y macros derivadas, ya redirigidas
desde 0006. DmaStop escribía mediante un puntero local: 0028 observa esa
operación inmediatamente. crt0/m4a_1 ARM no se ejecutan en host.

Write16/Write32 ofrecen un acceso observable por dirección para otras
escrituras futuras; Write32 ordena las dos mitades. Enable 0→1 carga estado
interno; deshabilitar desarma. PortDma_Set es la operación nativa de nueva
transferencia, con rearme explícito. CNT_L se limita a 14 bits en 0–2 y 16
en 3, con conteo cero como máximo. SAD/DAD programados no se incrementan;
la copia usa punteros internos. Repeat vuelve a cargar conteo y DAD cuando
corresponde. IRQ nace después de completar la copia; el despachador aplica
IE/IME. DMA0 precede a DMA1–3 en un evento compartido.

Se aplica alineación de 16/32 bits. Máscaras de direcciones GBA se aplican
solo por debajo de 0x10000000: el port también pasa punteros nativos de
heap/imagen/stack y no puede truncarlos a 27 bits. Esto es un contrato host,
no una reproducción de todas las restricciones del bus GBA. Source mode 3
se rechaza con diagnóstico y canal detenido. No se simulan ciclos de bloqueo
de CPU por transferencia, acceso SRAM ni circuitos externos DREQ.

NOW copia al armar. VBlank recibe un trigger por frame; HBlank solo durante
líneas visibles. FIFO/special y video capture no tienen triggers host: no
deben usarse como copia general. Emerald sustituye su SoundMain/VSync y
FIFO de m4a por el mezclador PCM/PSG y SDL; esas 14 escrituras están excluidas,
sin inventar requests FIFO que dupliquen la salida de audio. Capture/DREQ
no son consumidores identificados del recorrido normal; quedan sin soporte.

`dma_test`: copia/llenado 16/32, inc/dec/fijo, destino reload, repeat,
stop/rearme con valor idéntico, NOW/VBlank/HBlank, máscaras/conteo cero en
los cuatro canales, registros estables, IRQ y prioridad de canales. T11
prueba el calendario que limita los triggers a las fases correspondientes.
Referencia de comportamiento: [GBATEK DMA](https://rust-console.github.io/gbatek-gbaonly/).

Revisión: las máscaras GBA también se aplican al destino al recargar DAD
en repeat. La prueba usa el alias 0x0c000020 en DMA0 y comprueba dos HBlank
sobre 0x04000020, sin escribir el alias. El comportamiento previo fallaba
en el segundo evento (`build/t13-review-before.log`); el corregido pasa.
Las escrituras DMA a BG2/BG3 X/Y notifican al PPU, incluso con valor igual.
