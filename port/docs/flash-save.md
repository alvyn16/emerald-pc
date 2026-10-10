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

## Guardado del juego y recuperación — T06

Desde MINGW32, después de preparar `wild_battle_smoke.py`:

```sh
make -C port exe diagnostic-exe
python port/tests/save_game_smoke.py
```

El fixture aislado prepara Torchic nivel 5, 7 pociones, dinero y una variable
de progreso mediante GDB. Abre el menú real y confirma sus diálogos con A.
Guarda dos veces (contador 1, dinero 12.345, variable 1; contador 2,
dinero 23.456, variable 2). Al cerrar y reabrir otro proceso comprueba mapa
0.9, especie, equipo, cantidad de objetos, dinero, flag de Pokémon recibido
y variable. Recalcula los checksums de los 14 sectores de cada slot usando
sus tamaños leídos de la tabla del binario. No es una partida del usuario.

Resultados PASS en `build/save-game-regression/`:

- Reapertura selecciona contador 2 y sus campos.
- Checksum alterado o ID 0xffff en el slot reciente: estado ERROR (255),
  con recuperación del contador 1 y sus campos.
- Tercer guardado interrumpido antes del quinto sector mediante GDB kill,
  sin ejecutar el cierre host: recupera contador 2 y sus campos.
- Tamaño incorrecto y archivo de solo lectura: arranque devuelve 1 con
  causa explícita antes de crear ventana; contenido intacto.
- Suite flash: propietario exclusivo (error 32), solo lectura (error 5),
  tamaño incorrecto y operaciones sin buffer disponible rechazan escrituras.

0021 valida los IDs antes de indexar `locations` y calcular el checksum;
mantiene el comportamiento GBA. Compare OK, árbol de los 21 parches idéntico
en el checkout de reproducción: `7116809b753c1bd8c6d1279c5db8a88ac2c68edc`.
`--reload-only` reutiliza los dos slots y tamaños ya preparados en build/
para repetir fallos de carga sin recorrer otra vez la partida nueva.

### Garantías y límites

No se hace un reemplazo atómico del archivo completo: Emerald alterna y
valida dos slots, el backend trabaja sobre el mapeo. FlushViewOfFile fuerza
el mapeo por sector; FlushFileBuffers se llama al cerrar. Los retornos del
flush por sector se propagan como error; los del cierre no se comunican al
juego. El byte final de firma puede esperar al cierre/flush posterior.
Estas pruebas cubren cierre limpio y terminación durante sectores, no cortes
eléctricos, disco lleno, fallos físicos ni interrupción en cada byte de firma.
Una escritura rechazada al abrir no equivale a una falla de disco a mitad
del guardado. Reset real tras los dos saves completos PASS en T07 (`reset.md`).

El save original conserva SHA-256
`B5A41C3758763BBEC72769FAB4A2533BF2DB0B6312D93D25A695F9E4B9E02260`.
