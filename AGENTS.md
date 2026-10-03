# Reglas del proyecto

- Nunca commitear ROMs, saves, assets ni código de pokeemerald.
- Guardar los cambios a pokeemerald como parches en `patches/`, generados con `git format-patch`. La lógica de portabilidad va en `port/`.
- No modificar el build original de GBA salvo bajo `#ifdef PORT_PC`.
- Cada cambio debe compilar antes de darse por terminado.
- Hacer commits pequeños, usar una rama por hito y explicar el plan antes de escribir código.

## Hitos

1. Compilar con GCC o Clang para x86-64.
2. Abrir una ventana SDL2 con un framebuffer de 240x160.
3. Emular registros de video, VRAM, paletas y OAM.
4. Implementar el renderizador del PPU.
5. Implementar input.
6. Implementar audio.
7. Implementar guardado a disco.
8. Reemplazar llamadas a la BIOS.
