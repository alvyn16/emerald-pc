# Capa de portabilidad

Código propio del host i686: memoria GBA, ROM del usuario, flash persistida
en `saves/`, BIOS parcial, DMA inmediato, VBlank cooperativo y renderizador
SDL2 de modo 0 con fondos de texto y sprites regulares. El audio sigue
silenciado. Modos afines, ventanas, mezcla y DMA por HBlank faltan.

Compilar desde MINGW32: `make -C port exe`. El diagnóstico de la primera
ejecución y el siguiente fallo están en `docs/first-run-report.md`.
