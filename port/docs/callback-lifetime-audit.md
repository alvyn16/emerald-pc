# Callbacks y cargas síncronas — primer lote

Se encontraron **67 archivos C** con llamadas a SetVBlankCallback o
SetHBlankCallback. Es un inventario de candidatos, no 67 fallos confirmados.
La comprobación de vidas útiles sigue por lotes; no se consideran todas
las pantallas verificadas por tener un callback parecido.

| Ruta inspeccionada | Consumidor / recurso | Resultado |
| --- | --- | --- |
| Transición de combate | VBlankCB_Slice / sTransitionData | SIGSEGV reproducido y corregido en 0016; batalla regresada |
| Cierre de almacenamiento | VBlankCB_PokeStorage / sStorage->bg2_X | SIGSEGV reproducido al servir VBlank después de FreePokeStorageData; corrección 0018 |
| Pantalla de resumen | VBlank / OAM y paletas globales | No dereferencia directamente el objeto liberado; cola de copias pendiente de revisar |
| Equipo | VBlankCB_PartyMenu / OAM y paletas globales | No dereferencia directamente sPartyMenuInternal; no se declara probado todo el ciclo del menú |
| Nombre | CleanupNamingScreen / callback liberado | Corrección 0010 conservada |
| Carga de mapa | DMA diferido dentro de loop síncrono | Corrección 0012 conservada |
| Carga de bolsa | DMA diferido dentro de loop síncrono | Corrección 0014 conservada |

## Cargas que necesitan una regresión adicional

`CB2_InitSummaryScreen` repite LoadGraphics dentro de una sola llamada.
Su subcarga usa FreeTempTileDataBuffersIfPossible: hay que verificar si
requiere servir un frame cooperativo antes de cambiarla.
`CB2_InitPartyMenu` tiene un loop similar con ShowPartyMenu. Estos son
candidatos a espera infinita, no fallos ya reproducidos.

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

## Archivos candidatos

Lista obtenida con `rg -l 'Set(VBlank|HBlank)Callback\(' pokeemerald/src -g '*.c'`.

- `pokeemerald/src/battle_dome.c`
- `pokeemerald/src/battle_factory_screen.c`
- `pokeemerald/src/battle_main.c`
- `pokeemerald/src/battle_pyramid_bag.c`
- `pokeemerald/src/battle_records.c`
- `pokeemerald/src/battle_script_commands.c`
- `pokeemerald/src/battle_transition.c`
- `pokeemerald/src/berry_blender.c`
- `pokeemerald/src/berry_crush.c`
- `pokeemerald/src/berry_fix_program.c`
- `pokeemerald/src/berry_tag_screen.c`
- `pokeemerald/src/cable_car.c`
- `pokeemerald/src/clear_save_data_screen.c`
- `pokeemerald/src/contest_painting.c`
- `pokeemerald/src/contest_util.c`
- `pokeemerald/src/contest.c`
- `pokeemerald/src/credits.c`
- `pokeemerald/src/diploma.c`
- `pokeemerald/src/dodrio_berry_picking.c`
- `pokeemerald/src/easy_chat.c`
- `pokeemerald/src/egg_hatch.c`
- `pokeemerald/src/evolution_scene.c`
- `pokeemerald/src/field_effect.c`
- `pokeemerald/src/field_region_map.c`
- `pokeemerald/src/fldeff_flash.c`
- `pokeemerald/src/frontier_pass.c`
- `pokeemerald/src/hall_of_fame.c`
- `pokeemerald/src/intro.c`
- `pokeemerald/src/item_menu.c`
- `pokeemerald/src/link_rfu_2.c`
- `pokeemerald/src/link.c`
- `pokeemerald/src/mail.c`
- `pokeemerald/src/main_menu.c`
- `pokeemerald/src/main.c`
- `pokeemerald/src/menu_helpers.c`
- `pokeemerald/src/move_relearner.c`
- `pokeemerald/src/mystery_event_menu.c`
- `pokeemerald/src/mystery_gift_menu.c`
- `pokeemerald/src/naming_screen.c`
- `pokeemerald/src/option_menu.c`
- `pokeemerald/src/overworld.c`
- `pokeemerald/src/party_menu.c`
- `pokeemerald/src/pokeblock_feed.c`
- `pokeemerald/src/pokeblock.c`
- `pokeemerald/src/pokedex.c`
- `pokeemerald/src/pokemon_jump.c`
- `pokeemerald/src/pokemon_storage_system.c`
- `pokeemerald/src/pokemon_summary_screen.c`
- `pokeemerald/src/pokenav.c`
- `pokeemerald/src/rayquaza_scene.c`
- `pokeemerald/src/region_map.c`
- `pokeemerald/src/reset_rtc_screen.c`
- `pokeemerald/src/reshow_battle_screen.c`
- `pokeemerald/src/roulette.c`
- `pokeemerald/src/save_failed_screen.c`
- `pokeemerald/src/shop.c`
- `pokeemerald/src/slot_machine.c`
- `pokeemerald/src/start_menu.c`
- `pokeemerald/src/starter_choose.c`
- `pokeemerald/src/title_screen.c`
- `pokeemerald/src/trade.c`
- `pokeemerald/src/trainer_card.c`
- `pokeemerald/src/union_room_battle.c`
- `pokeemerald/src/union_room_chat.c`
- `pokeemerald/src/use_pokeblock.c`
- `pokeemerald/src/wallclock.c`
- `pokeemerald/src/wireless_communication_status_screen.c`
