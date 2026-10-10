# Callbacks y cargas síncronas — primer lote

Se encontraron **67 archivos C** con llamadas a SetVBlankCallback o
SetHBlankCallback. Es un inventario de candidatos, no 67 fallos confirmados.
La comprobación de vidas útiles sigue por lotes; no se consideran todas
las pantallas verificadas por tener un callback parecido.

| Ruta inspeccionada | Consumidor / recurso | Resultado |
| --- | --- | --- |
| Transición de combate | VBlankCB_Slice / sTransitionData | SIGSEGV reproducido y corregido en 0016; batalla regresada |
| Cierre de almacenamiento | VBlankCB_PokeStorage / sStorage->bg2_X | SIGSEGV reproducido al servir VBlank después de FreePokeStorageData; corrección 0018 |
| Pantalla de resumen | LoadGraphics / cola de tiles | Bloqueo reproducido en estado 6; 0020 sirve VBlank durante la carga; apertura/cierre PASS |
| Equipo | AllocPartyMenuBgGfx / cola DMA de fondos | Bloqueo reproducido en estado 8; 0019 sirve VBlank durante la carga; apertura/cierre PASS |
| Nombre | CleanupNamingScreen / callback liberado | Corrección 0010 conservada |
| Carga de mapa | DMA diferido dentro de loop síncrono | Corrección 0012 conservada |
| Carga de bolsa | DMA diferido dentro de loop síncrono | Corrección 0014 conservada |

## Cargas de resumen y equipo

`menu_load_smoke.py summary|party` reproduce ambos bloqueos en frame 30.500.
Resumen espera FreeTempTileDataBuffersIfPossible; equipo espera
IsDma3ManagerBusyWithBgCopy. La cola solo progresa en ProcessDma3Requests,
llamado por VBlankIntr. Los loops síncronos no retornaban al servicio host.
0019 y 0020 sirven PortHost_RunFrame entre iteraciones, solo bajo PORT_PC.
Ambos fixtures llegan al menú en 31.100 y regresan con B al mapa 0.9 en
31.600, con salida limpia. No prueban todas las acciones de esos menús.

Logs y capturas locales: `build/menu-load-party/` y `build/menu-load-summary/`.
Las 13 suites host pasan, GBA compare OK y reproducción de los 20 parches
con árbol idéntico `0bb32861903f5d16ce9aa3eff53a8f2cb52ca92c`.

El loop de liberación de Pokémon en Task_ReleaseMon ejecuta un cálculo
incremental de reglas de liberación; no debe sustituirse a ciegas por una
espera de VBlank por parecer un while infinito.

## Almacenamiento: prueba de vida útil

Fixture en GDB: salida de casa (30.500), equipo propio de prueba,
EnterPokeStorage(2), carga durante 500 frames, FreePokeStorageData y un
PortHost_RunFrame antes de ejecutar el callback del siguiente menú.
El binario previo falló con SIGSEGV en VBlankCB_PokeStorage, frame 31.000.
El callback intenta consultar bg2_X cuando sStorage ya es NULL.
Log anterior: `build/storage-lifetime-repro.log`.

0018 retira VBlank antes de liberar, únicamente bajo PORT_PC. No oculta
la desreferencia con un retorno en el consumidor. La regresión
`storage_smoke.py` reutiliza el entorno aislado preparado por
`wild_battle_smoke.py`; comprueba el callback NULL, sirve el frame y vuelve
mediante CB2_ExitPokeStorage. No equivale a depositar todos los Pokémon o
recorrer todas las opciones del PC con teclado.

Resultado del fixture corregido: PASS, vuelta al mapa 0.9 en frame 31.200,
salida limpia en 31.500. GBA compare OK; árbol de reproducción idéntico.

## Inventario completo de candidatos

[callback-inventory.md](callback-inventory.md) registra los 136 callbacks
no nulos y 17 loops con rutas transitivas hasta sondeos DMA, con ubicación,
función y raíces liberables detectadas. Se reproduce con
`python port/tools/audit_callbacks.py`. El análisis es léxico y local a
cada archivo: no demuestra ausencia de errores ni cubre llamadas indirectas
y recursos entre módulos. Los cuatro recorridos comprobados se distinguen
de los candidatos que todavía requieren una prueba de uso.

Al reutilizar el parser para T08 se detectaron seis registros duplicados
porque bloques if/switch anidados se interpretaban como funciones. El parser
ahora excluye rangos ya contenidos en una función y tiene un fixture propio
`audit_tools_test.py`. Conteo corregido: 136 registros, antes 142; 67 archivos
y 17 loops se mantienen. Se regeneró el inventario con la revisión actual.
