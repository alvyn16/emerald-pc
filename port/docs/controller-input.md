# T28 — controles host

El ejecutable normal lee teclado y un mando reconocido por SDL GameController.
El diagnóstico conserva su sobrescritura por script; no se compila en el normal.
Se abre el primer mando compatible, se cierra al desconectarse y se busca otro.
Stick izquierdo: zona muerta de 16000 sobre 32767; direcciones opuestas se anulan.
Al recuperar foco, conectar mando, cargar bindings o reiniciar, hay que soltar
los botones mantenidos antes de volver a activarlos. Sin foco no se emiten botones.

## Asignación y remapeo

Se crea `saves/controls.cfg`, ignorado por Git, junto a los saves del proyecto,
independientemente del directorio desde donde se ejecute. Editarlo con el juego
cerrado; la siguiente ejecución carga los cambios. Cada línea contiene dos
enteros: scancode SDL del teclado y número SDL GameControllerButton.

| Línea / acción GBA | Tecla (scancode) | Mando SDL (número) |
| --- | --- | --- |
| 1 A | Z (29) | A (0) |
| 2 B | X (27) | B (1) |
| 3 Select | Backspace (42) | Back (4) |
| 4 Start | Enter (40) | Start (6) |
| 5 derecha | derecha (79) | D-pad derecha (14) |
| 6 izquierda | izquierda (80) | D-pad izquierda (13) |
| 7 arriba | arriba (82) | D-pad arriba (11) |
| 8 abajo | abajo (81) | D-pad abajo (12) |
| 9 R | S (22) | hombro derecho (10) |
| 10 L | A (4) | hombro izquierdo (9) |

Ejemplo: intercambiar los scancodes 29 y 27 intercambia Z/X. Los números de
botón se pueden intercambiar de la misma manera; los ejes conservan direcciones.
Los scancodes corresponden a posiciones físicas de tecla. P (19) se reserva
para velocidad; el menú usa teclado P, arriba/abajo y Enter. Sus teclas no pasan
al juego hasta soltarlas, incluso si Enter se remapea a A. No hay editor gráfico
de bindings ni navegación del menú de velocidad mediante mando.

Se exige exactamente diez pares, sin teclas/botones repetidos ni valores fuera
de rango. Un archivo inválido se conserva y se usan defaults con mensaje claro.
Mando no reconocido por la base SDL: teclado disponible; no se inventa soporte.

## Evidencia

- `input_test.c`: backend falso, foco, botones retenidos, hotplug/reconexión,
  zona muerta, direcciones opuestas, remapeo/persistencia/reinicio, archivo
  inválido y Enter remapeado a A sin filtrarse desde el menú. PASS.
- `input_sdl_test.c`: SDL real con joystick virtual GameController, botones,
  eje izquierdo, desconexión y reconexión. Vídeo dummy para ejecución automática;
  no usa un backend falso de mando. PASS.
- SDL detectó **0 joysticks físicos** antes del fixture. Escucha/vibración,
  identificación de modelos reales y conexión/desconexión física: pendientes
  de hardware; no se ha pedido ni registrado una aprobación inexistente.
- Normal: casa → exterior de Littleroot sin batalla inesperada; PASS.
- Diagnóstico: retirada PC y recarga en nuevo proceso; PASS con input por script.
- Reinicio normal por teclas y por juego: un reemplazo, velocidad 1, save intacto,
  cierre limpio. Error real de CreateProcess también llega a cleanup. PASS.
- 21 suites host y verificación de separación normal/diagnóstico PASS.

Logs privados `build/t28-*.log`. Datos del usuario no se abren por las fixtures.
T27 y Checkpoint E siguen abiertos por el recorrido continuo de campaña.
