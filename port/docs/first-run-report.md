# Primera ejecución de `emerald-pc.exe` i686

## Estado actual: 22 de octubre de 2026

La campaña continua natural completa R01–R05: ocho medallas, Calle Victoria,
cuatro victorias del Alto Mando, Wallace, Hall of Fame y The End. El replay
del Campeon y la recarga final por Continue PASS: regreso al dormitorio,
ocho medallas, game-clear, seis especies/niveles y Hall of Fame valido.
Continue no modifica el archivo guardado. No se concedio progreso por GDB.

R06 (crianza/eclosión y cuatro recargas) PASS. R07 Safari completo (30 bolas/500 pasos y dos Continue). R09–R15 y Checkpoint E siguen abiertos. Las victorias, créditos y Hall of Fame
de fixtures con equipo preparado son pruebas anteriores independientes.
Consulta [cobertura pendiente](tasks/t27-remaining.md) y
[registro de campaña](campaign-progress.md). Los checkpoints, capturas,
ROM y saves se conservan localmente y no se distribuyen en Git.

## Registro cronológico de ejecución

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

## T11–T18 — calendario, dispositivos, PPU y BIOS (2026-10-11)

Cadena local: milestone-24-registers-irq → milestone-25-dma →
milestone-26-graphics → milestone-27-bios. Nuevos parches 0025–0029,
solo hooks PORT_PC; no se alteró la salida original GBA ni se publicó código
upstream, ROM, assets, saves o ejecutables.

- Calendario: 228 líneas, render/DMA HBlank solo en las 160 visibles,
  DISPSTAT/VCount coherentes, DMA antes del callback VBlank. Timers avanzan
  en fases 1006/226; overflow solicita IRQ sin callbacks fuera del hilo.
- Timers: recarga incluso idéntica, enable y control observables, prescaler
  común y cascada. La revisión reprodujo/corrigió ticks extra al cambiar
  divisor. DMA: SAD/DAD estables, repeat/count/máscaras, stop/rearme e IRQ
  al terminar; corregida máscara perdida al recargar DAD.
- PPU: bitmap 3/4/5, restricciones OBJ bitmap, prioridad OAM antes de BG,
  segunda capa sin OBJ ocultos, ventanas/mezcla combinadas, mosaico respecto
  a pantalla y referencias afines reescritas con el mismo valor.
- BIOS: inventario; CpuFastSet por bloques de ocho palabras y alineación
  word, ArcTan2 entero, matrices con ángulo cuantizado y wrap, división y
  raíz con extremos; fixtures propios de LZ/RLE y canarios.

17 suites pasan en `build/t12-control-build.log` tras la última corrección.
Build normal sin controles diagnósticos. La reproducción aislada con 29
parches también compila normal/diagnóstico y pasa las 17 suites en
`build/t18-clean-final.log`; árbol upstream idéntico
`a4e7dad5c792f55e13fde35af0e75e6f5d6c7e60`.

Recorridos finales:

| Prueba | Resultado / evidencia local |
| --- | --- |
| Normal: salir de casa, sin pelea forzada | PASS, build/t18-final-normal.log |
| Batalla Ruta 101 a 1× | Victoria y regreso; salida limpia 37000, build/t18-final-battle-1x.log |
| Batalla a 4× | Mismo resultado, build/t18-final-battle-4x.log |
| Reapertura/recuperación de save | PASS, build/t18-final-save.log |
| GBA original | pokeemerald.gba: OK, build/t18-final-gba.log |

Capturas alineadas del PPU anterior/actual en `build/visual-before/` y
`build/visual-after/`: intro 2400 y 2665, confirmación Torchic 30800.
Torchic está centrado; el frame 2665 es blanco en ambos renderizadores.
Combate 31300 y mapa 37000 también coinciden (0 píxeles distintos).
La comparación controla frame/registros/fixture, pero es entre versiones
del port, no contra hardware. Detalles y límites en `ppu-model.md`.

No apareció otra excepción o espera infinita en estos recorridos. Las
correcciones adicionales proceden de vectores sintéticos reproducibles;
no se afirma cobertura de todos los mapas/combates. El save normal del
usuario mantiene SHA256
`B5A41C3758763BBEC72769FAB4A2533BF2DB0B6312D93D25A695F9E4B9E02260`.

Siguiente tarea: **T19, RegisterRamReset por flags**, que aún es un no-op
host documentado. RTC, fidelidad de audio y campaña completa conservan sus
tareas pendientes. No se hizo push de esta cadena.

## T19–T22 — reset BIOS, RTC y audio (2026-10-11)

- T19: RegisterRamReset aplica flags a regiones/registros GBA y restablece
  DMA/timers/IRQ/PSG; excluye últimos 0x200 IWRAM, ROM y estado C nativo.
  Canarios/flags PASS, igual que reset real por teclado/juego/error spawner.
- T20/0030: RTC fecha BCD, configuración persistida junto al save, sin GPIO.
  El reloj del dormitorio se confirma en 19.531. Cheri brota a +3h;
  VAR_DAYS=1 a +24h; rollback no duplica eventos. Fixture aislado en 30.500.
  El reloj avanza con Windows, independiente de velocidad de frames.
- T21: reverb/contador/rounding, sustain cero y suma PCM corregidos. 1.134
  muestras de ondas propias contrastadas con SoundMain ARM del build GBA.
  Se preservan bounds/final de muestra seguro, sin publicar código/assets.
- T22/0031: 42 writes m4a observables, uploads y triggers del mismo valor,
  ambos bancos y cambio de banco activo en modo 64 muestras; reloj ruido
  corregido. Secuencia real CgbSound y fixtures PSG exactos PASS.

WAV de título (413), efecto selección (5) y grito Torchic (280) en
`build/audio-scene-regression/`, PCM16 stereo 48kHz, 10,062354 segundos
cada uno; mediciones en audio-model.md. El usuario escuchó los tres y
respondió «Se oyen reconocibles». No se confunde esto con equivalencia
bit a bit de todas las canciones ni captura original de hardware.

| Gate | Resultado / evidencia local |
| --- | --- |
| Builds normal/diagnóstico + 19 suites | PASS, t22-dual-build.log |
| Clon base + 31 parches + builds/19 suites | PASS, t22-clean-setup.log y t22-clean-final.log |
| Árbol upstream idéntico | 299f542a9c0d1a6d82ebd7645556e49bdc409692 |
| GBA original | pokeemerald.gba: OK, t22-gba-compare.log |
| Normal: salida casa sin batalla | PASS, t22-normal.log |
| Salvaje a 4×: victoria/regreso/salida | PASS, t22-battle.log, victoria frame 33.365 |
| Save: reapertura/corrupción/escritura interrumpida | PASS, t22-save.log |
| RTC: reloj/berry/día/retroceso | PASS, t20-game.log |
| Reset proceso teclado/juego/error | PASS, t19-reset-game.log |
| Audio de escenas reales | PASS, t21-scenes.log |

No apareció una nueva excepción/bloqueo en estos recorridos. Los tests
no cubren todos los combates, mapas o eventos. El save normal mantiene
SHA256 B5A41C3758763BBEC72769FAB4A2533BF2DB0B6312D93D25A695F9E4B9E02260.
La ROM original no se modifica. Se instaló Unicorn 2.1.4 como dependencia
opcional de la referencia ARM; no hace falta para jugar.

Siguiente tarea: **T23, salida SDL/pausa/velocidad**, seguida de la matriz
más amplia de juego. Sigue pendiente enlace, campaña, x64 y otros hosts.
T19–T22 quedan cerradas según los contratos documentados. Sin push.

## Revisión posterior T19–T22 (2026-10-11)

Se corrigieron overflow/salida insegura del RTC ante reloj inválido, pérdida
de triggers PSG al mezclar hooks y stores directos, dependencias de headers
de las suites y detección de retorno de la referencia ARM. Detalle y logs
en [review-t19-t22.md](review-t19-t22.md).

Builds normal/diagnóstico y 19 suites PASS también en checkout limpio.
Reloj 2100 no genera días/bayas falsos. Referencia ARM 1.134 muestras PASS;
tres escenas de audio PASS. Salvaje 4× victoria 33.365, mapa/salida limpia.
`make compare`: pokeemerald.gba: OK. Sin nueva excepción en estos recorridos.
Save normal intacto. T23 y cobertura amplia de campaña siguen pendientes.

## T23 — salida SDL, pausa y velocidad (2026-10-11)

Menú P pausa audio, vacía la cola y reanuda con datos nuevos. Dispositivo
perdido/error de cola reabre automáticamente con backoff de 120 frames; sin
salida el PSG continúa. Pruebas falsas de pausa, reconexión, cierre y longitud
1×–4× PASS; reset real teclado/juego/fallo de proceso PASS.

16 capturas reales: título, selección, combate y Torchic a 1×–4×. Duraciones
4,035 / 2,0175 / 1,345 / 1,00875 s, cero muestras saturadas y cero errores/
descartes; cola máxima 46,46 ms. Usuario confirma combate 1× y título 4×
«Sí, se oyen bien». Se documentan deltas y límites, sin inferir fidelidad del RMS.

19 suites y builds normal/diagnóstico en raíz y checkout limpio PASS;
make compare: pokeemerald.gba: OK. No apareció una nueva excepción en los
recorridos probados. Detalle: [audio-output.md](audio-output.md).
Siguiente: T24, variantes de combate; campaña todavía pendiente.

## T24 — variantes salvajes

Victoria, derrota/curación, huida y captura pasan con equipo/HP/experiencia/
dinero/item y mapa comprobados. Se encontró SIGFPE real al lanzar Master Ball
en Cmd_handleballthrow (32.167): índice fuera de tabla y división por odds cero.
Parche 0032 bajo PORT_PC; captura posterior PASS, GBA compare OK.
Detalles y límites en [gameplay-matrix.md](gameplay-matrix.md).

## T25 — entrenadores y mecánicas

Nueve escenarios PASS: entrenador/rival/gym/doble, veneno/Guts, cambio, poción,
combate largo y aprendizaje/evolución. Se corrigieron punteros sign-extended de
Rock Slide (0033), stop de grito nulo (0034) y party-order nulo rival (0035).
GBA compare OK. Detalles, direcciones, frames y límites en gameplay-matrix.md.

## T26 — almacenamiento

Se reprodujeron accesos nulos en prioridad del sprite y callback tras liberar
sStorage; parche 0036 PORT_PC. Los seis menús pasan tres ciclos y las cuatro
operaciones del PC pasan mutación, campo, guardado y recarga en nuevo proceso.
Detalles y reproducción en gameplay-matrix.md.

## T27 — contenido por segmentos

32 mapas, marcha/bici/surf, cinco combates de Liga, Hall of Fame/créditos,
concurso, huevo, Safari y Tower singles pasan sus comprobaciones semánticas.
0037 corrige argumento nulo de lluvia; 0038/0039 evitan esperas de RFU ausente;
0040 conserva resto ARM con divisor cero. GBA compare OK con KEEP_TEMPS=1
NODEP=1 tras una espera de make al regenerar dependencias; fuentes modificadas
recompiladas y ROM verificada. Campaña continua permanece pendiente.
Detalles y límites en gameplay-matrix.md.

## T28 — controles

Teclado/remapeo persistente, hotplug/foco y mando virtual SDL real PASS;
21 suites host. El normal sale de casa sin combate; retirada PC diagnóstica
y recarga PASS; reset por teclado/juego y fallo real de spawn PASS. SDL enumera
0 mandos físicos: prueba física pendiente. Ver controller-input.md.

## T27 — continuación con estado persistente

En codex/milestone-34-campaign-continuation se midió la cadena dirigida:
Wally captura y regresa; ocho scripts de líderes entregan medallas/MT;
Norman lleva a la entrega de Surf; cuatro scripts del Alto Mando conservan
el estado; Wallace inicia su secuencia y lleva al Hall of Fame y The End.
Un proceso nuevo confirma game-clear, ocho medallas y un equipo HOF válido
con tres Pokémon; la lectura no modifica el save. Safari independiente añade
recepción/cobro, captura y salida al agotar la cuota mediante la rutina de pasos.

Las esperas nuevas fueron del harness: límite de diálogos y selección por
índice original pese al reordenamiento de equipo del menú. GDB mostró
CB2_UpdatePartyMenu y Task_ReturnToChooseMonAfterText/Task_PrintAndWaitForText
con Pokémon vivos; se utiliza GetPartyIdFromBattleSlot. El guion maneja
movimientos con PP disponibles y reemplazos. No se necesitó un parche upstream
nuevo ni se encontró una nueva excepción del port en estos recorridos.

21 suites host y verify-normal PASS; make compare KEEP_TEMPS=1 NODEP=1 da
pokeemerald.gba: OK. ROM/save originales intactos. La campaña está asistida
con warps/equipo; intro, Aqua/Magma, eventos y gating natural, eclosión y
ampliación del Frontier siguen pendientes. T27 permanece abierta.
Evidencia y reproducción: [campaign-progress.md](campaign-progress.md).

## T27 natural: derrota de Roxanne y sombra tras liberar datos

La campaña con teclado completó intro, Mudkip, rescate de Birch, May,
Pokédex/bolas, guardado y Continue. Wally completó su captura; la puerta de
Norman siguió bloqueada antes de las medallas. Devon en Petalburg Woods llegó
al estado 1 mediante victoria y diálogo, después de una derrota legítima y
retorno al Centro Pokémon. Los helpers no conceden progreso a esta partida.

Al perder contra el primer Geodude de Roxanne, frame 230741 del primer
proceso, apareció `SIGSEGV` en `SpriteCB_EnemyShadow+126`, dirección
`0x100bba6b`. La instrucción `mov (%eax),%eax` recibió EAX=0. GDB confirmó
`gBattleSpritesDataPtr=0`, `gMonSpritesGfxPtr=0`, especie enemiga 74 y
`gBattleMainFunc=FreeResetData_ReturnToOvOrDoEvolutions`.

El cierre libera los datos de combate durante el fundido, antes de que
`ResetSpriteData` retire los sprites. Geodude tiene elevación 16, así que su
sombra aún ejecuta un callback que consulta datos liberados. El parche 0041
oculta la sombra y cambia su callback cuando esos datos ya son NULL, solo bajo
`PORT_PC`. El fundido sigue avanzando; no se omite `UpdatePaletteFade` ni se
retorna desde la función que falló para fingir un resultado.

Regresión propia `battle_shadow_teardown_smoke.py`: Magikarp débil contra
Roxanne en un fixture independiente. El binario anterior reproduce el mismo
SIGSEGV en frame 33206 (`build/t27-shadow-before0041.log`). Con 0041, el mismo
caso registra `SHADOW AFTER TEARDOWN`, outcome 2, blackout, HP restaurados y
callback de campo: PASS (`build/battle-shadow-teardown/gdb.log`).

Build normal/diagnóstico, 21 suites y `verify-normal`: PASS.
`build/t27-shadow-gba.log`: `pokeemerald.gba: OK`.
El clon de reproducción aplica 0041 después de los 40 parches anteriores y
produce el mismo árbol `a1e2ff89b49b2936363b001617e0d6644165264e`.
La campaña se reinicia con el binario corregido desde el guardado real de
Devon. El clon también compila normal/diagnóstico, pasa las 21 suites y
`verify-normal` (`build/t27-shadow-clean-build.log`). Roxanne fue derrotada
después: Marshtomp nivel 16, primera medalla y estado de Norman 3 guardados
y comprobados mediante Continue en un proceso nuevo. R02/T27 siguen abiertos.

## T27 natural: copyvar literal en Granite Cave

Con dos medallas y Marshtomp nivel 19, el acceso real a Granite Cave B1F
falló en `ScrCmd_copyvar+53`, dirección `0x102d0356`, al cargar el mapa.
La instrucción `movzwl (%eax),%edx` recibió EAX=0. El contexto inmediato
apuntaba a `CaveHole_FixCrackedGround`; bytes `19 22 40 01 00`:
`copyvar VAR_ICE_STEP_COUNT, 1`. `GetVarPointer(1)` retorna NULL, porque
1 es un literal, no un identificador de variable. El destino era válido.

Upstream ofrece `setvar` bajo UBFIX en ese script y en Sky Pillar 2F/4F.
La compilación C host seleccionaba SAFE_DIV bajo PORT_PC, pero los datos
ensamblados mantenían las variantes originales. `port/Makefile` selecciona
UBFIX en CPP y gas exclusivamente para los objetos host. La macro
`UBFIX=UBFIX` conserva el identificador que requiere `.ifdef UBFIX` de gas;
`--defsym UBFIX=1` activa también la variante de Magnitude. La dependencia
en Makefile asegura reconstruir los objetos de datos al cambiar esas opciones.
No se editaron scripts ni fuentes upstream; no corresponde un parche 0042.

`script_ubfix_smoke.py` comprueba `16 22 40 01 00` (`setvar`) y carga
Granite Cave B1F, Sky Pillar 2F y 4F con el contador inicialmente a cero.
Las tres transiciones dejan VAR_ICE_STEP_COUNT=1 y callback de campo: PASS
en `build/script-ubfix/gdb.log`. Son fixtures dirigidos, no evidencia de haber
recorrido Sky Pillar en la campaña.

Build normal/diagnóstico, 21 suites y verify-normal PASS;
`build/t27-script-ubfix-gba.log`: `pokeemerald.gba: OK`.
La campaña se reanuda desde el guardado real de Brawly para repetir la escalera.

## T27 natural: cierre del nombre después de capturar

Tras entregar los bienes a Stern, la primera captura por bolsa/teclas en
Ruta 110 abrió la pantalla de nombre. Al confirmarla, frame 154610 del tercer
proceso, SIGSEGV en `CurrentPageToKeyboardId+8`, `0x10228c37`:
`movzbl 0x1e22(%eax),%eax`, con EAX=0. `sNamingScreen` ya había sido liberado
y puesto a NULL. Backtrace: CurrentPageToKeyboardId →
GetCurrentPageColumnCount → SpriteCB_Cursor → AnimateSprites → BattleMainCB2.
El script de combate había avanzado hasta BattleScript_GiveCaughtMonEnd;
el Pokémon todavía no estaba incorporado al equipo.

La pantalla de nombre para capturas retorna directamente a BattleMainCB2,
que anima sprites antes de restaurar el campo. Retenía sprites del teclado
con callbacks que dependían del bloque liberado. El parche 0042 añade
ResetSpriteData antes de liberar ese bloque, exclusivamente bajo PORT_PC.
Se conserva el callback de retorno y la lógica de captura; no se salta ninguna
función del combate ni se modifica el comportamiento de GBA.

`caught_naming_teardown_smoke.py` usa un encuentro y Master Ball preparados
en un fixture independiente; selecciona bolsa, bola y nombre con teclas.
No acredita captura natural de campaña. El binario anterior reproduce el
mismo SIGSEGV (`build/t27-naming-before0042-gdb.log`). El corregido pasa por
MainState_Exit, consume la bola, añade Wingull al equipo, deja sNamingScreen
NULL y retorna al campo con outcome 7: PASS
(`build/caught-naming-teardown/gdb.log`).

Build normal/diagnóstico, 21 suites y verify-normal PASS
(`build/t27-naming-build.log`); `build/t27-naming-gba.log`:
`pokeemerald.gba: OK`. Clon limpio más los 42 parches: árbol
`35365585bab00d57aceea569202ad6d006e26a5b`, igual al árbol de trabajo upstream.
El clon también compila normal/diagnóstico y pasa las 21 suites y
verify-normal (`build/t27-naming-clean-build.log`). Se reabre por Continue
el último guardado real de Ruta 110 para repetir la captura en la campaña.

## T27 natural: callbacks de Vuelo tras liberar la pantalla

La primera confirmación de Vuelo, después de ganar la sexta medalla, produjo
SIGSEGV en SpriteCB_FlyDestIcon+8 (EIP 0x102bf070), frame 658172.
`movzwl 0x8(%eax),%eax` recibió EAX=0: sFlyMap ya era NULL.
Backtrace: SpriteCB_FlyDestIcon -> AnimateSprites -> CB2_FlyMap ->
CallCallbacks -> UpdateLinkAndCallCallbacks -> AgbMain. CB_ExitFlyMap había
seleccionado CB2_ReturnToField, pero la iteración actual de CB2_FlyMap todavía
animaba los iconos que dependían del bloque liberado.

El parche 0043 retira los sprites con ResetSpriteData antes de liberar
sFlyMap, solo bajo PORT_PC. La ruta de GBA conserva su comportamiento.
La regresión natural `--phase r03-fly` parte del guardado real con seis
medallas: confirma Fortree -> Rustboro, cancela otra selección y comprueba
el retorno al menú/equipo/campo en las mismas coordenadas, luego confirma
Rustboro -> Fortree y guarda: PASS, sin señales y salida normal
(`build/t27-natural-fly-replay.log`). Continue de r03-fly-roundtrip conserva
mapa, equipo, movimientos, seis medallas, eventos, inventario y dinero;
el archivo de guardado no cambia (`build/t27-fly-roundtrip-reload.log`).

Normal/diagnóstico, 21 suites y verify-normal: PASS
(`build/t27-fly-build.log`). Compare GBA: pokeemerald.gba: OK
(`build/t27-fly-gba.log`). La copia limpia con los 43 parches produce el árbol
cd4312af599d1212c62ae2a72dca15631fec46c3, idéntico al upstream local, y compila
normal/diagnóstico con las 21 suites y verify-normal: PASS
(`build/t27-fly-clean-build.log`). R04–R15 siguen pendientes; no se ha
verificado todavía el resto de la campaña ni se declara otro fallo observado.

## T27 natural: Mossdeep sin nueva excepcion

El puzzle completo de suelo/transportes llega a los lideres mediante teclas;
la repeticion desde la entrada termina normalmente (t27-natural-mossdeep-circuit-replay.log).
La campana original vence a Tate/Liza, recibe la septima medalla y conserva
recompensas y eventos al usar Continue. Una repeticion pierde con outcome=2
sin senal: el juego retorna al exterior del Centro y cura al equipo. Se
registra como derrota, no como cierre ni como repeticion de victoria.
No hay nuevo fallo nativo que justifique un parche tras 0043 en este tramo.
Detalles y limites de cobertura: campaign-progress.md; R04/T27 abiertos.

## T27 natural: Centro Espacial y Buceo recibido

La ruta por las dos plantas, los tres reclutas seguidos, seleccion de tres
Pokemon y combate junto a Steven terminan normalmente. Las repeticiones
r04-space-upper, r04-steven y r04-dive-gift dan PASS; Continue de
r04-dive-verified conserva los eventos y el movimiento aprendido.
La incompatibilidad de Pelipper con Dive es un dato original de learnset,
no una excepcion; se enseno a Swampert. No hubo nuevo fallo nativo en este
tramo. El uso submarino y el resto de R04 todavia no quedan acreditados.

## T27 natural: emerger en una cueva sin conexiones (0044)

Al elegir Dive para emerger desde Underwater_SeafloorCavern (6,7), SIGSEGV en
GetMapConnection+11, EIP 0x1022E8AB, instruccion mov (%eax),%eax, EAX=0.
gMapHeader.connections es NULL: ese mapa declara connections=null y usa un
warp fijo que su script OnResume establece hacia SeafloorCavern_Entrance (10,17).
La funcion leia connections->count antes de devolver NULL para permitir
la alternativa SetDiveWarp -> RunOnDiveWarpMapScript / sFixedDiveWarp.
Backtrace: GetMapConnection -> SetDiveWarp -> SetDiveWarpEmerge -> TrySetDiveWarp
-> SetUpFieldMove_Dive -> CursorCb_FieldMove -> Task_HandleSelectionMenuInput
-> RunTasks -> CB2_UpdatePartyMenu -> CallCallbacks -> AgbMain.

Parche 0044: comprobar connections==NULL antes de leer sus campos, solo bajo
PORT_PC. No fabrica un destino: devuelve NULL y la logica original usa el warp
fijo. Cinco lineas, src/overworld.c; commit upstream privado 9556659ee1daf2663ef64aba8c08472a5bfff332.
La prueba --phase r04-seafloor-dive parte del guardado natural Route128, baja
en (38,27), entra por UP a la cueva submarina y usa el menu Dive para emerger.
El binario anterior reproduce la misma senal (t27-seafloor-dive-before-fix-gdb.log).
Con el parche llega a Entrance (10,17), mantiene Surf y guarda por UI: PASS,
sin senales, salida normal (t27-seafloor-dive-after-fix.log).

Normal/diagnostico, 21 suites y verify-normal: PASS (t27-dive-host-build.log).
GBA: pokeemerald.gba: OK (t27-dive-gba-compare.log). El checkout de reproduccion,
limpio con los 43 parches anteriores, aplica 0044 con git am y genera el mismo
arbol 386a8afd3ba959f7852cd2e2ca28d15daa22818d; sus dos builds, 21 suites y
verify-normal pasan (t27-dive-clean-build.log).

Siguiente fallo observado al reabrir el guardado submarino previo: SIGSEGV en
LoadSaveblockObjEventScripts+78, EIP 0x1022DEB0, mov 0x10(%ecx),%eax, ECX=0.
Su bucle restaura 64 scripts desde un array de objetos NULL y count=0 en
Underwater_Route128. Es un fallo distinto de Continue, pendiente del parche
0045; el recorrido corregido por 0044 parte de un guardado de superficie y
no acredita aun Continue submarino. Logs privados gdb-post-dive-fix.log.

## T27 natural: Continue de mapa sin objetos (0045)

La recarga de r04-underwater128 se detenía en frame 1203, antes de devolver
control de campo. LoadSaveblockObjEventScripts+78, EIP 0x1022DEB0, ejecutaba
mov 0x10(%ecx),%eax con ECX=0. Underwater_Route128 declara cero object_events;
mapHeaderObjTemplates es NULL. El bucle original copia scripts de 64 entradas
sin limitarse a objectEventCount; tambien puede leer mas alla de arrays cortos.
Backtrace: LoadSaveblockObjEventScripts -> CB2_ContinueSavedGame -> CallCallbacks
-> UpdateLinkAndCallCallbacks -> AgbMain -> main.

Parche 0045: bajo PORT_PC, restaurar scripts solo cuando el array existe y
el indice esta dentro de objectEventCount; dejar el resto de scripts en NULL.
Se mantienen las 64 entradas de destino y la asignacion original de GBA.
Commit privado upstream 13816476b2e419be1c06ab4ecdf61c0836486706.

La prueba de Continue exige ahora parar en Port_ExitCleanly y control de
campo antes de validar el manifiesto, para no leer un estado intermedio tras
una excepcion. Con el binario anterior reproduce SIGSEGV
(t27-underwater-reload-before-fix-gdb.log). Con 0045, Continue submarino PASS,
archivo sin cambios (t27-underwater-reload-after-fix.log). La misma comprobacion
en Mossdeep Gym, mapa con objetos, tambien PASS (t27-underwater-mossdeep-reload.log).
Normal/diagnostico, 21 suites y verify-normal: PASS (t27-underwater-host-build.log).
GBA: pokeemerald.gba: OK (t27-underwater-gba-compare.log).

El checkout de reproduccion limpio con 0044 aplica 0045 y coincide con el
arbol f6122159ccf96e28ae9cdf8d44a26ce70563e301; ambos builds, 21 suites y
verify-normal PASS (t27-underwater-clean-build.log). La campana se reinicia
desde el MISMO archivo submarino previo, conservado antes de ambos cierres.
No se omite ninguna funcion de juego ni se reescribe progreso para continuar.
La exploracion de Seafloor sigue abierta.

## T27: niebla submarina opaca, corregida en el PPU propio

La revision visual mostro terreno invisible bajo una capa gris en
Underwater_Route128. Con los registros del juego sin alterar, WIN0 deshabilita
efectos normales de color, pero el OBJ de niebla necesita alfa forzado.
ResolvePixels lo condicionaba tambien a ese bit de ventana. Se separaron ambas
reglas en port/port_ppu.c y se corrigio la expectativa sintetica anterior.
La regresion falla antes y las 21 suites pasan despues; captura con los mismos
registros muestra ahora la entrada, rocas y fondo submarino. Detalles y referencia
primaria en ppu-model.md. Builds normales/diagnostico, reproduccion y GBA compare:
PASS. El save original del usuario sigue intacto. No requiere parche upstream.

## T27 natural: Seafloor completado hasta la salida de Kyogre

Tras 0044/0045 se resolvieron por teclado las salas de rocas, corrientes,
Shelly y los nueve empujes finales. Los replays de Shelly, puzzle y Archie
terminan sin senales y con salida normal. El script original de la orbe y
Kyogre retorna a Route128 y activa los eventos de Sootopolis; Continue de
r04-kyogre-verified valida su persistencia, sin cambiar el save.
No aparecio otra excepcion nativa en ese tramo. La niebla se corrigio en el
PPU propio, descrito arriba. Sky Pillar/Sootopolis y el resto de R04-R15 siguen
pendientes; no se declara completo T27.

## T27: objeto de camara sin plantilla al llegar a Sootopolis (0046)

La llegada natural por Dive produjo SIGSEGV en
GetObjectEventFlagIdByLocalIdAndMap+40 (EIP 0x10185BFA, EAX=0): lectura
movzwl 0x14(%eax),%eax. RemoveCameraObject intenta retirar LOCALID_CAMERA=127
(mapNum=7, mapGroup=0). Es un objeto creado en runtime por SpawnCameraObject,
sin plantilla en el mapa. La funcion ya tenia un guard bajo UBFIX, pero el
build C host no define UBFIX globalmente (0007 solo adapta SAFE_DIV).
0046 habilita ese mismo guard con PORT_PC: devuelve flag 0, que FlagSet trata
como no-op, y deja que la retirada original del objeto termine. No altera GBA.

Antes: t27-sootopolis-camera-before-fix-gdb.log reproduce el SIGSEGV.
Despues de 0046 aparecio ademas la espera DMA descrita en 0047 mas abajo;
no se declara que 0046 por si solo resuelva toda la escena. Con ambos parches,
--phase r04-sootopolis-entry PASS: dos creaciones de camara observadas, ninguna
camara activa al terminar, campo desbloqueado en (29,53), estado de ciudad 2,
guardado por menu y salida normal. Registro privado:
build/natural-campaign-replay-r04-sootopolis-entry/campaign.log.
Build host, 21 suites y verify-normal PASS (t27-camera-host-build.log).
GBA compare OK (t27-camera-gba-compare.log). Checkout limpio con 0046:
arbol 975e42ad9efd86b763bced6234a2d109e93dbc90 y ambos builds/21 suites PASS
(t27-camera-clean-build.log). La campana y el replay terminaron la llegada
con 0047 aplicado tambien; Sky Pillar y la octava medalla siguen pendientes.

## T27: espera de DMA sin VBlank en la escena de Rayquaza (0047)

El replay con 0046 se quedo en frame 16824, sin otra llamada al temporizador
de frames. Interrumpir con GDB muestra IsDma3ManagerBusyWithBgCopy ->
FreeTempTileDataBuffersIfPossible -> LoadDuoFightSceneGfx -> Task_DuoFightAnim
-> CB2_RayquazaScene. REG_VCOUNT=0, cola desbloqueada, cursor DMA=116.
El bucle vacio esperaba que una IRQ real drenara la cola de DMA3, pero el host
solo entrega IRQ al avanzar PortHost_RunFrame. Evidencia privada conservada:
t27-rayquaza-dma-before-fix-main.log y t27-rayquaza-dma-before-fix-gdb.log.

0047 llama VBlankIntrWait bajo PORT_PC en las cinco esperas equivalentes de
rayquaza_scene.c (duo, vuelo, descenso, carga y retirada). El resto del bucle
y la comprobacion original de fin se conservan; GBA conserva la espera vacia.
No se vacia la cola desde el harness ni se salta la escena. La llegada real
y --phase r04-sootopolis-entry terminan con campo desbloqueado en frame 18360
y guardado nativo en 19488. El replay registra dos camaras y ninguna pendiente.
Los otros cuatro segmentos se verificaran al invocar la escena completa;
no se declaran cubiertos por la llegada abreviada.

Normal/diagnostico, 21 suites, verify-normal PASS:
t27-rayquaza-dma-host-build.log. GBA compare: pokeemerald.gba: OK
(t27-rayquaza-dma-gba-compare.log). El checkout limpio con 0047 da el mismo
arbol f86fa9af402b714f06e6d7ad8c0a9e89975451f4 y ambos builds/21 suites PASS
(t27-rayquaza-dma-clean-build.log). El replay nuevo usa solo teclado y lecturas
de GDB; SpawnCameraObject se observa mediante un breakpoint que no detiene.

## T27: los cinco segmentos de Rayquaza ya ejecutados

Tras subir Sky Pillar y despertar a Rayquaza por el evento original, Fly
regresa legalmente a Sootopolis y ejecuta la escena completa. Tanto la campana
como --phase r04-rayquaza-peace observan exactamente una llamada a cada uno de
los cinco loaders: duo, vuelo, descenso, carga y retirada. Ninguna espera de
0047 vuelve a bloquear. Se conserva una captura por segmento 100+ frames tras
su carga, usando solo lectura de sPixels desde el checkpoint del host.
Capturas privadas: build/natural-campaign-replay-r04-rayquaza-peace/
rayquaza-scene-Load*SceneGfx.png. Se revisaron visualmente vuelo, descenso,
carga y retirada: Rayquaza, nubes/niebla, luz y ambos legendarios son visibles.
Las bandas negras corresponden al recorte original de esta escena.

La escena termina en (43,32), VAR_SKY_PILLAR_STATE=3 y flag 0x53=0; ya no
quedan camaras activas. Guardado real r04-sootopolis-peace (120352) y Continue
completo PASS, sin reescribir el archivo (t27-sootopolis-peace-reload.log).
Los replays de apertura, subida, despertar y paz pasan y salen normalmente:
t27-sky-open-replay.log, t27-sky-climb-replay.log,
t27-rayquaza-awaken-replay.log y t27-rayquaza-peace-replay.log.
No aparecio otra excepcion nativa en este tramo. La octava medalla y R05-R15
siguen pendientes; T27 permanece abierto.

## T27: octava medalla por juego real, sin nueva excepcion

Juan produjo dos derrotas normales contra Kingdra con la politica de ataques
simple. Se guardaron ambas, con el blackout original, perdida de dinero y
recompensas aun ausentes. No se modifico la dificultad ni el entrenador.
Quita-Movimientos, MT26 recogida anteriormente, tiendas y una estrategia de
cambio/objetos real permitieron ganar con el mismo equipo natural.
--phase r04-juan-tactical PASS: ocho medallas, trainer272, flags4F7/AC,
Sootopolis6 y MT03/WaterPulse291 verificados. Dos X Attack y un X Speed se
consumieron por la bolsa, tras retirar y devolver a Swampert para reiniciar
las bajadas de estadisticas. El guion conserva/restaura su propia funcion de
seleccion de botones; no modifica memoria de progreso del juego.

Se corrigio una espera del guion (UP antes del cursor Yes/No), reiniciando
desde el mismo guardado nativo previo y preservando el log anterior. La prueba
corregida sale normalmente; no se cuenta ese fallo de automatizacion como
crash del port. Continue de r04-juan-win valida todo el manifiesto y conserva
el archivo (t27-juan-win-reload.log). Captura privada r04-juan-win.png.
R04 esta cubierto; T27 sigue abierto para R05-R15. No hay push.

## T27 R05: captura y Cascada hasta Calle Victoria

La seleccion de Ball de las pruebas ahora exige un stack concreto (Poke Ball
por defecto), en lugar de tomar el primero. La captura R02 de Wingull sigue
pasando. En Dewford se capturo Tentacool18 con Ultra Ball comprada, preservando
Master Ball y Poke Balls. HM07 se enseno por bolsa; el replay y Continue pasan.
Gloom aprende Flash por HM05 antes del recorrido maritimo a Ever Grande.

Pisar Waterfall13 sin activar el movimiento devuelve al jugador al sur por
la tabla original de movimientos forzados; las primeras aproximaciones del
guion no eran un bloqueo nativo. Se llega mirando al norte desde una casilla
normal, se pulsa A y se acepta Yes. FldEff_UseWaterfall se ejecuta una vez con
monId4, y el jugador asciende (18,68)->(18,59). --phase r05-waterfall PASS,
incluyendo cura y entrada real a VictoryRoad_1F (15,40), sin senales y con
salida normal. El planificador ya evita usar cascadas como Surf ordinario.
Capturas privadas r05-waterfall-used.png y r05-victory-road-entry.png.
No se ha cambiado codigo nativo adicional desde 0047. R05 y T27 siguen abiertos.

## T27 R05: Wally y segundo sotano de Calle Victoria

Wally se derrota por combate original: trainer519, flag7E y Var40C3=2.
Replay r05-wally y Continue r05-wally-verified PASS. Se entra al primer sotano
por la escalera (9,14), no por una ruta inaccesible. Flash usa a Gloom desde
Party: FldEff_UseFlash una vez, flag888=1 y GetFlashLevel()=1 (radio ampliado,
no luminosidad completa). Replay r05-flash PASS; capturas antes/despues privadas.

Fuerza desplaza realmente las rocas locales3 (4,7)->(3,7) y4 (9,10)->(10,10).
Golpe Roca elimina el obstaculo10 en (18,12). Los replays r05-upper-boulders
y r05-smash-corridor pasan, verificando posiciones/ausencia de obstaculos.
La escalera (30,25) conduce al segundo sotano, con combates originales durante
el recorrido. r05-second-basement PASS y checkpoint r05-victory-road-b2f-entry.
Los manifiestos y Continue ahora incluyen Var40C3, FlashLevel y Ultra/Great Balls.

No ha aparecido otro fallo nativo en estos tramos. No se han escrito banderas,
posiciones, objetos ni equipo: solo teclas y guardados del juego. El build ARM
continua verificado con 0047 (sin cambios nativos posteriores). R05 sigue abierto:
faltan el resto de Calle Victoria, Liga, creditos y Hall of Fame. Sin push.

## T27 R05: salida de Calle Victoria y acceso real a Liga

B2F: Surf desde (33,17), cascada central (26,12)->(26,8), cruce al oeste
y bajada forzada original (8,10)->(8,14). La escalera (19,12) llega a B1F
(17,16). La escalera del este es una zona lateral: se comprobo sin forzar
warps y su replay separado tambien pasa. r05-cave-waterfalls PASS.

En B1F se rompen rocas11/12 y empuja roca5 al norte una vez; la escalera
(20,21) lleva a 1F(21,32). r05-central-puzzle PASS. La salida norte llega
a EverGrande(18,28): incluye el paso automatico tras la puerta, que faltaba
en la primera asercion del guion. El replay corregido r05-victory-exit PASS.
La enfermera de Liga se alcanza desde (3,4), no desde el mostrador (3,3).
Todos los HP se verifican al maximo. r05-league-lobby PASS y Continue del
checkpoint r05-league-lobby-rested PASS, archivo sin cambios.

Capturas privadas revisadas: r05-victory-road-exit.png,
r05-league-lobby-rested.png y r05-sidney-ready.png, dentro de build/.
El build GBA vuelve a dar pokeemerald.gba: OK (t27-league-gba-compare.log).
Sin nuevo fallo nativo ni cambios en upstream. R05 sigue abierto para Alto
Mando, Campeon, creditos y Hall of Fame. No se da T27 por terminado.

El control original de medallas desplaza ambos guardias y activa flag107;
r05-league-gate PASS desde el guardado del lobby. Se entra por Hall5 al cuarto
de Sidney. El primer intento con el equipo de campana termina en derrota
normal (gBattleOutcome=2), no en excepcion: reaparece fuera de Liga y permite
guardar. Cuatro Hyper Potions consumidas y dinero14642->7321; no se cuenta
como victoria ni se da el Alto Mando por cubierto. r05-sidney-result privado.

## T27 R05: Sidney, Torment y recarga del primer Alto Mando

Tras la derrota se compran cinco Hyper Potions por UI (6000), sin reponer
objetos por el depurador. r05-sidney-supplies PASS. El guion de combate elige
Pelipper contra Grass y Swampert contra el resto, usando Pokemon/Send Out y
las pociones reales. r05-sidney-tactical PASS: outcome1, flag4FB=1 y tres
cambios observados. No se alteran stats, PP, rivales ni reglas de combate.

Se encontro una espera propia de la automatizacion: Pelipper bajo Torment
(status2=80000000, gLastMoves=19) intentaba repetir Fly. GDB lo situa en
BattleScript_SelectingTormentedMove+3 / CompleteOnInactiveTextPrinter2.
El selector ahora omite ese ultimo movimiento mientras Torment esta activo;
solo lee estado y pulsa teclas. La misma batalla antes detenida termina en
outcome1 tras recargar el helper, sin reiniciar ni editar progreso del juego.

Tambien se limita Continue a frame1181 al estar frente a Sidney: los pulsos
hasta8000 podian iniciar la pelea antes de instalar la politica de pruebas.
Se conservan logs del replay anterior, y el replay corregido sale normalmente.
Continue de r05-sidney-win-verified PASS, archivo sin cambios; el manifiesto
incluye flag107, victorias del Alto Mando y game-clear. Captura privada
r05-sidney-win-verified.png. Se ha llegado al cuarto de Phoebe por las puertas
originales; R05 sigue abierto para los otros combates, creditos y Hall of Fame.

## T27 R05: derrota normal ante Phoebe y Bici Carrera por UI

El intento siguiente llega a Phoebe sin Pelipper y sin Hyper Potions. Termina
con outcome2, flag4FC=0 y regreso normal a EverGrande(18,6), dinero6221->3110.
No hay senal ni excepcion; se puede guardar. r05-phoebe-loss reproduce el
blackout y conserva ocho medallas. Las victorias temporales del Alto Mando
se reinician por el juego; la victoria de Sidney queda probada en su propio
checkpoint/replay, no se presenta este intento como una Liga completada.

Se vuela a Mauville, se habla con Rydel desde (3,5) mirando izquierda y se
elige Mach Bike por dialogo. Item259 pasa0->1. Se cura por enfermera real;
r05-mach-bike PASS. Desde Bag/Key Items se usa la bicicleta, comprobando bit2
de gPlayerAvatar, se guarda, y se desmonta por el mismo menu. El contexto de
Key Items tiene dos columnas (MultipleRows): se corrigio la suposicion de
SingleRow del guion. r05-bike-toggle PASS y Continue r05-mach-bike-tested PASS,
guardado intacto. El manifiesto ahora incluye la propiedad del item259.

Fly a Mossdeep, Surf y conexiones Route127/128/129/130/131, entrada normal
al Pilar, puertas/escaleras hasta1F: r05-pillar-return PASS. Escalera10,1 a2F
(10,2), estadoSkyPillar3 y casilla13,5 con comportamientoD2 (piso agrietado
real, no layout limpio de la primera visita): r05-broken-floor-entry PASS.
Continue r05-sky-pillar-broken-floor PASS, archivo intacto. Este es el punto
actual de continuacion: falta resolver el recorrido con Bici Carrera, preparar
un nuevo intento de Liga y completar el final; R05 y T27 siguen abiertos.

Capturas privadas: r05-mach-bike-mounted.png, r05-sky-pillar-broken-floor.png.
El proceso principal termina normalmente al salir del checkpoint del host.
ROM original SHA1 f3ae088181bf583e55daf962a92bb46f4f1d07b7 y save del usuario
SHA256 b5a41c3758763bbec72769fab4a2533bf2db0b6312d93d25a695f9e4b9e02260
conservados. Solo cambios en helpers/documentacion; GBA sin cambios desde0047,
ultima verificacion pokeemerald.gba: OK. Sin push; planes del usuario intactos.

## T27 R05: cruce real del piso agrietado de Pilar Celeste 2F

Desde r05-sky-pillar-broken-floor se monta la Bici Carrera por Bag/Key Items.
El recorrido usa (12,2)->(12,13)->(1,13)->(1,7)->(3,7)->(3,2) y la escalera
original hasta 3F(3,2). ride_to observa cada dos frames sin soltar la direccion.
El helper advance permite hold==frames; no cambia input ni comportamiento
fuera del ejecutable de diagnostico. No se escriben velocidad ni coordenadas.

Los intentos iniciales cayeron normalmente por frenar contra el muro en
(13,7), o arrancar demasiado cerca de las grietas al subir desde (0,13).
GetPlayerSpeed y bikeFrameCounter observados con GDB: llegar a un giro con
contador2/velocidad3 conserva el impulso; detenerse reinicia el contador.
No hubo excepcion nativa. No se modifica la fisica ni el callback del suelo.

Replay r05-broken-floor-crossing PASS; Continue r05-sky-pillar-3f-mach PASS,
guardado intacto. Captura privada r05-sky-pillar-3f-mach.png en build/.
La repeticion arranca de Continue en frame2000, con pulsos solo hasta1800;
fallos de control, cambio inesperado de mapa y deadline son aserciones.
Queda resolver 4F, preparar el nuevo intento de Liga y completar R05; T27
sigue abierto. No hay cambios nativos ni nuevos parches upstream.

## T27 R05: puzzle de 4F, caida central y llegada a 5F

Desde el checkpoint 3F se desmonta por Bag y se sube por (11,1). Bici en
4F(12,2), recorrido continuo (12,6)->(10,6)->(10,12)->(3,12)->(3,4)->(4,4).
Al soltar la direccion, la inercia termina rompiendo el suelo en (6,4): el
script original hace caer a 3F(6,4), plataforma central inaccesible caminando.
La escalera (7,1) vuelve al centro de 4F y (3,1) lleva a 5F(3,2).
No se cambia ningun tile, warp, posicion, callback ni velocidad por GDB.

Replay r05-upper-floor PASS y Continue r05-sky-pillar-5f-mach PASS, save
intacto. Capturas privadas de la caida central y 5F bajo build/natural-campaign/.
Un intento por la columna13 quedo contra el muro13,3 y fallo por deadline del
helper; el recorrido correcto usa columna12. No es bloqueo ni excepcion del
juego y no requiere parche nativo. Captura de Rayquaza/final aun no acreditan
R05; se verifican en el siguiente incremento. T27 sigue abierto.

## T27 R05: captura natural de Rayquaza nivel70 con Master Ball

Desde 5F se sube por (10,1) a SkyPillar_Top y se llega a (14,7) andando.
La conversacion mirando arriba inicia BattleSetup_StartLegendaryBattle.
El helper selecciona Bag/Poke Balls/Master Ball, conservando las reglas del
combate. Outcome7, equipo5->6, especie406/nivel70/PokeBall1 y HP240/240.
La Master Ball obtenida por UI en el escondite Aqua pasa1->0. No se crean
Pokemon ni se conceden objetos, niveles, movimientos o resultados con GDB.

Replay r05-rayquaza-catch PASS y Continue r05-rayquaza-caught PASS; save
sin cambios. Se comprueban especie, nivel, movimientos, objetos equipados,
medallas y cantidades de inventario tras la recarga. Capturas antes/despues
privadas en build/natural-campaign/. No hubo excepcion nativa.
La captura habilita una nueva preparacion legal para Liga, pero no acredita
las victorias pendientes. R05, R06-R15 y Checkpoint E siguen abiertos.

## T27 R05: regreso preparado a Liga, Sidney/Phoebe y derrota ante Glacia

Rayquaza se pone primero mediante Pokemon/Switch. Fly a Mossdeep, Mart real:
compra de tres Hyper Potions por3600 (dinero4742->1142), enfermera del Centro,
Fly a EverGrande(18,6) y enfermera de Liga. Entrada por (9,1) al Hall5 y su
puerta (5,2) al cuarto de Sidney. No se conceden dinero, objetos ni curaciones.
Replay r05-rayquaza-league-prep PASS y r05-rayquaza-sidney PASS.
Sidney: outcome1/flag4FB1, dinero6042, tres pociones conservadas, Rayquaza92HP.

Puertas originales de Sidney/Hall1 a Phoebe: outcome1/flag4FC1, tres Hyper
Potions consumidas y dinero11142. Replay r05-rayquaza-phoebe y Continue de
r05-rayquaza-phoebe-win PASS, save intacto. El combate no se omite ni se
alteran movimientos, PP, enemigos o resultados. Se conserva ese checkpoint
antes de seguir: una derrota posterior no borra la evidencia de esta victoria.

El intento siguiente termina en derrota normal ante Glacia: outcome2, regreso
a EverGrande(18,6), dinero11142->5571 y flags temporales4FB-4FE todos0.
Ocho medallas y Rayquaza70 siguen presentes. Ya no habia Hyper Potions al
iniciar ese tramo; quedan pendientes preparacion y estrategia para ganarlo.
No es una excepcion ni espera infinita del host. El proceso principal sale
normalmente desde su checkpoint de frame127732. R05 NO esta completo: Glacia,
Drake, Wallace, creditos y Hall of Fame naturales siguen pendientes.

Pruebas finales: ejecutables normal/diagnostico, 21 suites host y verify-normal
PASS; ARM Binutils2.43.1, make compare -> pokeemerald.gba: OK. Sin cambios
en upstream ni nuevos parches. ROM SHA1 f3ae088181bf583e55daf962a92bb46f4f1d07b7
y save original SHA256 b5a41c3758763bbec72769fab4a2533bf2db0b6312d93d25a695f9e4b9e02260
sin cambios. Capturas/checkpoints/replays privados bajo build/. Sin push.

La primera repeticion exploratoria de Glacia produjo outcome1, mientras la
prueba esperaba2: fallo una asercion del harness, sin guardar esa victoria.
No se presenta ese intento como checkpoint verificado. El runner ahora
registra el desenlace real (1 o 2) y valida los flags correspondientes; no
fuerza RNG ni resultados. Las repeticiones nuevas conservan los logs, guion,
inputs y save anteriores en history/<timestamp>/ dentro del scratch privado.
La conservacion de bytes y dos archivos sucesivos se verifico con fixtures
temporales propios. Ese intento exploratorio quedo sin checkpoint; la repeticion final se verifica abajo.


## T27 R05: victoria guardada sobre Glacia y Continue

La repeticion final desde el mismo guardado natural r05-rayquaza-phoebe-win
gana a Glacia: outcome1, flags Sidney/Phoebe/Glacia=1, Drake=0 y game_clear=0.
El runner registra el desenlace real; no modifica RNG, enemigos, objetos ni
progreso. El intento previo perdido permanece como evidencia independiente.
Replay r05-rayquaza-glacia PASS; checkpoint r05-rayquaza-glacia-win guardado
en build/natural-campaign/ y Continue --continue-until1181 PASS, save intacto.
Este es el punto de continuacion actual. Drake, Wallace, creditos y Hall of
Fame siguen pendientes; R05, R06-R15, T27 y Checkpoint E no se cierran.
Capturas, saves y logs siguen privados en build/. No hay push de estos cambios.


## T27 R05: derrota ante Drake y reabastecimiento natural

Desde r05-rayquaza-glacia-win se cruzan Glacia/Hall3/Drake por las puertas
(6,2)/(5,2) y se inicia el combate por dialogo. El intento termina en outcome2:
EverGrande(18,6), dinero16442->8221, ocho medallas conservadas y flags del
Alto Mando reiniciados. No hay excepcion nativa. Replay r05-rayquaza-drake PASS;
checkpoint r05-rayquaza-drake-loss y Continue --continue-until1181 PASS.
La inspeccion de los recursos del guardado anterior muestra Rayquaza0/240PS,
los otros cuatro companeros debilitados y Swampert73/188PS: el checkpoint
prueba una victoria sobre Glacia, pero deja un equipo agotado para Drake.

Desde ese blackout se vuela a Mossdeep y se compran cuatro Hyper Potions
(4800) y dos Revive(3000): dinero8221->421. Enfermera real, Fly de regreso y
puertas normales hasta Sidney. No se conceden dinero, objetos, PP ni PS por
el debugger. Replay r05-league-restock PASS y Continue del checkpoint
r05-league-restocked PASS. Los nuevos intentos usan las medicinas mediante
Bag/Use/seleccion del Pokemon, con verificaciones de consumo y PS.

Verificacion de esta continuacion: normal/diagnostico, 21 suites host y
verify-normal PASS; make compare -> pokeemerald.gba: OK. ROM legal SHA1
f3ae088181bf583e55daf962a92bb46f4f1d07b7 y save del usuario SHA256
b5a41c3758763bbec72769fab4a2533bf2db0b6312d93d25a695f9e4b9e02260 intactos.
Upstream no se modifica; evidencias y capturas permanecen privadas en build/.


El segundo recorrido desde r05-league-restocked vuelve a ganar Sidney,
Phoebe y Glacia, pero pierde ante Drake de forma normal. Se conservan todos
sus checkpoints con prefijo r05-league-retry-; no sustituyen la evidencia
del primer recorrido. Las Hyper Potions usadas fuera del combate restauran
Rayquaza158->240 y154->245PS y descuentan una unidad por uso; el resto se
consume durante las peleas. Al llegar a Drake quedan Rayquaza47/245PS y
0PP de Outrage, Fly5PP, ExtremeSpeed5PP, Rest10PP; Pelipper47 y Swampert53
estan sanos. Quedan dos Revive sin consumir. No es un bloqueo del host:
la politica automatica solo elige ataques y no aprovecha Rest o Revive.
Drake, Wallace y el final de R05 continuan pendientes.


## T27 R05: recursos verificados, Rest/Revive y cosecha de Leppa

El replay r05-drake-rest selecciona Rest por teclado cuando Rayquaza tiene
pocos PS y usa los dos Revive comprados al debilitarse. Tambien acaba en
derrota normal, outcome2; no se cambia el juego para ganar. Los nuevos
checkpoints incluyen PS/maximos, estado, PP por movimiento y cantidades de
Revive/Leppa. Continue compara esos valores cuando estan presentes, con
compatibilidad para checkpoints anteriores sin estos campos.

Desde el blackout, Fly a Rustboro y conexion real a Route104. El dialogo
del arbol(36,6), abordado desde(36,7), entrega dos Leppa: cantidad0->2.
Luego compra de tres Hyper Potions y dos Revive por6600, enfermera real y
regreso hasta Sidney: r05-leppa-prep PASS. Checkpoint r05-league-leppa-ready
y Continue PASS, incluyendo PS/PP/estado e inventario de ambas medicinas.

El primer recorrido desde esa preparacion gana Sidney/Phoebe/Glacia. Sin
embargo, la politica gasta ambos Revive contra Glacia y Rayquaza queda
sin PS; una asercion de recursos detiene el harness antes de Drake. No es
una excepcion del ejecutable ni una victoria de Liga. Se conserva el log.
Se retoma r05-leppa-phoebe-win (Continue con recursos PASS), reservando
Revive para Drake y evitando Rest frente a movimientos de hielo conocidos.
El primer arranque de esta continuacion reabre dialogo por demasiados
pulsos A de Continue; el harness lo detecta antes de usar objetos. Se corrige
ese guion para terminar las pulsaciones en1181, sin modificar el juego.
Los logs previos quedan archivados en history/ dentro del scratch privado.


Prueba aislada r05-leppa-use PASS: Mochila/Berries/Use, Rayquaza y su cuarto
movimiento seleccionados por teclado. Leppa2->1 y Enfado8->15PP; el limite
se calcula con los PP maximos del movimiento y sus bonus, no se asume10.
Checkpoint r05-phoebe-leppa-restored y Continue PASS con PS/estado/PP y
ambas cantidades de consumibles intactos. La captura privada muestra la
sala de Phoebe, el jugador y el NPC visibles tras volver del menu.
El intento r05-leppa-finish corregido pierde ante Glacia normalmente;
no acredita completar el Alto Mando. Se conserva para reproduccion.


## Cierre de este incremento T27: limites y siguiente preparacion

r05-leppa-precharged vuelve a perder ante Glacia; recuperar PP por si solo
no resuelve la debilidad a hielo. r05-glacia-ground-lead cambia realmente
Swampert del slot5 al primero mediante Pokemon/Switch, pero tambien acaba
en outcome2. Sus ataques quedan registrados en battle-choices.jsonl, ahora
tanto para combates individuales como dobles. No se modifican stats, tipos,
enemigos, movimientos ni resultados para aprobar el recorrido.

Checkpoint exterior mas reciente: r05-glacia-ground-lead-loss, frame53764,
EverGrande(18,6), dinero5630, Swampert54 primero, Pelipper49 y Rayquaza71 en
slot5; Hyper Potions0, Revive2 y Leppa1. El equipo queda curado por el blackout
y los cuatro flags del Alto Mando vuelven a0. La recarga final comprueba
mapa, orden del equipo, PS, estados, PP, inventario, dinero y eventos.
El checkpoint previo r05-phoebe-leppa-restored conserva Enfado15PP y la
victoria de Phoebe; los checkpoints anteriores de Glacia siguen intactos.
Ninguno acredita una victoria sobre Drake ni la Liga completa.

Siguiente trabajo: preparar cobertura electrica y mas curacion mediante
obtencion/compra/ensenanza reales, luego repetir Glacia/Drake/Wallace desde
la misma partida. No seguir repitiendo la misma estrategia agotada. R05,
R06-R15, T27 y Checkpoint E permanecen abiertos. Este incremento cambia
solo helpers y documentacion; el codigo del juego y los parches no cambian.

Continue final de r05-glacia-ground-lead-loss: PASS; save sin reescribir.


## T27: New Mauville, recarga antes de asignar fondos (17-10-2026)

La campaña obtuvo la Llave del Sotano de Wattson, cruzo New Mauville con
Surf y sus interruptores, recogio Escape Rope/Full Heal y apago el generador
(var 0x40BA=2). Continue desde ese save revelo un fallo real del host:
`DrawMetatile` escribia con EAX=0 durante `RunOnLoadMapScript`, invocado desde
`InitMapFromSavedGame`. El script solicita `DrawWholeMapView` antes de
`InitOverworldBgs`; los tres buffers de fondos seguian siendo NULL.

El parche 0048 agrega una comprobacion solo PORT_PC a DrawWholeMapView.
Las modificaciones del mapa se conservan; el dibujo normal posterior a la
asignacion de fondos las presenta. No cambia el comportamiento GBA.

Validacion: normal/diagnostico, 21 suites y verify-normal PASS
(`build/t27-new-mauville-fixed-host.log`); ARM Binutils 2.43.1,
`make compare` -> `pokeemerald.gba: OK`
(`build/t27-new-mauville-fixed-gba.log`). Continue conserva posicion, equipo,
PS/PP/estados e inventario; los tres buffers estan asignados y la captura
muestra suelo, jugador y generador (`build/t27-new-mauville-generator-off-verified-reload.log`).

Reproduccion: clon local del commit fijado + 48 parches mediante git am;
arbol upstream d912ff84e88b58409e8c3eb5d97e24718ca08f33 identico. field_camera.c
compilado desde ese clon genera objeto identico al del build actual
(SHA256 f80c66ae887e54fd4039868a11dae6957e6cbd599ea203433f7a9663b886e670).
Se reenlazo el diagnostico sustituyendo ese objeto y se repitio Continue PASS;
los demas objetos/assets existentes fueron reutilizados: no fue una
recompilacion integral desde cero. Evidencia privada:
`build/t27-new-mauville-clean-relink-reload.log` y directorio
`build/t27-new-mauville-clean/`. ROM, saves y capturas permanecen ignorados.


## T27: cobertura electrica obtenida sin conceder progreso (17-10-2026)

Wattson entrego la Llave del Sotano por dialogo. Se entro a New Mauville
con Surf y la llave, se resolvieron los interruptores por desplazamiento,
se recogieron Escape Rope y Full Heal y se apago el generador. Continue
conserva var 0x40BA=2; el parche 0048 corrige la recarga descrita en
first-run-report.md. Se consumio Escape Rope por Bolsa y se regreso a Wattson:
regalo TM24, flag 0xD1 y aprendizaje de Rayo por menu verificados; TM consumida.
Rayquaza conserva Vuelo/Rayo/Velocidad Extrema/Enfado; no se concedieron
movimientos, dinero, objetos, experiencia ni flags desde GDB.

Se compraron cuatro Hiper Pociones (4800, saldo 5630->830), se curo el equipo
y se volvio a la Liga por Fly/puertas reales. El replay r05-thunderbolt-league
vence a Sidney (frame27448), Phoebe (49216), Glacia (75544) y Drake (95920).
Save de Drake (96952): cuatro flags del Alto Mando=1, game-clear=0,
Rayquaza72 PS75/249, PP12/12/5/2; dos Revivir, Full Heal1, Leppa1,
saldo21630. Continue de Drake PASS, incluida integridad PS/PP/estado/inventario.
Se uso la ultima Leppa por Bolsa (Enfado2->12PP) y se guardo delante de Wallace
(Hall4,5,3). Esto no acredita aun victoria sobre Wallace ni el final.

Replays PASS: r05-new-mauville-key/entry/generator/reward,
r05-thunderbolt-league-prep/league y r05-champion-door. Evidencia y capturas
privadas en build/natural-campaign/ y build/natural-campaign-replay-r05-*;
resumenes build/t27-thunderbolt-league-replay.log,
build/t27-thunderbolt-drake-win-reload.log y build/t27-champion-door-replay.log.
R05 sigue abierto; R06-R15 y Checkpoint E siguen abiertos.


## T27: final natural y cierre de R05 (17-10-2026)

Desde r05-wallace-door-ready, la entrada real a la sala inicia el combate
contra Wallace. La observacion de CB2_EndTrainerBattle registra outcome1;
ningun resultado, objeto, experiencia o flag se escribe desde el debugger.
Se usan los menus para movimientos/cambios y los Revivir adquiridos antes.
Dos ejecuciones llegan al Hall of Fame. La segunda verifica el registro de
los seis miembros y continua sin pulsaciones durante los creditos hasta
Task_CreditsTheEnd6: The End capturado en frame68624.

Equipo del Hall of Fame: Rayquaza73, Pelipper52, Gloom21, Castform25,
Tentacool18 y Swampert54. Ocho medallas y game-clear=1. Capturas y saves
privados: build/natural-campaign/r05-hall-of-fame.* y r05-the-end.*.
La captura del Hall of Fame muestra al entrenador, su equipo y
LEAGUE CHAMPION / CONGRATULATIONS. La pantalla final coincide en los
38400 pixeles con una referencia derivada de las tablas originales de
letras, sus flips y los graficos/paleta generados por GBA (expansion RGB5).
Una sospecha visual inicial de trazos ausentes no se confirma: 0 diferencias
(build/t27-the-end-reference-check.json); no se hizo ningun cambio por ella.

Otro proceso carga ese save mediante Continue: dormitorio de Brendan 2F,
control de campo libre, ocho medallas, game-clear y seis especies/niveles
conservados. LoadGameSave(SAVE_HALL_OF_FAME) devuelve SAVE_STATUS_OK y los
seis registros persistidos coinciden. El save queda identico byte a byte.
No hubo una nueva excepcion del host en el tramo del Campeon/final.

Reproduccion MINGW32, con los checkpoints naturales previos en build/:
python port/tests/natural_campaign_smoke.py --phase r05-wallace-champion
Conservar r05-hall-of-fame y r05-the-end en build/natural-campaign/ y ejecutar:
python port/tests/natural_ending_reload.py
Logs: build/t27-wallace-champion-replay.log,
build/natural-campaign-replay-r05-wallace-champion/campaign.log,
build/t27-natural-ending-reload.log y build/natural-campaign-ending-reload/reload.log.

R05 completo; T27 y Checkpoint E siguen abiertos. Siguiente cobertura:
R06 (crianza/huevo/eclosion natural), despues Safari y Battle Frontier
R07-R14, y los gates finales R15. Los fixtures preparados anteriores no
sustituyen estos criterios. Normal/diagnostico y 21 suites PASS; GBA compare
OK con ARM Binutils2.43.1, como consta en los logs del parche0048.


## T27 / R06 completo: huevo y eclosion naturales (21-10-2026)

La partida procede del Hall of Fame ganado en R05. Se compraron 20 Poke Balls,
se deposito Gloom hembra y se capturo Oddish macho13 mediante Bolsa/huida.
La pareja real Gloom/Oddish tiene compatibilidad20. Los padres se dejaron por
UI y el huevo aparecio con pasos del padre4->2560, personalidad1496255074 y
flag pendiente0->1. No se invocaron rutinas para producir huevos ni se
escribieron readiness, pasos, especie, experiencia o personalidad desde GDB.

Se entro/salio de la guarderia para que el script colocara al cuidador fuera,
y se recogio el huevo por dialogo. Equipo5->6, especie43, is_egg=1, ciclos20,
personalidad1496255074; pending y offspring se limpian mediante el script.
Despues se recorrieron 5375 pasos medidos por el contador materno2677->8052.
Los ciclos bajan por el juego; la animacion y el texto ODDISH hatched from
the EGG aparecen. Oddish hembra5 conserva su personalidad, is_egg pasa a0,
friendship=120 y no es Bad Egg. Regreso al campo y guardado en Route117(53,6).
Mientras se caminaba, los padres generaron un segundo huevo pendiente; se
conserva ese estado normal, sin confundir su personalidad2442798564 con la
del primer huevo ya eclosionado.

Cuatro Continue en procesos nuevos PASS: madre depositada, huevo pendiente,
huevo recogido y Oddish nacido. Se comparan padres/identidades/pasos,
compatibilidad, pending/offspring/contador y especie/nivel/genero/personalidad/
is_egg/friendship-ciclos de todo el equipo, ademas de PS/PP/movimientos/estado,
inventario, dinero y progreso. Cada recarga deja el archivo save intacto.
No aparecio una excepcion nativa: solo se ajustaron rutas y simbolos del
harness. No hace falta parche0049; los 48 parches existentes no cambian.

Evidencia privada: build/t27-r06-{daycare,mother,father-catch,generate,receive,hatch}.log;
build/t27-r06-{mother,pending,received,hatched}-reload.log.
Checkpoints en build/natural-campaign/r06-*. Capturas PNG de
r06-hatch-animation y r06-oddish-hatched bajo ese mismo directorio, fuera de Git.
Reproduccion MINGW32, con los checkpoints previos obtenidos naturalmente:
python port/tests/natural_campaign_smoke.py --phase r06-daycare
Continuar con --phase r06-mother, r06-father-catch, r06-generate, r06-receive y
r06-hatch; conservar sus checkpoints en build/natural-campaign/ entre fases.
python port/tests/natural_campaign_reload.py r06-oddish-hatched --continue-until 1181

Normal/diagnostico, 21 suites y verify-normal PASS (build/t27-r06-host.log).
ARM Binutils2.43.1, make compare -> pokeemerald.gba: OK (build/t27-r06-gba.log).
R06 completo. T27/Checkpoint E siguen abiertos para R07-R15; el siguiente
recorrido es Safari por bolas agotadas y por 500 pasos reales.


## T27 / R09: fallo real al abrir alquileres de Fabrica (22-10-2026)

Admision por recepcionista, Nivel50 y guardado originales llevan a
CB2_InitSelectScreen. SIGSEGV en 0x100af91f: movzbl 0x6(%eax),%eax,
con EAX=0. sFactorySelectScreen esta a NULL antes de Select_InitMonsData
(case5); los cases2/4/5 consultan fromSummaryScreen antes de asignarla.
Upstream ya tiene comprobaciones bajo UBFIX, pero PORT_PC solo habilitaba
SAFE_DIV, no todos los UBFIX de C.

Parche0049 habilita esas tres comprobaciones con
#if defined(UBFIX) || defined(PORT_PC). No habilita globalmente UBFIX
ni altera GBA. Pantalla de alquileres CB2_SelectScreen: replay PASS.
Normal/diagnostico compilan; make compare -> pokeemerald.gba: OK
(build/t27-r09-host-build.log, t27-r09-gba.log).

Clon limpio del commit fijado +49 parches por git am: arbol
1bd153153472fc30461897998ef4ea2d62ec478e identico. battle_factory_screen.c
compilado en ese clon produce objeto identico SHA256
7709c41c996230c23cc8c3d1aeddbb2b1510fb8028855e10c5b3f16cf70903af.
Reenlace sustituyendo ese objeto y nueva entrada por UI PASS
(build/t27-r09-clean-entry.log). Se reutilizan headers/recursos generados
y los demas objetos; no se afirma una reconstruccion integral desde cero.
R09 sigue abierto: esta prueba aun no selecciona alquileres ni intercambios
ni completa la ronda. Evidencia previa SIGSEGV en history/ del replay;
los siguientes fallos se registraran al continuar desde esta pantalla.
