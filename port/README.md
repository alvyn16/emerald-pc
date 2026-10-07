# Capa de portabilidad

Código propio del host i686: memoria GBA, ROM del usuario, flash persistida
en `saves/`, BIOS parcial, DMA inmediato, VBlank cooperativo y renderizador
SDL2 de modos 0, 1 y 2 con fondos de texto, fondos afines y sprites regulares
y afines, con máscaras WIN0/WIN1 para fondos, objetos y efectos de color.
El PPU mezcla las dos capas superiores mediante BLDCNT, BLDALPHA y BLDY.
El audio sigue silenciado. La ventana de objetos, el mosaico y DMA por
HBlank faltan.

Compilar desde MINGW32: `make -C port exe`. El diagnóstico de la primera
ejecución y el siguiente fallo están en `docs/first-run-report.md`.
El menú de velocidad se abre con P y permite elegir entre 1× y 4×.
