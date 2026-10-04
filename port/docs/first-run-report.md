# Primera ejecución de `emerald-pc.exe` i686

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
la región de ROM/RTC `0x08000000` no está mapeada. Ese es el primer fallo
actual. La ROM legal del usuario permanece intacta en `roms/`; ninguna ROM,
asset ni dato extraído se incorporó al ejecutable o al repo. El PPU y el
audio no están implementados; el renderer permanece negro y m4a usa stubs
silenciosos. El diagnóstico no presupone que mapear RTC baste para ejecutar
el juego completo: flash/guardado e interrupciones siguen sin emulación.
