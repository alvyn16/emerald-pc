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
