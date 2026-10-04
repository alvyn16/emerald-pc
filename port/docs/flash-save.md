# Backend de flash PC (hito 4)

`port/host_flash.c` usa un archivo mapeado de Windows de **131.072 bytes**
como buffer de 32 sectores de 4 KiB. La ruta de producción es
`saves/emerald-pc.sav` en la raíz del proyecto; `saves/` está ignorado por
Git. Un save nuevo se llena con `0xFF`; si existe otro tamaño, se rechaza sin
truncarlo. El programa no abre la ROM para escritura ni usa direcciones
`0x0E000000`.

El parche upstream `0004` conserva la ruta GBA bajo `#else`. En `PORT_PC`,
`IdentifyFlash` asigna las funciones host a `ProgramFlashByte`,
`ProgramFlashSector`, `EraseFlashSector` y `EraseFlashChip`, y declara el
descriptor de 128 KiB `MX29L010` como flash presente. `ReadFlash`,
`VerifyFlashSector` y `VerifyFlashSectorNBytes` operan directamente sobre
el buffer mapeado; `ReadFlashId` devuelve el ID sin comandos de hardware.

La programación por byte permite cambiar bits de 1 a 0 y rechaza un intento
de volverlos a 1 sin borrar. Borrar sector/chip y programar un sector completo
fuerzan un flush del mapeo. La programación por byte hace flush cada 256
operaciones y al cerrar el proceso. El archivo mantiene el formato bruto de
flash Emerald de 128 KiB; no se distribuye ningún `.sav`.

Prueba reproducible desde MINGW32, con `build/` ya creado:

```sh
gcc -std=gnu11 -Wall -Wextra -Werror -DMODERN=0 -DPORT_PC \
  -iquote pokeemerald/include -Iport \
  port/host_flash.c port/tests/host_flash_test.c \
  -o build/host-flash-test-i686.exe
build/host-flash-test-i686.exe
```

Resultado medido: `host flash read/write/erase/persistence OK`. La prueba
usa y elimina solo un `.sav` temporal de `build/`; no toca el save de
`saves/`.
