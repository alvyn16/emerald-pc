# Inventario reproducible de callbacks y cargas

Checkout analizado: `cac99eeb49d7883d2b49eef3e51ccd75d841859b`. 67 archivos registran callbacks,
142 registros no nulos; 17 funciones con while alcanzan
sondeos de DMA dentro del mismo archivo.

Generador propio: `python port/tools/audit_callbacks.py`. Análisis léxico de
funciones y llamadas transitivas dentro de cada archivo. No resuelve macros,
punteros dinámicos, ramas de preprocesado ni llamadas entre archivos.
Los candidatos no son fallos confirmados. Una raíz puede corresponder a un
campo liberado, no al objeto entero; revisar el orden y la ruta real.
Las colas de sprite/DMA y recursos entre módulos requieren revisión adicional.

## Registros y recursos candidatos

| Registro (archivo, función, línea) | Callback | Raíz y liberadores candidatos |
| --- | --- | --- |
| src/battle_dome.c:3055 Task_ShowTourneyInfoCard | VBlank → VblankCb_TourneyInfoCard | sin raíz liberada detectada |
| src/battle_dome.c:5334 Task_ShowTourneyTree | HBlank → HblankCb_TourneyTree | sin raíz liberada detectada |
| src/battle_dome.c:5334 Task_ShowTourneyTree | VBlank → VblankCb_TourneyTree | sin raíz liberada detectada |
| src/battle_factory_screen.c:1135 CB2_InitSelectScreen | VBlank → VBlankCB_SelectScreen | sin raíz liberada detectada |
| src/battle_factory_screen.c:3273 CB2_InitSwapScreen | VBlank → Swap_VblankCb | sin raíz liberada detectada |
| src/battle_main.c:619 CB2_InitBattleInternal | VBlank → VBlankCB_Battle | sin raíz liberada detectada |
| src/battle_main.c:2177 CB2_InitEndLinkBattle | VBlank → VBlankCB_Battle | sin raíz liberada detectada |
| src/battle_main.c:2417 CB2_InitAskRecordBattle | VBlank → VBlankCB_Battle | sin raíz liberada detectada |
| src/battle_pyramid_bag.c:459 LoadPyramidBagMenu | VBlank → VBlankCB_PyramidBag | sin raíz liberada detectada |
| src/battle_records.c:473 switch | VBlank → VblankCB_TrainerHillRecords | sin raíz liberada detectada |
| src/battle_records.c:471 CB2_ShowTrainerHillRecords | VBlank → VblankCB_TrainerHillRecords | sin raíz liberada detectada |
| src/battle_script_commands.c:10101 Cmd_displaydexinfo | VBlank → VBlankCB_Battle | destino dinámico/externo |
| src/battle_transition.c:1201 Swirl_Init | VBlank → VBlankCB_Swirl | sTransitionData → IsBattleTransitionDone:1041 |
| src/battle_transition.c:1201 Swirl_Init | HBlank → HBlankCB_Swirl | sin raíz liberada detectada |
| src/battle_transition.c:1265 Shuffle_Init | VBlank → VBlankCB_Shuffle | sTransitionData → IsBattleTransitionDone:1041 |
| src/battle_transition.c:1265 Shuffle_Init | HBlank → HBlankCB_Shuffle | sin raíz liberada detectada |
| src/battle_transition.c:1382 InitPatternWeaveTransition | VBlank → VBlankCB_PatternWeave | sTransitionData → IsBattleTransitionDone:1041 |
| src/battle_transition.c:1701 PatternWeave_CircularMask | VBlank → VBlankCB_CircularMask | sTransitionData → IsBattleTransitionDone:1041 |
| src/battle_transition.c:1891 ClockwiseWipe_Init | VBlank → VBlankCB_ClockwiseWipe | sTransitionData → IsBattleTransitionDone:1041 |
| src/battle_transition.c:2090 Ripple_Init | VBlank → VBlankCB_Ripple | sTransitionData → IsBattleTransitionDone:1041 |
| src/battle_transition.c:2090 Ripple_Init | HBlank → HBlankCB_Ripple | sin raíz liberada detectada |
| src/battle_transition.c:2175 Wave_Init | VBlank → VBlankCB_Wave | sTransitionData → IsBattleTransitionDone:1041 |
| src/battle_transition.c:2308 Mugshot_Init | VBlank → VBlankCB_Mugshots | sTransitionData → IsBattleTransitionDone:1041 |
| src/battle_transition.c:2332 Mugshot_SetGfx | HBlank → HBlankCB_Mugshots | sTransitionData → IsBattleTransitionDone:1041 |
| src/battle_transition.c:2455 Mugshot_WaitPlayerSlide | VBlank → VBlankCB_MugshotsFadeOut | sTransitionData → IsBattleTransitionDone:1041 |
| src/battle_transition.c:2733 Slice_Init | VBlank → VBlankCB_Slice | sTransitionData → IsBattleTransitionDone:1041 |
| src/battle_transition.c:2733 Slice_Init | HBlank → HBlankCB_Slice | sin raíz liberada detectada |
| src/battle_transition.c:2852 ShredSplit_Init | VBlank → VBlankCB_Slice | sTransitionData → IsBattleTransitionDone:1041 |
| src/battle_transition.c:2852 ShredSplit_Init | HBlank → HBlankCB_Slice | sin raíz liberada detectada |
| src/battle_transition.c:3051 Blackhole_Init | VBlank → VBlankCB_CircularMask | sTransitionData → IsBattleTransitionDone:1041 |
| src/battle_transition.c:3444 Rayquaza_Init | VBlank → VBlankCB_Rayquaza | sTransitionData → IsBattleTransitionDone:1041 |
| src/battle_transition.c:3529 Rayquaza_TriRing | VBlank → VBlankCB_CircularMask | sTransitionData → IsBattleTransitionDone:1041 |
| src/battle_transition.c:3597 WhiteBarsFade_Init | HBlank → HBlankCB_WhiteBarsFade | sin raíz liberada detectada |
| src/battle_transition.c:3597 WhiteBarsFade_Init | VBlank → VBlankCB_WhiteBarsFade | sTransitionData → IsBattleTransitionDone:1041 |
| src/battle_transition.c:3658 WhiteBarsFade_BlendToBlack | VBlank → VBlankCB_WhiteBarsFade_Blend | sTransitionData → IsBattleTransitionDone:1041 |
| src/battle_transition.c:3839 AngledWipes_Init | VBlank → VBlankCB_AngledWipes | sTransitionData → IsBattleTransitionDone:1041 |
| src/battle_transition.c:4333 FrontierLogoWave_InitScanline | VBlank → VBlankCB_FrontierLogoWave | sTransitionData → IsBattleTransitionDone:1041 |
| src/battle_transition.c:4333 FrontierLogoWave_InitScanline | HBlank → HBlankCB_FrontierLogoWave | sin raíz liberada detectada |
| src/berry_blender.c:1061 CB2_LoadBerryBlender | VBlank → VBlankCB_BerryBlender | sBerryBlender → LoadBerryBlenderGfx:957, CB2_CheckPlayAgainLink:2826, CB2_CheckPlayAgainLink:2826, CB2_CheckPlayAgainLocal:2942 |
| src/berry_blender.c:1498 InitBlenderBgs | VBlank → VBlankCB_BerryBlender | sBerryBlender → LoadBerryBlenderGfx:957, CB2_CheckPlayAgainLink:2826, CB2_CheckPlayAgainLink:2826, CB2_CheckPlayAgainLocal:2942 |
| src/berry_crush.c:1060 BerryCrush_SetVBlankCB | VBlank → VBlankCB | sin raíz liberada detectada |
| src/berry_tag_screen.c:212 InitBerryTagScreen | VBlank → VblankCB | sin raíz liberada detectada |
| src/cable_car.c:243 CB2_LoadCableCar | VBlank → VBlankCB_CableCar | sCableCar → CB2_EndCableCar:370, CB2_EndCableCar:370, CB2_EndCableCar:370, CB2_EndCableCar:370, CB2_EndCableCar:370 |
| src/clear_save_data_screen.c:123 SetupClearSaveDataScreen | VBlank → VBlankCB | sin raíz liberada detectada |
| src/contest.c:1169 CB2_StartContest | VBlank → VBlankCB_Contest | sin raíz liberada detectada |
| src/contest_painting.c:195 ShowContestPainting | VBlank → VBlankCB_ContestPainting | sin raíz liberada detectada |
| src/contest_util.c:523 CB2_StartShowContestResults | VBlank → VBlankCB_ShowContestResults | sin raíz liberada detectada |
| src/credits.c:409 CB2_StartCreditsSequence | VBlank → VBlankCB_Credits | sin raíz liberada detectada |
| src/credits.c:513 Task_SetBikeScene | VBlank → VBlankCB_Credits | sin raíz liberada detectada |
| src/diploma.c:50 CB2_ShowDiploma | VBlank → VBlankCB | sin raíz liberada detectada |
| src/dodrio_berry_picking.c:749 Task_StartDodrioGame | VBlank → VBlankCB_DodrioGame | sin raíz liberada detectada |
| src/easy_chat.c:1343 Task_EasyChatScreen | VBlank → VBlankCB_EasyChatScreen | sin raíz liberada detectada |
| src/egg_hatch.c:490 CB2_LoadEggHatch | VBlank → VBlankCB_EggHatch | sin raíz liberada detectada |
| src/evolution_scene.c:209 EvolutionScene | HBlank → EvoDummyFunc | sin raíz liberada detectada |
| src/evolution_scene.c:209 EvolutionScene | VBlank → VBlankCB_EvolutionScene | sin raíz liberada detectada |
| src/evolution_scene.c:311 CB2_EvolutionSceneLoadGraphics | HBlank → EvoDummyFunc | sin raíz liberada detectada |
| src/evolution_scene.c:311 CB2_EvolutionSceneLoadGraphics | VBlank → VBlankCB_EvolutionScene | sin raíz liberada detectada |
| src/evolution_scene.c:382 CB2_TradeEvolutionSceneLoadGraphics | HBlank → EvoDummyFunc | sin raíz liberada detectada |
| src/evolution_scene.c:382 CB2_TradeEvolutionSceneLoadGraphics | VBlank → VBlankCB_TradeEvolutionScene | sin raíz liberada detectada |
| src/evolution_scene.c:468 TradeEvolutionScene | VBlank → VBlankCB_TradeEvolutionScene | sin raíz liberada detectada |
| src/field_effect.c:2613 FieldMoveShowMonOutdoorsEffect_Init | VBlank → VBlankCB_FieldMoveShowMonOutdoors | sin raíz liberada detectada |
| src/field_effect.c:2713 FieldMoveShowMonOutdoorsEffect_End | VBlank → callback | destino dinámico/externo |
| src/field_effect.c:2781 FieldMoveShowMonIndoorsEffect_Init | VBlank → VBlankCB_FieldMoveShowMonIndoors | sin raíz liberada detectada |
| src/field_effect.c:2839 FieldMoveShowMonIndoorsEffect_End | VBlank → intrCallback | destino dinámico/externo |
| src/field_region_map.c:101 MCB2_InitRegionMapRegisters | VBlank → VBCB_FieldUpdateRegionMap | sin raíz liberada detectada |
| src/fldeff_flash.c:123 CB2_DoChangeMap | VBlank → VBC_ChangeMapVBlank | sin raíz liberada detectada |
| src/frontier_pass.c:729 InitFrontierPass | VBlank → VBlankCB_FrontierPass | sMapData → FreeFrontierMap:1380; sPassData → FreeFrontierPassData:652; sPassGfx → FreeFrontierPassGfx:674, FreeFrontierPassGfx:674, FreeFrontierPassGfx:674, FreeFrontierPassGfx:674 |
| src/frontier_pass.c:1069 Task_PassAreaZoom | VBlank → VBlankCB_FrontierPass | sMapData → FreeFrontierMap:1380; sPassData → FreeFrontierPassData:652; sPassGfx → FreeFrontierPassGfx:674, FreeFrontierPassGfx:674, FreeFrontierPassGfx:674, FreeFrontierPassGfx:674 |
| src/frontier_pass.c:1388 InitFrontierMap | VBlank → VBlankCB_FrontierPass | sMapData → FreeFrontierMap:1380; sPassData → FreeFrontierPassData:652; sPassGfx → FreeFrontierPassGfx:674, FreeFrontierPassGfx:674, FreeFrontierPassGfx:674, FreeFrontierPassGfx:674 |
| src/hall_of_fame.c:369 InitHallOfFameScreen | VBlank → VBlankCB_HallOfFame | sin raíz liberada detectada |
| src/hall_of_fame.c:799 CB2_DoHallOfFamePC | VBlank → VBlankCB_HallOfFame | sin raíz liberada detectada |
| src/intro.c:1072 SetUpCopyrightScreen | VBlank → VBlankCB_Intro | sin raíz liberada detectada |
| src/intro.c:1209 Task_Scene1_FadeIn | VBlank → VBlankCB_Intro | sin raíz liberada detectada |
| src/intro.c:1375 Task_Scene2_CreateSprites | VBlank → VBlankCB_Intro | sin raíz liberada detectada |
| src/item_menu.c:683 SetupBagMenu | VBlank → VBlankCB_BagMenuRun | sin raíz liberada detectada |
| src/link.c:296 LinkTestScreen | VBlank → VBlankCB_LinkError | sin raíz liberada detectada |
| src/link.c:1594 CB2_LinkError | VBlank → VBlankCB_LinkError | sin raíz liberada detectada |
| src/link_rfu_2.c:2574 Debug_RfuIdle | VBlank → VBlank_RfuIdle | sin raíz liberada detectada |
| src/mail.c:501 MailReadBuildGraphics | VBlank → VBlankCB_MailRead | sin raíz liberada detectada |
| src/main_menu.c:557 InitMainMenu | VBlank → VBlankCB_MainMenu | sin raíz liberada detectada |
| src/main_menu.c:1788 CB2_NewGameBirchSpeech_ReturnFromNamingScreen | VBlank → VBlankCB_MainMenu | sin raíz liberada detectada |
| src/move_relearner.c:391 CB2_InitLearnMove | VBlank → VBlankCB_MoveRelearner | sin raíz liberada detectada |
| src/move_relearner.c:419 CB2_InitLearnMoveReturnFromSelectMove | VBlank → VBlankCB_MoveRelearner | sin raíz liberada detectada |
| src/mystery_event_menu.c:82 CB2_InitMysteryEventMenu | VBlank → VBlankCB | sin raíz liberada detectada |
| src/mystery_gift_menu.c:384 HandleMysteryGiftOrEReaderSetup | VBlank → VBlankCB_MysteryGiftEReader | sin raíz liberada detectada |
| src/naming_screen.c:2033 SetVBlank | VBlank → VBlankCB_NamingScreen | sNamingScreen → MainState_Exit:696 |
| src/option_menu.c:152 CB2_InitOptionMenu | VBlank → VBlankCB | sin raíz liberada detectada |
| src/overworld.c:1782 SetFieldVBlankCallback | VBlank → VBlankCB_Field | sin raíz liberada detectada |
| src/party_menu.c:565 ShowPartyMenu | VBlank → VBlankCB_PartyMenu | sin raíz liberada detectada |
| src/party_menu.c:689 ExitPartyMenu | VBlank → VBlankCB_PartyMenu | sin raíz liberada detectada |
| src/pokeblock.c:521 InitPokeblockMenu | VBlank → VBlankCB_PokeblockMenu | sin raíz liberada detectada |
| src/pokeblock_feed.c:615 LoadPokeblockFeedScene | VBlank → VBlankCB_PokeblockFeed | sin raíz liberada detectada |
| src/pokedex.c:1591 CB2_OpenPokedex | VBlank → VBlankCB_Pokedex | sin raíz liberada detectada |
| src/pokedex.c:2053 LoadPokedexListPage | VBlank → VBlankCB_Pokedex | sin raíz liberada detectada |
| src/pokedex.c:3231 Task_LoadInfoScreen | VBlank → gPokedexVBlankCB | destino dinámico/externo |
| src/pokedex.c:3477 Task_LoadAreaScreen | VBlank → gPokedexVBlankCB | destino dinámico/externo |
| src/pokedex.c:3534 Task_LoadCryScreen | VBlank → gPokedexVBlankCB | destino dinámico/externo |
| src/pokedex.c:3727 Task_LoadSizeScreen | VBlank → gPokedexVBlankCB | destino dinámico/externo |
| src/pokedex.c:3957 Task_DisplayCaughtMonDexPage | VBlank → gPokedexVBlankCB | destino dinámico/externo |
| src/pokemon_jump.c:684 Task_StartPokemonJump | VBlank → VBlankCB_PokemonJump | sin raíz liberada detectada |
| src/pokemon_storage_system.c:1658 FieldTask_ReturnToPcMenu | VBlank → vblankCb | destino dinámico/externo |
| src/pokemon_storage_system.c:2089 Task_InitPokeStorage | VBlank → VBlankCB_PokeStorage | sStorage → FreePokeStorageData:3789, WaitForWallpaperGfxLoad:5416 |
| src/pokemon_summary_screen.c:1182 LoadGraphics | VBlank → VBlank | sin raíz liberada detectada |
| src/pokenav.c:315 CB2_InitPokeNav | VBlank → VBlankCB_Pokenav | sin raíz liberada detectada |
| src/pokenav.c:339 CB2_InitPokenavForTutorial | VBlank → VBlankCB_Pokenav | sin raíz liberada detectada |
| src/pokenav.c:537 SetVBlankCallback_ | VBlank → callback | destino dinámico/externo |
| src/pokenav.c:542 SetPokenavVBlankCallback | VBlank → VBlankCB_Pokenav | sin raíz liberada detectada |
| src/rayquaza_scene.c:1607 Task_DuoFightAnim | VBlank → VBlankCB_DuoFight | sin raíz liberada detectada |
| src/rayquaza_scene.c:2041 Task_RayTakesFlightAnim | VBlank → VBlankCB_RayquazaScene | sin raíz liberada detectada |
| src/rayquaza_scene.c:2281 Task_RayDescendsAnim | VBlank → VBlankCB_RayquazaScene | sin raíz liberada detectada |
| src/rayquaza_scene.c:2300 Task_HandleRayDescends | HBlank → HBlankCB_RayDescends | sRayScene → Task_EndAfterFadeScreen:1326 |
| src/rayquaza_scene.c:2499 Task_RayChargesAnim | VBlank → VBlankCB_RayquazaScene | sin raíz liberada detectada |
| src/rayquaza_scene.c:2692 Task_RayChasesAwayAnim | VBlank → VBlankCB_RayquazaScene | sin raíz liberada detectada |
| src/region_map.c:1647 CB2_OpenFlyMap | VBlank → VBlankCB_FlyMap | sin raíz liberada detectada |
| src/reset_rtc_screen.c:520 CB2_InitResetRtcScreen | VBlank → VBlankCB | sin raíz liberada detectada |
| src/reshow_battle_screen.c:42 CB2_ReshowBattleScreenAfterMenu | VBlank → VBlankCB_Battle | destino dinámico/externo |
| src/reshow_battle_screen.c:44 switch | VBlank → VBlankCB_Battle | destino dinámico/externo |
| src/roulette.c:1170 CB2_LoadRoulette | VBlank → VBlankCB_Roulette | sRoulette → FreeRoulette:1103, FreeRoulette:1103 |
| src/save_failed_screen.c:176 CB2_SaveFailedScreen | VBlank → VBlankCB | sin raíz liberada detectada |
| src/save_failed_screen.c:176 CB2_SaveFailedScreen | VBlank → VBlankCB_UpdateClockGraphics | sin raíz liberada detectada |
| src/save_failed_screen.c:178 switch | VBlank → VBlankCB | sin raíz liberada detectada |
| src/save_failed_screen.c:178 switch | VBlank → VBlankCB_UpdateClockGraphics | sin raíz liberada detectada |
| src/save_failed_screen.c:294 CB2_GameplayCannotBeContinued | VBlank → VBlankCB | sin raíz liberada detectada |
| src/save_failed_screen.c:307 CB2_FadeAndReturnToTitleScreen | VBlank → VBlankCB | sin raíz liberada detectada |
| src/shop.c:501 CB2_InitBuyMenu | VBlank → VBlankCB_BuyMenu | sin raíz liberada detectada |
| src/slot_machine.c:1153 SlotMachineSetup_InitVBlank | VBlank → SlotMachine_VBlankCB | sSlotMachine → SlotTask_FreeDataStructures:1745 |
| src/start_menu.c:1203 InitSaveWindowAfterLinkBattle | VBlank → VBlankCB_LinkBattleSave | sin raíz liberada detectada |
| src/starter_choose.c:374 CB2_ChooseStarter | VBlank → VblankCB_StarterChoose | sin raíz liberada detectada |
| src/title_screen.c:572 switch | VBlank → VBlankCB | sin raíz liberada detectada |
| src/title_screen.c:570 CB2_InitTitleScreen | VBlank → VBlankCB | sin raíz liberada detectada |
| src/trade.c:395 InitTradeMenu | VBlank → VBlankCB_TradeMenu | sin raíz liberada detectada |
| src/trade.c:2827 CB2_LinkTrade | VBlank → VBlankCB_TradeAnim | sTradeAnim → DoTradeAnim_Cable:3438, DoTradeAnim_Wireless:3911, CB2_FreeTradeAnim:4825 |
| src/trade.c:2996 CB2_InitInGameTrade | VBlank → VBlankCB_TradeAnim | sTradeAnim → DoTradeAnim_Cable:3438, DoTradeAnim_Wireless:3911, CB2_FreeTradeAnim:4825 |
| src/trainer_card.c:377 Task_TrainerCard | VBlank → VblankCb_TrainerCard | sData → CloseTrainerCard:360 |
| src/trainer_card.c:1587 FlipTrainerCard | HBlank → HblankCb_TrainerCard | sin raíz liberada detectada |
| src/union_room_battle.c:115 switch | VBlank → VBlankCB_UnionRoomBattle | sin raíz liberada detectada |
| src/union_room_battle.c:113 CB2_UnionRoomBattle | VBlank → VBlankCB_UnionRoomBattle | sin raíz liberada detectada |
| src/union_room_chat.c:943 CB2_LoadInterface | VBlank → VBlankCB_UnionRoomChatMain | sin raíz liberada detectada |
| src/use_pokeblock.c:567 ShowUsePokeblockMenu | VBlank → VBlankCB_UsePokeblockMenu | sMenu → FeedPokeblockToMon:690, CloseUsePokeblockMenu:820 |
| src/use_pokeblock.c:717 ShowUsePokeblockMenuForResults | VBlank → VBlankCB_UsePokeblockMenu | sMenu → FeedPokeblockToMon:690, CloseUsePokeblockMenu:820 |
| src/wallclock.c:671 WallClockInit | VBlank → VBlankCB_WallClock | sin raíz liberada detectada |
| src/wireless_communication_status_screen.c:198 CB2_InitWirelessCommunicationScreen | VBlank → VBlankCB_WirelessCommunicationScreen | sin raíz liberada detectada |

## Loops con dependencias DMA alcanzables

No toda función listada se bloquea: algunas repiten tareas con límites
internos o retornan al loop principal. Los sondeos pueden pertenecer a otra
rama del mismo grafo de llamadas. Verificar cada consumidor antes de parchear.

| Ubicación | Función con while | Sondeo alcanzable |
| --- | --- | --- |
| src/battle_pyramid_bag.c:452 | CB2_LoadPyramidBagMenu | FreeTempTileDataBuffersIfPossible |
| src/berry_tag_screen.c:199 | CB2_InitBerryTagScreen | FreeTempTileDataBuffersIfPossible |
| src/diploma.c:50 | CB2_ShowDiploma | FreeTempTileDataBuffersIfPossible |
| src/easy_chat.c:1328 | Task_InitEasyChatScreen | IsDma3ManagerBusyWithBgCopy |
| src/item_menu.c:672 | CB2_Bag | FreeTempTileDataBuffersIfPossible |
| src/mail.c:627 | CB2_InitMailRead | FreeTempTileDataBuffersIfPossible |
| src/overworld.c:2069 | DoMapLoadLoop | FreeTempTileDataBuffersIfPossible |
| src/party_menu.c:551 | CB2_InitPartyMenu | IsDma3ManagerBusyWithBgCopy |
| src/pokeblock.c:504 | CB2_InitPokeblockMenu | FreeTempTileDataBuffersIfPossible |
| src/pokeblock_feed.c:687 | PreparePokeblockFeedScene | FreeTempTileDataBuffersIfPossible |
| src/pokemon_summary_screen.c:1170 | CB2_InitSummaryScreen | FreeTempTileDataBuffersIfPossible |
| src/rayquaza_scene.c:1587 | LoadDuoFightSceneGfx | FreeTempTileDataBuffersIfPossible |
| src/rayquaza_scene.c:2025 | LoadTakesFlightSceneGfx | FreeTempTileDataBuffersIfPossible |
| src/rayquaza_scene.c:2229 | LoadDescendsSceneGfx | FreeTempTileDataBuffersIfPossible |
| src/rayquaza_scene.c:2479 | LoadChargesSceneGfx | FreeTempTileDataBuffersIfPossible |
| src/rayquaza_scene.c:2665 | LoadChasesAwaySceneGfx | FreeTempTileDataBuffersIfPossible |
| src/region_map.c:508 | InitRegionMap | FreeTempTileDataBuffersIfPossible |
