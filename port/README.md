# Capa de portabilidad

Código propio del host i686: memoria GBA, ROM del usuario, flash persistida
en `saves/`, BIOS parcial, DMA inmediato/HBlank/VBlank, temporizadores,
reinicio suave y renderizador
SDL2 de modos 0–5 con fondos de texto, fondos afines y sprites regulares
y afines, con máscaras WIN0/WIN1/OBJWIN para fondos, objetos y efectos de color.
El PPU mezcla las dos capas superiores mediante BLDCNT, BLDALPHA y BLDY.
El renderizado se realiza por línea e incluye mosaico. El secuenciador
m4a upstream utiliza un motor host propio para PCM y PSG, con salida SDL2.
No se busca precisión por ciclo; las limitaciones se detallan en el README
principal y en `docs/milestones-13-19-review.md`.

Compilar desde MINGW32: `make -C port exe`; ejecutar las 21 suites host:
`make -C port test`. El diagnóstico de la primera
ejecución y el siguiente fallo están en `docs/first-run-report.md`.
El menú de velocidad se abre con P y permite elegir entre 1× y 4×.

El ejecutable para jugar es `build/emerald-pc.exe`; las pruebas usan
`build/emerald-pc-diagnostic.exe` y guardados separados. Para construir y
comprobar esa separación: `make -C port diagnostic-exe verify-normal`.

La campaña continua tiene ocho medallas y victorias sobre Sidney/Phoebe/Glacia;
T27 sigue abierto. Estado y límites: [campaña](docs/campaign-progress.md) y
[cobertura pendiente](docs/tasks/t27-remaining.md).

Los nuevos checkpoints de campaña registran PS, estados, PP y consumibles;
Continue comprueba esos valores. Los helpers usan medicinas y bayas por
los menús reales del juego, sobre copias privadas del guardado de diagnóstico.
