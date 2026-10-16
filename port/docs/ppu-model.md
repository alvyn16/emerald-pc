# PPU: verificación T14–T17

Implementación propia en port_ppu.c; no copia código ni tablas del juego.

| Capacidad | Vectores propios y límites |
| --- | --- |
| Modos 3/4 | RGB555 / índice de paleta; páginas; primer/último píxel; BG2 afín; color cero opaco en 3 e índice cero transparente en 4. |
| Modo 5 | 160×128 RGB555, páginas 0/0xa000, borde final 0x13ffe, coordenadas negativas y fuera de bitmap como backdrop. Wrap ignorado en bitmap. |
| OBJ bitmap | Tiles <512 no disponibles; 512 permitido. Prioridad, ventanas y mezcla se conservan. |
| Prioridad | OAM antes de prioridad BG; OBJ ocultos no son segunda capa. Empates BG por número, OBJ gana empate con BG. |
| Ventanas/mezcla | WIN0>WIN1>OBJWIN, bordes invertidos, máscaras de efectos, alfa de OBJ sobre segunda capa inmediata, no búsqueda de una tercera capa objetivo. Forced blank. |
| Afines/mosaico | Coordenadas signed, matrices negativas, caja doble, wrap, mosaico anclado a pantalla antes de flips, clipping y grupo parcial inicial/final. |
| Writes de referencia | BG2/BG3 X/Y recargan acumulador aunque el valor escrito sea idéntico. Hooks de gpu_regs/scanline (0029) y DMA; cambios PA/PB/PC/PD afectan la siguiente línea. Acumulación envuelve a 28 bits. |

Suites: ppu, bitmap, ppu_priority y ppu_affine. Antes de las correcciones,
`build/t16-before.log` reproduce el orden OAM incorrecto y
`build/t17-before.log` la fila perdida de mosaico con origen (3,3).
La revisión añadió flips y matriz OBJ negativa, tamaños normales/dobles y
notificación de un write idéntico entre líneas.

Referencias: [GBATEK LCD](https://rust-console.github.io/gbatek-gbaonly/),
[mosaico OBJ mGBA](https://github.com/mgba-emu/mgba/blob/master/src/gba/renderers/software-obj.c),
[mosaico vertical mGBA](https://github.com/mgba-emu/mgba/blob/master/src/gba/renderers/video-software.c).
Son referencias de comportamiento, no código incorporado al proyecto.

## Comparación de escenas locales

Harness: `python port/tests/visual_smoke.py`, GDB MINGW32 y Pillow.
Los assets, ROM, saves, dumps y PNG se guardan solo en build/.
El inicial se abre mediante CB2_ChooseStarter después de un recorrido nuevo
aislado; no se declara comprobado todo su evento de historia.

Para aislar el renderizador, se enlazó su versión de 43b2d72 con el resto
de la plataforma actual. Su hook nuevo NotifyWrite es un no-op local, igual
que la ausencia de observación en esa versión. Ese binario de comparación
vive en build/visual-before-renderer/, nunca sustituye al ejecutable normal.
Ambos usan idénticos BIOS, IRQ/timers, input, datos y frame diagnóstico.

| Escena alineada | Antes/después | Observación |
| --- | ---: | --- |
| Intro 2400, mismos registros BG2 y frame | 0 píxeles distintos | Kyogre estilizado durante transición, con efecto de color. |
| Intro 2665, mismos registros y frame | 0 | Flash blanco en esta fase; no confundir con fallo de ejecución. |
| Confirmación Torchic 30800, CB2_StarterChoose y registros iguales | 0 | Pokémon centrado en círculo, texto y menú YES/NO. |
| Batalla 31300, mismo fixture Ruta 101/Poochyena | 0 | Entrenador, Pokémon y ventana visibles; captura durante aparición. |
| Regreso a mapa 37000, victoria 33365 | 0 | Sin regresión visual detectada en este checkpoint. |

Capturas en build/visual-before/, build/visual-after/,
build/visual-before-battle/ y build/wild-battle-regression/.
Los fallos corregidos son demostrados por fixtures combinados; estas escenas
concretas no activan sus casos extremos. No es una comparación contra píxeles
de una GBA o emulador de referencia, y no prueba fidelidad de todas las escenas.

## Límites

No se encontraron consumidores C explícitos MODE_3/4/5: no se afirma que
Emerald use los tres modos. Su verificación es sintética. Quedan pendientes
comparaciones hardware, scanline timing de instrucciones nativas, límite de
tiempo de dibujo OBJ, open bus y modos prohibidos 6/7. El calendario por línea
y DMA HBlank visible están implementados, sin emulación de CPU ARM.

## T27: niebla submarina y OBJ semitransparentes dentro de ventanas

La captura real de Underwater_Route128 ocultaba el terreno bajo niebla opaca.
En frame 10000: DISPCNT=0x7F60, WININ=0x1F1F, WINOUT=0x0101,
BLDCNT=0x1E40 y BLDALPHA=0x1004. WIN0 cubre la pantalla, pero su bit de efectos
esta apagado. El resolvedor aplicaba ese bit tambien al alfa forzado de OBJ.

Un OBJ semitransparente conserva su alfa forzado cuando ese bit esta apagado;
los efectos normales de BG/OBJ siguen dependiendo de la mascara de ventana.
Referencia de comportamiento: [mGBA, seleccion del primer objetivo OBJ](https://github.com/mgba-emu/mgba/blob/master/src/gba/renderers/software-obj.c#L145).
Se corrigio la condicion de ResolvePixels en la implementacion propia.

La prueba sintetica ahora exige alfa dentro de WIN0 y fuera con ambos bits
de efectos apagados. Incluye los registros de la escena submarina y comprueba
EVA=4/EVB=16 sobre colores conocidos. El binario anterior falla esa asercion
(t27-fog-before-fix-test.log); con la correccion pasan las 21 suites, builds
normal/diagnostico y verify-normal (t27-fog-host-build.log).

La recarga privada del mismo save produce capturas de antes/despues en
build/underwater-before-color-fix.png y build/underwater-after-color-fix.png:
antes solo se veia la niebla gris; despues se distinguen las rocas, la entrada
y el fondo azul/violeta. Los 1024 bytes de registros IO coinciden entre ambas
capturas, y el save permanece sin cambios. Logs t27-underwater-visual*.log.
El checkout de reproduccion con los 45 parches y las fuentes propias actualizadas
pasa ambos builds y 21 suites (t27-fog-clean-build.log). GBA sigue dando
pokeemerald.gba: OK (t27-fog-gba-compare.log).
