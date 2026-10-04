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
