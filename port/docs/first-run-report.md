# Primera ejecución de `emerald-pc.exe` i686

## Hito 2: primer acceso fuera del mapa

Entorno: MSYS2 MINGW32, GCC 16.2.0-4, SDL2 2.32.10-1, GDB 18.1-3.
`make -C port exe` termina con código 0 y genera `build/emerald-pc.exe`
(ignorado por Git). El proceso reserva EWRAM, IWRAM, IO, paletas, VRAM y OAM
en las direcciones pedidas, carga SDL2 después de esas reservas, abre una
ventana negra de 960×640 con coordenadas lógicas 240×160 y entra en `AgbMain`.

Al enlazar SDL2 como dependencia de carga, Windows reservaba un bloque que
cubría `0x02000000` o `0x03000000`; `VirtualAlloc` falló con error 487.
La carga posterior con `LoadLibraryA` y la imagen PE basada en `0x10000000`
dejaron libres las seis regiones. La prueba de memoria independiente también
escribió y leyó EWRAM e inicializó `REG_KEYINPUT` a `0x03FF`.

El primer bloqueo fue `AgbMain → InitRFU → rfu_REQ_stopMode →
AgbRFU_SoftReset`: GDB encontró el hilo principal en el bucle que lee
`REG_TMCNT_L`. Ese timer es un registro de IO mapeado como RAM ordinaria;
su contador nunca avanza. El parche `0002` omite la inicialización RFU solo
en `PORT_PC` y permite continuar.

La siguiente ejecución recibió **SIGSEGV** inmediatamente después de iniciar:

```
#0 EnableGpioPortRead
#1 SiiRtcUnprotect
#2 RtcInit
#3 AgbMain
eax = 0x080000C8
```

`EnableGpioPortRead` escribe `GPIO_PORT_READ_ENABLE` en `0x080000C8`.
Las seis regiones de memoria exigidas para este hito terminan en OAM;
la región de ROM/RTC `0x08000000` no estaba mapeada. Ese fue el primer fallo
del hito 2. La ROM legal del usuario permaneció intacta en `roms/`; ninguna ROM,
asset ni dato extraído se incorporó al ejecutable o al repo. El PPU y el
audio no están implementados; el renderer permanece negro y m4a usa stubs
silenciosos. El diagnóstico no presupone que mapear RTC baste para ejecutar
el juego completo: flash/guardado e interrupciones siguen sin emulación.

## Hito 3: ROM cargada y RTC ausente

`port/gba_memory.c` reserva **32 MiB** con `VirtualAlloc` en
`0x08000000–0x09FFFFFF`. Busca exactamente un `.gba` en `roms/` junto a la
raíz del proyecto (deducida de `build/emerald-pc.exe`), abre ese archivo solo
para lectura y copia sus **16.777.216 bytes** a la reserva. El resto se llena
con `0xFF`. El archivo original no se escribe ni se copia al repositorio.
Solo la copia en memoria deja a cero los halfwords GPIO `0x080000C4`,
`0x080000C6` y `0x080000C8`.
El SHA-256 del archivo original fue idéntico antes y después de ejecutar el
diagnóstico. `make compare` del build GBA original volvió a indicar
`pokeemerald.gba: OK` con ARM Binutils 2.43.1.

El parche `0003-Report-absent-RTC-on-host.patch` hace que `SiiRtcProbe`
devuelva 0 bajo `PORT_PC`; en GBA queda intacto. GDB paró al entrar en
`CheckForFlashMemory`, después de `RtcInit`, y midió
`RtcGetErrorStatus() = 1`, igual a `RTC_INIT_ERROR`: el juego detecta RTC
ausente sin fallar ni afirmar un reloj inexistente.

La ejecución siguiente recibe **SIGSEGV**:

```
#0 ReadFlashId
#1 IdentifyFlash
#2 CheckForFlashMemory
#3 AgbMain
eax = 0x0E005555
```

`ReadFlashId` escribe el comando `0xAA` en `FLASH_BASE + 0x5555`, es decir,
`0x0E005555`. La región flash/guardado `0x0E000000` no está mapeada en este
hito; el acceso produce la excepción. El mismo procedimiento prepara una
rutina de lectura copiada a RAM y espera ejecutarla con semántica ARM Thumb,
por lo que reservar flash sin adaptar esa rutina tampoco bastaría para
continuar. No se implementó flash, guardado, PPU ni audio en esta sesión.

## Hito 4: flash de 128 KiB y siguiente espera

El parche `0004-Route-host-flash-operations-to-save-backend.patch` hace que,
solo bajo `PORT_PC`, `IdentifyFlash` seleccione una flash válida de 128 KiB
con 32 sectores de 4 KiB. Lectura y verificación dejan de copiar y ejecutar
rutinas Thumb desde la pila. Las operaciones de escritura y borrado apuntan
al buffer de `port/host_flash.c`, que está mapeado al archivo
`saves/emerald-pc.sav` (ignorado por Git). El archivo nuevo se llena con
`0xFF`; uno existente debe tener exactamente 131.072 bytes. El backend
preserva la regla de flash de programar bits de 1 a 0 y persiste los cambios.
No se reserva ni se usa `0x0E000000` para esas operaciones host.

La prueba independiente `port/tests/host_flash_test.c` usó un save temporal
bajo `build/`: borrado, programación de byte/sector, lectura, verificación,
rechazo de sector inválido y persistencia tras cerrar y reabrir dieron **OK**.
GDB detuvo la ejecución después de `CheckForFlashMemory` y midió
`gFlashMemoryPresent = 1` y `gFlash->romSize = 131072`. El build original
continuó dando `make compare` → `pokeemerald.gba: OK` con ARM Binutils 2.43.1.

La ejecución ya no cae en `ReadFlashId`; el **siguiente bloqueo** es:

```
#0 WaitForVBlank
#1 AgbMain
#2 main
```

`WaitForVBlank` limpia `INTR_FLAG_VBLANK` de `gMain.intrCheck` y gira hasta
que una IRQ vuelva a poner ese bit. El host todavía no genera interrupciones
VBlank ni ejecuta el despachador ARM `IntrMain`: la memoria IO y la tabla de
interrupciones son solo reservas/estados iniciales. Por eso el bit nunca cambia
y el hilo principal queda en ese bucle, sin procesar eventos SDL. Emular esa
IRQ queda para un hito posterior; no se cambió video, PPU ni audio aquí.

## Hito 5: VBlank cooperativo y siguiente límite visible

El parche `0005-Use-cooperative-host-frame-in-WaitForVBlank.patch` cambia
`WaitForVBlank` solo bajo `PORT_PC`: limpia el bit y llama a
`PortHost_RunFrame` en lugar de girar esperando una IRQ física. La función
host procesa eventos SDL, termina limpiamente al recibir `SDL_QUIT` o cierre
de ventana, traduce el teclado a `REG_KEYINPUT` (activo en bajo), espera con
el contador de alta resolución de SDL a **59,7275 FPS**, ejecuta
`gIntrTable[4]` (la entrada VBlank real de `gIntrTableTemplate`) y asegura
`INTR_FLAG_VBLANK` en `gMain.intrCheck`. `VBlankIntrWait`, `IntrWait` y `Halt`
usan la misma ruta. Teclas: flechas = cruceta, Z/X = A/B, Enter/Retroceso =
Start/Select y A/S = L/R. `IntrWait` no emula todavía otras máscaras de IRQ.

La prueba host `frame_test.c` verificó la conversión de Z y flecha arriba,
la liberación de las teclas, 1.002 llamadas al callback VBlank, el ritmo
simulado de 1.000 frames y la salida ante `SDL_QUIT` sin despachar otro frame.
GDB alcanzó la llamada 601 a
`PortHost_RunFrame` después de **600 VBlanks**: `gMain.vblankCounter1 = 600`,
`gMain.vblankCounter2 = 600` y `gMain.callback2` no era nulo. No hubo
excepción ni bloqueo nuevo en ese intervalo. `make compare` del build GBA
original dio `pokeemerald.gba: OK` con ARM Binutils 2.43.1. El parche `0005`
aplicado sobre el clon limpio con los cuatro parches anteriores produjo el
mismo árbol Git que el checkout de trabajo.

El **siguiente fallo observable** es visual: la ventana sigue completamente
negra porque `PortHost_RunFrame` solo limpia y presenta negro. El juego
avanza y escribe registros, paletas y VRAM, pero aún no hay emulación del PPU
que convierta ese estado en píxeles. No se implementó PPU ni audio aquí.

## Hito 6: DMA inmediato, PPU de modo 0 y siguiente excepción

Antes de este hito, `DmaSet` solo escribía los registros `REG_DMA0..3` en
memoria mapeada: no había copia ni relleno. El parche
`0006-Route-host-DMA-macros-to-immediate-transfer-backend.patch` desvía la
macro común a `port/port_dma.c` únicamente bajo `PORT_PC`. El backend copia
unidades de 16/32 bits, admite origen y destino con incremento, decremento
o dirección fija, usa 16.384/65.536 unidades cuando el contador vale cero
(DMA0–2/DMA3) y limpia `DMA_ENABLE` al completar. Conserva el control de
transferencias programadas para HBlank, VBlank o modo especial, pero aún no
las dispara. Las escrituras directas de DMA en `m4a.c` pertenecen al audio
ARM excluido de este ejecutable. `dma_test.c` confirmó copia, relleno,
decremento, destino fijo y ausencia de disparo HBlank.

`port/port_ppu.c` genera un buffer ARGB8888 de 240×160. En modo 0 dibuja
fondos de texto de 4 y 8 bpp, bancos de paleta, scroll, flips de tile,
mapas 256×256/512×256/256×512/512×512 y prioridades. También dibuja
sprites regulares de 4 y 8 bpp desde OAM, con tamaños, flips, prioridad y
disposición de tiles 1D/2D. El color 0 de cada tile es transparente; el
backdrop usa la entrada 0 de la paleta. SDL recibe el buffer mediante una
textura de 240×160 y lo escala en la ventana. El ciclo host pone
`REG_VCOUNT = 160` y `DISPSTAT_VBLANK` durante el callback VBlank y vuelve a
línea 0 al terminar. No simula cada scanline ni genera IRQ VCount/HBlank.

Las pruebas `ppu_test.c` y `frame_test.c` pasaron con GCC i686 MINGW32.
GDB capturó frames reales del proceso usando la ROM local ignorada:

- Frame 180: fondo selvático verde, 19 colores.
- Frame 1.200: paisaje de montañas y árboles, 15 colores.
- Frame 1.800: Rayquaza, el protagonista en bicicleta y otros Pokémon sobre
  el paisaje, 55 colores. Son visibles tanto fondos como sprites.

Esas capturas están en `build/`, ignorado por Git; no se distribuyen. El
parche `0006` aplicado sobre el clon limpio con los parches anteriores dio
el mismo árbol Git que el checkout de trabajo. `make compare` del build GBA
original volvió a dar **`pokeemerald.gba: OK`** con ARM Binutils 2.43.1.

El primer límite visual posterior aparece al comenzar la siguiente escena:
`REG_DISPCNT = 0x1441` selecciona **modo 1**, cuyo fondo afín BG2 está fuera
de este hito. El renderizador deja solo el backdrop blanco. El siguiente
fallo de ejecución ocurre en el frame **2.235**, antes de llegar al 2.400:

```
SIGFPE: Task_Scene3_SpinPokeball
        RunTasks → MainCB2_Intro → CallCallbacks → AgbMain
```

`Task_Scene3_Load` pone `tZoomDiv = 0` y `tZoomDivSpeed = 0`. La primera
llamada a `Task_Scene3_SpinPokeball` aún deja el divisor en cero y evalúa
`SAFE_DIV(0x10000, tZoomDiv)`. En este build host `UBFIX` no está definido,
por lo que `SAFE_DIV` se expande a una división directa; x86 produce
`SIGFPE`. Este fallo pertenece a la compatibilidad de la lógica de la
introducción, separado del PPU. No se modificó esa lógica ni se implementó
el modo afín, las ventanas, la mezcla o el audio en este hito.

## Hito 7: división segura y escenas afines

El parche `0007-Use-safe-division-for-host-intro-code.patch` hace que
`SAFE_DIV` compruebe el divisor cuando se compila con `PORT_PC`, igual que
cuando se activa `UBFIX`. La rama GBA conserva el comportamiento anterior.
El host dejó atrás el antiguo `SIGFPE` del frame 2.235.

El PPU de `port/port_ppu.c` ahora renderiza BG2 en modo 1 y BG2/BG3 en
modo 2. Usa las matrices con signo `PA/PB/PC/PD`, las referencias de 28 bits
`BG2X/Y` y `BG3X/Y`, mapas afines de 128, 256, 512 y 1.024 píxeles y el
bit de wraparound de `BGxCNT`. Mantiene la prioridad entre fondos y objetos.
Los sprites afines toman sus cuatro parámetros de la matriz elegida en OAM;
admiten rotación, escala y doble tamaño. Las pruebas host con memoria
sintética verificaron matriz identidad y rotada, desplazamiento, referencia
negativa, wrap, mapa de 1.024 píxeles, BG3 en modo 2, sprite afín, doble
tamaño y rotación. `make -C port exe` y esa prueba pasaron en MINGW32.

Las capturas reales de la intro, guardadas solo en `build/` (ignorado por
Git), muestran:

- `hito7-frame-2400.png`: escena rosa con la Poké Ball ampliada y elementos
  afines; 16 colores.
- `hito7-frame-3000.png`: escena oscura con contornos amarillos; 4 colores.
- `hito7-frame-4200.png`: regreso al paisaje selvático; 19 colores.

GDB alcanzó los frames 2.400, 3.000 y 4.200 sin nueva excepción. El
**siguiente fallo observado es visual**: en el frame 2.400,
`REG_DISPCNT = 0x3641` tiene `WIN0_ON` activo, pero el renderizador todavía
ignora las ventanas, así que dibuja píxeles fuera de la máscara prevista.
La mezcla de color también sigue sin emular; las escenas con fundidos no
reproducen aún su aspecto GBA. No se encontró otro fallo de ejecución en los
primeros 4.200 frames sin input. Ventanas, mezcla, audio y DMA HBlank quedan
fuera de este hito.

El parche `0007` aplicado al clon de verificación después de los seis
anteriores produjo el mismo árbol Git que el checkout de trabajo. El build
GBA original dio **`pokeemerald.gba: OK`** con ARM Binutils 2.43.1.

## Hito 8a: ventanas WIN0 y WIN1

El PPU host usa `WIN0H/V` y `WIN1H/V` para delimitar rectángulos. El borde
izquierdo/superior es inclusivo y el derecho/inferior, exclusivo. Cuando el
segundo borde es menor que el primero, la ventana continúa desde el borde de
la pantalla hasta el origen; dos bordes iguales producen una ventana vacía.
`DISPCNT` activa cada ventana. `WININ` selecciona las capas visibles en cada
una, con WIN0 por encima de WIN1; `WINOUT` selecciona las capas fuera de
ambas. Las máscaras cubren BG0–BG3 y OBJ, también sobre fondos afines.
La ventana de objetos (`OBJWIN_ON` y el byte alto de `WINOUT`) queda como
**TODO**: aún no se calculan sus píxeles desde OAM. El bit de efectos de color
de `WININ`/`WINOUT` se aplicará cuando exista mezcla.

La prueba host `ppu_test.c` pasó con GCC i686 MINGW32. Cubre solapamiento y
precedencia, bordes exclusivos, recorrido horizontal y vertical por el borde
de la pantalla, ventana vacía, ventanas desactivadas, máscaras positivas de
`WINOUT`, sprites y BG2 afín. `make -C port exe` enlazó y el build GBA
original conservó **`pokeemerald.gba: OK`** con ARM Binutils 2.43.1.

GDB alcanzó los frames 2.400 y 3.000 sin excepción. Las capturas ampliadas
`build/hito8a-frame-2400.png` y `build/hito8a-frame-3000.png` permanecen en
`build/`, ignorado por Git. En el frame 2.400 se ve la escena rosa de la
Poké Ball recortada a una franja horizontal: aparecen bandas negras arriba y
abajo que no estaban en la captura del hito 7. En el frame 3.000 se ve una
escena oscura con contornos amarillos, también recortada por las ventanas.

El siguiente límite observado es **visual**, no una excepción. En el frame
2.665, al entrar en `PortPpu_Render` después de `Task_Scene3_LoadClouds1`, GDB
midió `REG_BLDCNT = 0x0087`, `REG_BLDY = 0x001F` y
`REG_DISPCNT = 0x3740`: el juego pide aclarado de BG0–BG2, pero el
renderizador todavía ignora la mezcla. No se implementaron mezcla ni audio
en este hito.

## Hito 8b: mezcla de color

`port/port_ppu.c` conserva por píxel el color GBA de 15 bits y la identidad de
la capa superior y la inmediatamente inferior. Solo el sprite visible más
alto participa en la mezcla; otro sprite oculto no sustituye al fondo como
segundo objetivo. `BLDCNT` selecciona BG0–BG3, OBJ y backdrop como objetivos
primero o segundo. El PPU aplica alfa, aclarado y oscurecimiento; limita
EVA/EVB y EVY a 16, y satura cada canal de alfa a 31. Un OBJ en modo OAM 1
fuerza alfa cuando la segunda capa es objetivo válido, incluso si `BLDCNT`
no selecciona alfa ni OBJ como primer objetivo. El bit de efectos de
`WININ`/`WINOUT` permite o bloquea estos efectos en cada región. La ventana
de objetos sigue como **TODO**; no se implementaron mosaico ni audio.

La prueba host `ppu_test.c` pasó con GCC i686 MINGW32. Incluye alfa entre
BG0/BG1, BG0/OBJ, OBJ/BG0, BG0/BG2 y BG0/backdrop; backdrop y BG3 como
primer objetivo; coeficientes 0, 8, 16 y 31; saturación a 31; aclarado y
oscurecimiento; bits de efectos de WIN0 y WIN1; sprite semitransparente y
sprites superpuestos. `make -C port exe` enlazó. El build GBA original dio
**`pokeemerald.gba: OK`** con ARM Binutils 2.43.1.

GDB capturó el frame **2.665** en `build/hito8b-frame-2665.png`, ignorado
por Git junto con el volcado `.raw`. Antes de renderizar midió
`REG_BLDCNT = 0x0087`, `REG_BLDALPHA = 0x1F1F`, `REG_BLDY = 31` y
`REG_DISPCNT = 0x3740`. La imagen muestra una franja blanca entre dos bandas
negras: el aclarado satura los fondos visibles de esa franja, mientras las
ventanas dejan fuera el resto. No hay sprites visibles en esa captura.

No se observó otra excepción hasta el frame **4.200**; allí GDB midió
`DISPCNT = 0x1F40`, `MOSAIC = 0` y `BLDCNT = 0`. Por tanto, no hay un nuevo
fallo de ejecución medido en ese tramo. El siguiente límite gráfico
identificado en el código del juego es la **ventana de objetos**:
`battle_intro.c` activa `DISPCNT_OBJWIN_ON`, pero el PPU aún no calcula su
máscara desde los sprites OAM ni aplica el byte alto de `WINOUT`. Se verá
cuando se alcance esa escena; no se observó en la captura de la intro.

## Hito 9: guion de entrada y recorrido de partida nueva

Se añadió un ejecutable de diagnóstico i686 con entradas por intervalos de
frames. La sintaxis y las variables de entorno están en
`port/docs/scripted-input.md`. Un guion local en `build/` pulsó A durante la
intro y los menús, eligió partida nueva, completó la pantalla de nombre y
usó RIGHT y DOWN para salir del camión. `EMERALD_PC_FAST=1` permitió repetir
el recorrido bajo GDB sin la espera de 59,7275 FPS. El ejecutable normal no
contiene la entrada programada.

### Fallos encontrados en orden

| Punto | Evidencia de GDB | Causa y corrección PC |
| --- | --- | --- |
| Menú principal | El hilo se quedó en `AgbRFU_SoftReset` desde `Task_MainMenuCheckSaveFile`. | `IsWirelessAdapterConnected` intentaba interrogar hardware RFU inexistente. El parche `0008` devuelve `FALSE` bajo `PORT_PC`. |
| Pantalla de título | `Task_TitleScreenPhase3` veía `gMPlayInfo_BGM.status = 0` y volvía a copyright sin mostrar menú. | El backend de audio silencioso no mantenía estado lógico. Ahora start/stop/fade actualizan `status`, sin generar sonido. |
| Animación de Pokémon | `Task_HandleMonAnimation` produjo `SIGSEGV` al reconstruir `ANIM_SPRITE`: el semipuntero bajo `s16` se extendía con signo (valor observado `0xffffea44`). | `0009` activa para PC la reconstrucción ya existente bajo `MODERN`/`BUGFIX`; no cambia GBA. |
| Salida de nombre, frame ~5.209 | `MainState_Exit` liberó `sNamingScreen` en `RunTasks`; `SpriteCB_Cursor` lo usó después desde `AnimateSprites`. En el VBlank siguiente también quedaba registrado `VBlankCB_NamingScreen`. | `0010` omite el resto del callback host si ya se liberó y desregistra el VBlank antes de liberar. |
| Inicialización de partida, frame ~7.014 | `CB2_NewGame` llegó a `ClearRankingHallRecords`, que pasó el puntero nulo `ZERO` a `CopyTrainerId`; produjo `SIGSEGV`. | `0011` usa bajo PC los cuatro bytes cero de la ruta `UBFIX` existente. |
| Carga del mapa | `DoMapLoadLoop` esperaba que terminara `IsDma3ManagerBusyWithBgCopy`, pero el bucle síncrono nunca dejaba ejecutar el VBlank que procesa la cola DMA3. | `0012` ejecuta `PortHost_RunFrame` entre pasos de carga solo bajo `PORT_PC`. |
| Mapa negro con sprites visibles | En el frame 7.500 GDB mostró tilemaps BG1–BG3 con datos en el heap (`0x1000`, `0x6201`, `0x3014`), pero VRAM `0x0600e800`, `0x0600f000` y `0x0600f800` a cero. `IsTileMapOutsideWram` rechazaba esos punteros host por estar sobre `IWRAM_END`. | `0013` acepta cualquier buffer no nulo bajo `PORT_PC`. El camino GBA mantiene su comprobación de dirección. |

### Resultado del recorrido

GDB confirmó título en el frame 1.002, menú principal en 1.112, presentación
del profesor Birch en 1.203, nueva partida en 7.014 y `CB2_Overworld` en
7.028. Tras la corrección de tilemaps se ve el camión en el frame 7.500 y el
texto de las cajas en 9.000. Con RIGHT y DOWN, el protagonista sale a
**Villa Raíz**: el frame **12.500** muestra el mapa exterior, la madre y el
camión. El recorrido continúa a la casa (14.000) y, con UP, al dormitorio de
la segunda planta (19.000). El guion interactúa con el reloj, elige YES en la
confirmación y deja que termine el diálogo de la madre (20.000). Después del
evento de la televisión en la planta baja (27.000), el personaje camina hasta
la salida. El frame **30.500** lo muestra de nuevo en el mapa exterior, con
control por dirección y `CB2_Overworld` activo. No hubo excepción ni espera
infinita hasta ese frame. El generador `port/tests/gameplay_smoke.py` produjo
las mismas 614 entradas que se usaron en el recorrido medido.

Las capturas ampliadas `build/hito9-frame-1080.png` (título),
`build/hito9-frame-1800.png` (Birch), `build/hito9-frame-4900.png` (nombre),
`build/hito9-frame-7500.png` (camión), `build/hito9-route-12500.png`
(exterior), `build/hito9-route-14000.png` (casa) y
`build/hito9-stairs-19000.png` (dormitorio),
`build/hito9-clock2-19500.png` (confirmación del reloj) y
`build/hito9-world-free-30500.png` (exterior tras el reloj) están en `build/`,
ignorado por Git. También se guardaron allí los guiones y registros GDB para repetir el
diagnóstico. Los parches `0008` a `0013` se aplicaron a un clon limpio junto
con `0001` a `0007`; su árbol Git final coincide exactamente con el checkout
de trabajo (`5fbe81f4033bbac5a2192bede821976b93db982e`).

No se implementó audio ni DMA por HBlank. La ventana de objetos y el mosaico
siguen pendientes de hitos gráficos futuros.
La prueba de entrada pasó con GCC i686 y `-Wall -Wextra -Werror`; ambos
ejecutables enlazaron. La compilación GBA original terminó con
**`pokeemerald.gba: OK`** usando ARM Binutils 2.43.1.

## PC del dormitorio y selección del inicial

La ruta de diagnóstico llegó al PC del dormitorio en el frame 26.321. Al
elegir «Item Storage» → «Deposit Item», GDB encontró el bloqueo en
`CB2_Bag` → `SetupBagMenu` → `LoadBagMenu_Graphics` →
`FreeTempTileDataBuffersIfPossible` → `IsDma3ManagerBusyWithBgCopy`.
`CB2_Bag` ejecutaba un bucle síncrono que impedía el VBlank necesario para
vaciar la cola DMA3. El parche `0014`, solo bajo `PORT_PC`, ejecuta
`PortHost_RunFrame()` entre los pasos de carga de la bolsa. Con el mismo guion,
`CB2_BagMenuRun` empieza en el frame 26.530. Una Poción añadida **solo en la
sesión aislada de GDB** se seleccionó en el frame 26.580: se llamaron
`TryDepositItem` y `AddPCItem`, y `Task_RemoveItemFromBag` se ejecutó en el
frame 26.581. El proceso alcanzó el frame 26.750 y salió normalmente. La ROM
original y el save del usuario no se modificaron en esta prueba.

En la captura del usuario, el círculo blanco de la selección del inicial
estaba desplazado arriba y a la izquierda. `BuildOamBuffer` ya coloca un
sprite afín de doble tamaño en la esquina del cuadro ampliado; el PPU host
restaba otra vez la mitad del tamaño y desplazaba el efecto. Se eliminó esa
segunda resta en `port/port_ppu.c`. La prueba de sprite afín de doble tamaño
comprueba ahora la coordenada OAM real y pasa con GCC i686. No apareció una
nueva excepción en el recorrido hasta el frame 26.750; quedan pendientes
pruebas de otras opciones y objetos del PC.

`make -C port exe` y `make -C port diagnostic-exe` enlazaron. El build GBA
original devolvió **`pokeemerald.gba: OK`** con ARM Binutils 2.43.1. Los
parches `0001` a `0014` se aplicaron a un checkout limpio de la revisión base;
el hash del árbol resultante coincide con el checkout de trabajo:
`ba59c2e86fafcc9c799e24c3dacd30046ad6d97b`.

## Hito 13: pruebas host unificadas

`make -C port test` compila y ejecuta suites con fuentes explícitas y
`-Wall -Wextra -Werror`. El objetivo propaga el primer fallo. Empezó con
8 suites y termina estos hitos con 13; los binarios y archivos temporales
se guardan en `build/`. No necesitan una ROM para ejecutarse.

## Hito 14: temporizadores

`port_timer.c` observa TM0–TM3 y emula prescaler, habilitación, recarga,
desbordamiento y cascada. La suite cubre también recarga estando detenido
y un avance de `UINT32_MAX` ciclos, sin overflow del cálculo host.
El modo normal usa tiempo host a 2^24 Hz escalado por la velocidad; el
diagnóstico usa 280.896 ciclos por frame. No implementa IRQ de timer y no
puede detectar una escritura idéntica al último valor observado.
El recorrido de 30.500 frames terminó con código 0.

## Hito 15: reinicio suave

`SoftReset` normal cierra el save, relanza la ruta y línea de comandos
Unicode del propio ejecutable y termina limpiamente. El diagnóstico sale
para evitar reiniciar el guion. La suite con spawner sustituido comprobó
ruta/argumentos, cierre previo del save y fallo de creación de proceso.
El relanzamiento real con las teclas queda como comprobación manual.
El recorrido de 30.500 frames terminó con código 0.

## Hito 16: render por línea y HBlank

Cada frame ejecuta VBlank, luego 160 líneas de render con DMA HBlank e IRQ
HBlank/VCount habilitadas por IME/IE/DISPSTAT. Los fondos afines mantienen
referencias internas que avanzan con PB/PD y se recargan al cambiar BGxX/Y.
Las suites comprobaron equivalencia frame/líneas, scroll entre filas,
recarga afín, DMA repetido, destino recargado y enmascaramiento de IRQ.

Comparación secuencial de 30.500 frames sin límite de FPS: hito 15
**60,087 s**, hito 16 **70,477 s**, ambos salida 0; relación **1,173×**
(límite del plan: 1,5×). La metodología y commits se describen en
`milestones-13-19-review.md`. No se emulan HBlank en líneas 160–227.

## Hito 17: OBJWIN y mosaico

Los sprites OAM modo 2 aportan máscara sin dibujarse; precedencia
WIN0 > WIN1 > OBJWIN > exterior. El mosaico afecta texto, fondos afines
y sprites; se probaron 1×1 y 4×4, ventanas superpuestas y color/efectos.
Se corrigió el producto afín firmado para matrices negativas. El mosaico
de sprites continúa siendo una aproximación. El recorrido de 30.500
frames terminó con código 0 en **79,372 s**.

## Hito 18: audio PCM y PSG

El parche `0015` deja compilar `m4a.c` bajo `PORT_PC` omitiendo copia de
Thumb a RAM, SWI, esperas VCOUNT y DMA/FIFO físico. El GBA conserva su ruta.
El motor host propio ejecuta secuencias m4a, mezcla PCM con envolvente,
paneo, bucles, muestras comprimidas y reverberación; PSG sintetiza cuadrada,
onda y ruido. SDL reproduce S16 estéreo a 48 kHz; la velocidad 2×–4×
acelera y eleva el tono. Las suites m4a/PSG/audio pasan, incluido fallo de
dispositivo y límite de cola con backend falso.

El recorrido de 30.500 frames terminó con código 0 en **78,606 s**.
`build/hito18-audio.wav` contiene **510,651 s** de audio; en frames
1.000–1.100, RMS normalizado **0,0724753**, pico **18.915**, sin muestras
saturadas. Falta la escucha humana para validar fidelidad musical. El modelo
PSG no observa varias escrituras de bancos de onda dentro del mismo frame.

Los 15 parches se aplicaron a un checkout limpio; el árbol coincide con el
de trabajo: `0e1297df733a73e688c8bd6448982e8f479d4dec`. Repetir `setup.ps1`
no aplicó duplicados. `make compare` devolvió **`pokeemerald.gba: OK`**
con ARM Binutils 2.43.1. No apareció una excepción nueva en el recorrido
conocido; todavía falta comprobar rutas de juego fuera de él.

### Capturas finales y siguiente fallo

GDB volcó el framebuffer al salir en los frames 2.400 (intro, sin entrada),
1.100 (título, con guion) y 30.500 (Villa Raíz, con guion):
`build/hito18-intro-2400.png`, `build/hito18-title-1100.png` y
`build/hito18-world-30500.png`. Se revisaron visualmente: intro con bandas
negras, título completo y protagonista en el exterior con casas y NPC.
La comparación host histórica hito 15/16 en frame 2.400 dio 0 píxeles
distintos, pero ambos muestran un destello blanco, por lo que no certifica
todos los efectos gráficos. El audio real cambia los tiempos de la intro.

**Siguiente fallo:** no se encontró una nueva excepción en el guion hasta
30.500 frames. No se asigna una causa hipotética; habrá que diagnosticar el
próximo fallo que aparezca en otra ruta. Siguen pendientes las limitaciones
enumeradas en `milestones-13-19-review.md`.

## Hito 19: documentación y arranque desde Windows

README y toolchain describen controles, pruebas, velocidad, sonido y límites
actuales. `make -C port exe test` volvió a terminar con las 13 suites PASS.
Se lanzó el ejecutable normal desde el directorio temporal de Windows,
sin depender del cwd del proyecto: cargó la ROM, encontró `build/SDL2.dll`,
creó la ventana SDL e inició `AgbMain`. Se envió `WM_CLOSE` únicamente a
esa ventana de prueba y el proceso terminó por `Port_ExitCleanly`, cerrando
audio y save. Los registros están en `build/hito19-windows-launch.*.log`.
El lanzador de prueba ocultó las ventanas al arrancar; esta comprobación
valida carga/cierre y las capturas anteriores validan el framebuffer.

## Hito 20: cierre al comenzar un combate salvaje

El usuario informó que, después de obtener el inicial y hablar con el
profesor, un encuentro en Ruta 101 mostraba la transición, pantalla negra
y cierre. Se reprodujo el mismo tipo de cierre en GDB iniciando un combate
normal con Torchic nivel 5 y Poochyena nivel 2 después del recorrido al mapa.
El fixture se creó en memoria con funciones del juego; no es una prueba de
la probabilidad de encuentro ni de todos los pasos previos de la historia.

### Causa medida

En el frame **30.589**, GDB detuvo un **SIGSEGV**:

```text
VBlankCB_Slice → VBlankIntr → PortHost_RunFrame → WaitForVBlank → AgbMain
EAX = 0x00000000
EDX = 0x04000048 (WININ)
movzwl 0x2(%eax), %eax
```

`IsBattleTransitionDone` libera y pone a NULL `sTransitionData`, pero deja
registrado `VBlankCB_Slice`. `Task_BattleStart` selecciona `CB2_InitBattle`
para la siguiente iteración; antes de ejecutarla, el host cooperativo llama
a VBlank. El callback antiguo intenta leer `sTransitionData->WININ` desde
la dirección **0x00000002**, que no está mapeada en Windows. No faltaba la
región IO: el fallo era la vida útil de los datos del callback.

### Corrección y verificación

El parche **0016**, generado con `git format-patch`, desregistra VBlank y
HBlank y detiene DMA0 antes de liberar los datos, exclusivamente bajo
`PORT_PC`. Se conserva el código GBA. El ejecutable normal y el diagnóstico
se reconstruyeron, y las **13 suites host pasan**.

La primera repetición alcanzó **CB2_EndWildBattle en frame 32.425,
outcome=1 (victoria)**, y el frame **36.500** sin excepción nueva. La captura
`build/wild-battle-final.png` muestra al protagonista de vuelta en Villa Raíz.
GDB y la entrada por guion están en `build/wild-battle-*.log`/`.gdb`.

La regresión repetible se ejecuta desde MINGW32:

```sh
make -C port diagnostic-exe
python port/tests/wild_battle_smoke.py
```

La prueba usa `build/wild-battle-regression/`: copia local de la ROM,
save vacío propio, ejecutable y logs, todo ignorado por Git. No modifica
`roms/` ni `saves/`. Exige victoria, llegada al frame 36.500, ausencia de
señales y salida limpia. Requiere GDB i686 y Python 3.9 o posterior.

`make compare` volvió a devolver **`pokeemerald.gba: OK`** con ARM Binutils
2.43.1. Se verificó aplicar `0016` mediante `setup.ps1` a un checkout limpio
con `0001`–`0015`: árbol final idéntico al de trabajo,
`e990d9cea5ae60d66b293bff35b6c5f2725b5a49`.

El SHA-256 del save original se mantuvo igual antes y después:
`B5A41C3758763BBEC72769FAB4A2533BF2DB0B6312D93D25A695F9E4B9E02260`.
Durante el combate apareció un aviso no fatal de stream comprimido inválido
(`expected 0x10`); su origen gráfico queda pendiente de diagnóstico. No se
confunde ese aviso con la causa del SIGSEGV corregido, ni se afirma haber
validado todas las transiciones o combates del juego.

## Separación del juego normal y las regresiones — 2026-10-10

El usuario informó un combate al salir de su casa en Villa Raíz. La
regresión anterior forzaba un combate en esa localidad exclusivamente
desde GDB; ambas ventanas tenían el mismo título. No se encontró una
inyección equivalente en los fuentes del juego normal ni una modificación
de las reglas de encuentros. Esto no demuestra cuál de los procesos vio
el usuario, ni reproduce su sesión particular.

Se distingue ahora la ventana de diagnóstico con `DIAGNOSTIC - TEST ONLY`,
y se separa su save como `emerald-pc-diagnostic.sav`. Las regresiones usan
SDL dummy y no muestran una ventana. La prueba de batalla se prepara ahora
en Ruta 101, después de comprobar la salida de casa en Villa Raíz.

La prueba del binario normal alcanzó 30.500 iteraciones de ReadKeys,
mapa **0.9 (Villa Raíz)**, sin llamadas a `BattleSetup_StartWildBattle` y
con salida limpia. El binario ignora las variables de guion, velocidad
diagnóstica y frame de parada. `nm` confirma la ausencia de sus funciones
y variables de diagnóstico. Los pasos y límites de las pruebas se explican
en `normal-and-diagnostic.md`; los logs están en
`build/normal-game-regression/` y `build/wild-battle-regression/`.

No se alteró la ROM ni el save original, cuyo SHA-256 sigue siendo
`B5A41C3758763BBEC72769FAB4A2533BF2DB0B6312D93D25A695F9E4B9E02260`.
Las 13 suites host pasan y `make compare` devuelve `pokeemerald.gba: OK`.

## Imagen trasera del entrenador — parche 0017

GDB detuvo el rechazo de cabecera durante el fixture de combate anterior:
frame **30.615**, origen `0x10c43fa0` (`gTrainerBackPic_Brendan`), destino
`0x1037b9ec` (heap). Cadena: `DecompressedLength` → `Lz77Unpack` →
`LZ77UnCompWram` → `DecompressPicFromTable_2` → `DecompressTrainerBackPic`
→ `PlayerHandleDrawTrainerPic`. Los primeros bytes de origen eran cero.
Las direcciones corresponden a ese binario, no a un ABI estable.

La tabla contiene una imagen `.4bpp` **sin comprimir**. Upstream ya explica
el error y ofrece una copia bajo BUGFIX. El parche `0017` habilita esa misma
ruta también con PORT_PC; no altera los datos ni acepta cabeceras inválidas
en la BIOS. El comportamiento GBA permanece igual.

La repetición del fixture en Ruta 101 ganó en frame **33.365** y llegó a
**37.000** con salida limpia, sin `invalid compressed stream`. La captura
local `build/trainer-backpic-battle.png` (frame 31.300) muestra al entrenador
de espaldas, al Poochyena y el fondo de batalla. No se observó otro cierre
en ese recorrido; esto no valida todos los ataques ni eventos del juego.

Las 13 suites host siguen pasando; `build/trainer-backpic-gba-compare.log`
contiene `pokeemerald.gba: OK`. Aplicar `0017` al checkout aislado con los
16 parches anteriores produce el mismo árbol que el checkout de trabajo:
`de4ac4ca18bc3502e5a3cf4d5eaee31db1db35d9`. También se recompiló y enlazó allí.

## Cierre de almacenamiento Pokémon — parche 0018

La auditoría de callbacks encontró que FreePokeStorageData deja registrado
VBlankCB_PokeStorage, que consulta `sStorage->bg2_X`. Se reprodujo en un
fixture aislado: EnterPokeStorage(2), 500 frames de carga, liberar datos y
servir el siguiente frame antes de ejecutar CB2_ExitPokeStorage. El binario
anterior recibió SIGSEGV en VBlankCB_PokeStorage en frame **31.000**.
El fixture prueba la ventana de vida útil, no una partida del usuario.

0018 retira VBlank antes de liberar sStorage, exclusivamente con PORT_PC.
El build host y las 13 suites pasan; el build GBA da `pokeemerald.gba: OK`
en `build/storage-gba-compare.log`. Aplicar 0018 sobre los 17 parches previos
en el checkout aislado y recompilar reproduce el mismo árbol:
`830b2344fd47636788defbbbc028642d5996c313`.

El inventario del primer lote está en `callback-lifetime-audit.md`.
Hay 67 archivos que registran callbacks de vídeo; no se afirma que todos
contengan errores ni que todas sus pantallas estén probadas. Quedan como
candidatos adicionales en el inventario; los loops de resumen/equipo se
reprodujeron después y se describen a continuación.

La repetición pasó: callback retirado antes del frame cooperativo, vuelta
a Villa Raíz y frame **31.500**, sin señal ni proceso de prueba superviviente.
Log: `build/wild-battle-regression/storage.log`. La primera tentativa del
harness se detuvo por su propio límite 31.000, no por otra excepción del
juego; se movió ese límite antes de servir el frame y se repitió la prueba.

## Cargas de equipo y resumen — parches 0019 y 0020

Ambos fixtures se bloqueaban en frame **30.500**, dentro de una única
llamada del callback. GDB detectó 256 sondeos consecutivos sin avance:
equipo en `gMain.state=8`, resumen en `gMain.state=6`. Equipo espera la
cola DMA de fondos en AllocPartyMenuBgGfx; resumen espera las copias de
tiles en DecompressGraphics. ProcessDma3Requests solo se ejecuta al servir
VBlank, que estos loops nunca alcanzaban en el host cooperativo.

0019/0020 llaman PortHost_RunFrame entre iteraciones bajo PORT_PC. No
cambian la ruta GBA. `menu_load_smoke.py party|summary` abre cada pantalla,
captura en 31.100, cierra con B y verifica CB2_Overworld y mapa **0.9** en
31.600, sin señales y con salida limpia. Las capturas muestran Torchic,
sus HP y la ficha de perfil; no prueban todas las opciones del menú.
Evidencia local: `build/menu-load-party/` y `build/menu-load-summary/`,
incluyendo `before.log`, `gdb.log` y `menu.png`.

Las 13 suites host pasan; `build/menu-load-gba-compare.log` contiene
`pokeemerald.gba: OK`. El checkout aislado recompiló/enlazó los dos cambios
con el mismo árbol de los 20 parches:
`0bb32861903f5d16ce9aa3eff53a8f2cb52ca92c`.
Inventario reproducible: `callback-inventory.md`, generado con
`port/tools/audit_callbacks.py`: 67 archivos, 136 registros no nulos y
17 loops candidatos. Sus límites de análisis están documentados.

## Save no disponible — arranque host

El fixture de tamaño inválido reveló una espera permanente: AgbMain pone
callback2 en NULL cuando no hay flash. El host seguía completando frames,
sin mapa ni callbacks, y no alcanzaba LoadGameSave. Por ello un watchdog
basado solo en frames no lo considera detenido. No hubo excepción.

`port/main.c` abre ahora la flash después de inicializar SDL y antes de crear
la ventana; si falla, informa la causa, libera SDL/memoria y devuelve 1.
Un archivo incorrecto o de solo lectura permanece intacto. Reabrir una
flash ya abierta durante IdentifyFlash conserva la ruta normal del juego.
Pruebas: `build/save-game-regression/invalid-size.log`, `read-only.log`.

También se comprobaron dos guardados por el diálogo real, reapertura con
campos semánticos, recuperación tras corrupción e interrupción del tercer
guardado. El parche 0021 valida IDs de sector antes de indexar las tablas
en PORT_PC: el fixture con ID 0xffff no había causado una señal, pero el
acceso previo estaba fuera del array según el código de save.c.
GBA compare sigue OK (`build/save-id-gba-compare.log`). No se observó otra
excepción en estos recorridos; reset real y cortes eléctricos no quedan
probados por ellos.

## Reinicio normal — parche 0022 y limpieza host

La prueba de A+B+Start+Select recibió SIGSEGV en AgbRFU_SoftReset
(`keyboard-before.log`), al consultar timerSelect con gSTWIStatus NULL.
RFU está deshabilitado en el host. 0022 conserva el apagado inalámbrico
para GBA y lo omite en esa ruta de reset bajo PORT_PC.

`reset_game_smoke.py` verifica la combinación y DoSoftReset sobre el
ejecutable normal: una instancia nueva, velocidad 1×, save contador 2 y
campos correctos. Ruta con espacios y cwd externo. El segundo caso entra
en la función del juego mediante GDB, sin pretender cubrir un evento de
historia. Padre e hijo terminan y el save queda idéntico.

main centraliza la limpieza en atexit para incluir el fallo de relanzamiento.
La prueba de CreateProcess real con archivo inexistente informa Windows
error 2, llega a ShutdownHost, termina con código 1 y no deja reemplazo.
Detalles y límites en `reset.md`. 13 suites PASS; GBA compare OK; checkout
de reproducción recompilado con árbol de 22 parches idéntico:
`b55fa9c92f3f8e4b8ec83911bef75951698612cb`. No apareció otro fallo en estas
rutas; el modelo IRQ/esperas sigue siendo el siguiente trabajo (T08–T12).

## IRQ y esperas cooperativas — T09/T10, parches 0023/0024

El host conserva IF pendiente y aplica IE/IME antes de despachar callbacks,
según el orden de gIntrTable/IntrMain de Emerald. Reconoce antes de llamar,
impide reentrada y separa flags BIOS de frame completado. VBlank ya no es
incondicional. Inicio de DISPCNT con forced blank permite aplicar DISPSTAT
antes de depender de la primera solicitud IRQ. No se ejecuta crt0 ARM.

0023/0024 convierten las siete escrituras C a IF en REG_IF_ACK; bajo PORT_PC
llaman al backend, bajo GBA conservan la asignación original. IntrWait ahora
respeta flags/discard, consume solo los coincidentes y fuerza IME. Halt puede
despertar con IME=0 y observa solicitudes habilitadas aunque se reconozcan
dentro del frame. VBlankIntrWait exige un nuevo flag entregado.

14 suites PASS en `build/irq-wait-build.log`. El ejecutable normal pasa salida
de casa a mapa 0.9 sin batalla; la prueba de Ruta 101 gana y retorna al mapa,
con salida limpia en 37.000. También pasa `save_game_smoke.py --reload-only`.
No aparece otra excepción en estos fixtures. Cierre durante espera: pump
sintético en BIOS y SDL_QUIT en la suite frame, según `bios.md`.

GBA compare OK en `build/irq-ack-rfu-gba-compare.log`. Reproducción con 24
parches y árbol `0db24077d24c9c51701f36e575d466f280bdb3af`, recompilada en
`build/irq-clean-build.log`. Modelo y límites en `register-model.md`.
Siguen pendientes líneas 160–227 completas y eventos IRQ de timers/DMA
(T11–T13); no se afirma precisión temporal de instrucciones ARM.
