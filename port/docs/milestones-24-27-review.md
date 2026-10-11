# Revisión y cierre de T11–T18

Fecha: 2026-10-11. Base revisada: e1ff772. Código hasta 6e73f5b;
documentación posterior sin cambios ejecutables. Ramas locales por hito;
publicación no solicitada en este incremento.

## Revisión por cinco ejes

| Eje | Resultado |
| --- | --- |
| Correctitud | Revisión de fases/IRQ, enable/reload, máscaras DMA, selección de capas, wrap afín y extremos BIOS. Se corrigieron fallos reproducibles; gates abajo PASS. |
| Lectura | Helpers comunes para destino DMA y matriz BIOS; contratos de writes y precisión documentados. No se duplicó una implementación de BIOS/upstream. |
| Arquitectura | Dispositivos y PPU en port/; hooks upstream bajo PORT_PC, entregados por format-patch. Un hilo cooperativo; binarios normal/diagnóstico separados. |
| Entradas/seguridad | Fixtures aislados dentro de build/, ROM aportada localmente, save normal intacto, label visual restringido. La API BIOS sin longitud fuente no asegura entrada comprimida truncada; recursos del juego, no decoder para archivos arbitrarios. |
| Rendimiento | Calendario medido: ~16,8 µs adicionales/frame en fixture sin PPU/audio. Cadencia 1×/4× en fixture y recorridos reales con watchdog; no se atribuye esa cifra al coste gráfico entero. |

Hallazgos resueltos con test antes de corrección:

1. CpuFastSet no redondeaba conteos pequeños a ocho palabras.
2. ArcTan2 flotante difería de resultados fijos documentados.
3. Matrices ignoraban cuantización y sustituían wrap por saturación.
4. DMA repeat perdía máscara del destino GBA en la recarga.
5. Cambio de divisor timer reinterpretaba ciclos restantes como ticks.
6. Prioridad OBJ se ordenaba por BG antes de resolver el índice OAM.
7. Mosaico OBJ usaba fase local y podía perder la fila inicial.
8. Escritura afín idéntica no recargaba referencia interna; ahora hay hooks.

No quedan bloqueadores identificados para el alcance T11–T18. Esto no es
aprobación de compatibilidad completa: FIFO/capture, precisión de CPU,
BIOS malformed/bus VRAM, pruebas físicas y campaña siguen limitados.
No se añadió ni actualizó ninguna dependencia del entorno.

## Gates finales

- Normal y diagnóstico enlazan, normal sin input/frame de diagnóstico.
- 17 suites en raíz tras última corrección: build/t12-control-build.log.
- Clon de integración con los 29 parches: build/t18-clean-final.log,
  normal/diagnóstico y 17 suites PASS. Árbol upstream coincide con el original:
  a4e7dad5c792f55e13fde35af0e75e6f5d6c7e60.
- GBA compare OK: build/t18-final-gba.log.
- Batalla 1×/4× con victoria y regreso: build/t18-final-battle-1x.log y
  build/t18-final-battle-4x.log; normal sin combate forzado:
  build/t18-final-normal.log; save recovery: build/t18-final-save.log.
- Capturas con estados alineados: ppu-model.md; numéricos BIOS: bios.md.
- ROM/save/assets/binarios excluidos de archivos rastreados; parches 0025–29
  reproducidos. El documento preexistente port/docs/plans/ queda sin tocar.

T11–T18 y checkpoints C/D se cierran para los contratos documentados.
T19 sigue abierto: el hito 27 y el plan completo no se declaran terminados.
