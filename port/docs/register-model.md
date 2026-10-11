# Registros y contrato host — T08

Estado: inventario/contrato revisados; IRQ T09 y esperas T10 implementadas y
verificadas. Base del inventario: upstream con parches hasta 0022. El generador
`python port/tools/audit_registers.py` produce [register-inventory.md](register-inventory.md):
75 nombres dentro de funciones C, con consumidores y escrituras candidatas.
Incluye ramas GBA deshabilitadas en host; no es una traza del ejecutable.

## Consumidores y observabilidad

| Familia / dirección | Ancho usado | Consumidores concretos | Ownership / acción propuesta |
| --- | --- | --- | --- |
| IE 0x04000200, IME 0x04000208 | 16 | main InitIntrHandlers/DoSoftReset; gpu_regs SyncRegIE; IntrEnable en gba/macro.h; link/RFU | Juego escribe; IRQ consulta al despachar en el hilo principal. Sin preempción de instrucciones nativas |
| IF 0x04000202 | 16 | 7 asignaciones en 6 C: agb_flash, ereader_helpers, librfu_intr, librfu_stwi, librfu_sio32id (2), link; crt0.s acknowledge | Pending pertenece a IRQ. Necesita hook explícito para cada acknowledge alcanzable; sondeo de RAM no distingue escritura de estado |
| TM0–3 0x04000100–10E | 16; pares por puntero | main StartTimer1/SeedRngAndSetTrainerId; m4a SoundInit/SampleFreqSet; agb_flash StartFlashTimer; librfu_stwi timerL/timerH; ereader_helpers StartTm3 | Timer posee counter/reload. Writes iguales de recarga necesitan hook; el sondeo actual los pierde. Punteros indirectos requieren lote aparte |
| DMA0–3 0x040000B0–DE | SAD/DAD 32, CNT 32 o mitades 16 | DmaSet/DmaStop en gba/macro.h; dma3_manager; scanline_effect; m4a SoundInit/m4aSoundVSyncOn/Off | PortDma_Set captura solicitudes; escrituras directas no arman sChannels. Hook por canal/registro, incluyendo control repetido; distinguir FIFO de copia ordinaria |
| Vídeo 0x04000000–54 | 16; referencias afines/FIFO DMA 32 | gpu_regs GPU_REG(regOffset), CopyBufferedValueToGpuReg/SetGpuReg; bg; scanline_effect; PPU host | Juego controla configuración. Frame controla bits de estado DISPSTAT y VCOUNT. Capturar configuración por línea; DISPSTAT solo modifica bits escribibles |
| Audio 0x04000060–A6 | 8/16; FIFO 32 | m4a C/asm, port_psg, port_audio | PSG/audio poseen triggers, estado y banco wave. Writes iguales de trigger y cambios de banco necesitan hooks futuros, no solo comparar RAM |
| KEYINPUT/KEYCNT 0x04000130/132 | 16 | main ReadKeys; link/SIO; frame UpdateKeyInput | Host produce KEYINPUT; juego configura KEYCNT. IRQ teclado y condiciones AND/OR son eventos futuros |
| GPIO 0x080000C4/C6/C8 | 16 | siirtc GPIO_PORT_DATA/DIRECTION/READ_ENABLE | Stub RTC ausente actual; T20 reemplaza transacciones por backend de reloj, sin writes a la ROM del archivo |
| Serie 0x04000120–12A, RCNT 134, JOY 140/150–158 | 16/32; agregado 64 | librfu, link, ereader_helpers, libgcnmultiboot | Enlace deshabilitado. Inventariado, sin generar respuestas o IRQ ficticias hasta T31–T33 |
| WAITCNT 0x04000204; POST/HALT | 16; 8 | main AgbMain; agb_flash; BIOS Halt | WAITCNT no representa latencia de CPU x86; documentar aproximación. Halt delega al servicio de eventos, no a código ARM |

### Rutas fuera del conteo de macros REG_*

- `gpu_regs.c:7,45`: GPU_REG calcula dirección por offset. No atribuir sus
  writes únicamente a las pocas macros de vídeo encontradas léxicamente.
- `gba/macro.h`: IntrEnable y DmaSet expanden escrituras no visibles en el
  cuerpo del llamador. DmaSet ya usa PortDma_Set bajo PORT_PC.
- `librfu_stwi.c:57`: timerL/timerH calculados desde timerSelect;
  `librfu_intr.c` queda excluido del exe host. Las funciones RFU restantes
  compilan, pero no prueban soporte de adaptador.
- `src/crt0.s:34–136`: despacho/ack IRQ ARM; no se ejecuta en el host.
  IntrMain_Buffer solo conserva la forma del arranque, no emula opcodes.
- m4a contiene partes ARM excluidas y writes GBA bajo guards; revisar el
  preprocesado antes de parchear una ruta que el exe no usa.

## Contrato IRQ implementado en T09

Interfaz propia en `port/port_irq.h`:

```c
void PortIrq_Reset(void);
void PortIrq_Raise(uint16_t flags);
void PortIrq_Acknowledge(uint16_t flags);
uint16_t PortIrq_Pending(void);
uint16_t PortIrq_Dispatch(void);
uint64_t PortIrq_WakeCounter(void);
```

Decisiones host derivadas del inventario:

1. Un único owner en el hilo del juego. Raise agrega pendientes y publica
   IF. Acknowledge elimina los bits indicados; escribir 0 no elimina nada.
   Ningún sondeo interpreta un cambio de IF como una solicitud de hardware.
2. Dispatch consulta IE/IME, selecciona por orden de la tabla **Emerald**:
   VCount, serial, timer3, HBlank, VBlank, timer0/1/2, DMA0–3, keypad, gamepak.
   Se toma de crt0.s; no se afirma que sea una prioridad fija del hardware.
3. Reconocer la solicitud antes de llamar al consumidor. No reentrar en
   Dispatch desde un callback. Reevaluar máscaras tras cada callback y
   entregar cada fuente como máximo una vez por llamada; una nueva solicitud
   de esa misma fuente queda para el siguiente límite cooperativo.
4. Estado IF, flags BIOS `INTR_CHECK` en 0x03007FF8 y
   `gMain.intrCheck` son distintos. Solo IRQ entregada actualiza flags de
   BIOS; un frame completado no debe fingir una IRQ habilitada. Conservar
   los flags de juego que ya actualizan VBlankIntr/HBlankIntr/VCountIntr.
5. Registrar hooks de IF con parche PORT_PC en lotes de hasta cinco archivos.
   IE/IME pueden seguir como lvalues: no hay otro hilo que interrumpa entre
   writes. Su efecto se observa al siguiente Dispatch explícito, no al
   ejecutar cada instrucción x86. No cambiar todas las macros de MMIO a ciegas.
6. Reset vacía pending, flags BIOS y guard de reentrada; módulos de timer/DMA
   resetean su propio estado. No crear callbacks concurrentes desde SDL.

WakeCounter permite a Halt observar una solicitud habilitada que ya fue
reconocida dentro del servicio de frame: aumenta al generar eventos con IE
activo, independiente de IME. Se compara con una captura inicial; no consume
pending ni flags BIOS. Reset reinicia el contador. Prueba de máscara IME=0
en irq_test; la API no representa tiempo ni frames transcurridos.

Los parches 0023/0024 cambian las siete asignaciones C a REG_IF_ACK,
definida como PortIrq_Acknowledge en PORT_PC y la asignación original en GBA.
El despacho reemplaza la parte IRQ de crt0 ARM en host, no sus opcodes.
La pantalla inicia con DISPCNT forced blank en Port_InitGbaMemory, para
que SetGpuReg aplique DISPSTAT antes de depender del primer VBlank.

## Eventos, anchos y orden

Contrato de writes futuros: Write16(address,value) valida offset/alineación;
Write32 divide en low16 y high16, en ese orden, para pares timer/DMA. Una
recarga igual cuenta como write. La mitad control de DMA dispara después
de establecer dirección/count; lecturas siguen viendo el registro publicado.
No mezclar escrituras de estado del backend con writes solicitados por juego.
Los FIFO y bancos de sonido necesitan un contrato propio antes de T21–T23.

Frame genera estado de línea, solicitudes y avance de dispositivos;
el dispatcher entrega al final de cada fase segura. T09 cubre IRQ y eventos
visibles actuales; T11 cambiará el calendario a 228 líneas con tests de orden.
DMA precede a la entrega IRQ de esa fase; una IRQ por transferencia nace solo
después de completarla. Timers se avanzarán por el mismo reloj emulado,
sin derivar eventos independientes de la frecuencia de callback SDL.

Bootstrap detectado antes de T09: RegisterRamReset es no-op. Sin forced
blank inicial, SetGpuReg puede diferir DISPSTAT mientras aún no llega
VBlank. T09 inicializa DISPCNT=0x0080 y lo prueba en la suite de memoria
y arranque del juego, sin mantener VBlank incondicional. El reset por
flags en mitad de ejecución sigue pendiente en T19.

## Esperas T10 y evidencia de hardware

IF reconoce bits escribiendo 1. IE/IME controlan entrega. IntrWait fuerza
IME=1, espera sus flags BIOS, descarta previos cuando se solicita y consume
los coincidentes al volver. VBlankIntrWait equivale a esperar un VBlank
nuevo. Halt despierta ante IE&IF aunque IME esté apagado. Referencia:
[GBATEK de Martin Korth, espejo GBA, IRQ y BIOS](https://rust-console.github.io/gbatek-gbaonly/).

Implementación host propuesta: las esperas sirven SDL/frames para poder
cerrar la ventana, pero solo retornan según su condición. Un evento diferente
no satisface una máscara. IE apagado puede mantener una espera: no arreglarla
activando IRQ de manera global. El timeout del harness debe conservar traza.

## Matriz de pruebas requerida

- Pendiente con IME=0; habilitar después entrega una vez. IE filtra fuentes.
- Ack parcial/0/valor repetido, sin borrar otras fuentes pendientes.
- Prioridad de Emerald; cambio de IE/IME dentro del callback y solicitud nueva.
- Callback pide Dispatch: sin reentrada; mismo IRQ regenerado queda pendiente.
- Bootstrap y VBlank enmascarado: no consumer ni flag BIOS ficticio.
- IntrWait discard=0/1, evento diferente, consumo parcial; Halt con IME=0.
- Cierre SDL durante una espera sin objetivo disponible; salida limpia.
- Calendario completo y DMA/timer IRQ se añaden en T11–T13.

Verificación T09: 14 suites host PASS, incluidas IRQ/frame/memoria; combate
posterior a los hooks gana en 33.365 y termina limpio en 37.000. GBA compare
OK en `build/irq-ack-rfu-gba-compare.log`; checkout aislado con 24 parches
recompilado/enlazado y árbol idéntico
`0db24077d24c9c51701f36e575d466f280bdb3af` (`build/irq-clean-build.log`).
T10: `build/irq-wait-build.log`, 14 suites PASS; normal sale de casa sin
combate (`normal-game-regression/gdb.log`); fixture de batalla gana y sale
en 37.000 (`wild-battle-regression/gdb.log`); recarga/recuperación de save
PASS. El calendario completo y dispositivos T11–T13 siguen pendientes.

Actualización T11–T13 (2026-10-11): ya están implementados el calendario de
228 líneas, IRQ de timers/DMA y writes observables de timer/stop DMA.
Los parches 0025–0028 y las suites frame/timer/dma cubren los consumidores
identificados; 0029 añade observación de referencias afines. Contratos y
límites actuales: video-calendar.md y dma-model.md. Los párrafos T09/T10
anteriores conservan el estado y los logs históricos de esos incrementos.
