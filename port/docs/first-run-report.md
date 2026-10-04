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
