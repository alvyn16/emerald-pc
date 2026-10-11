# Inventario BIOS (T18)

Generador: `python port/tools/audit_bios.py`. Inventario léxico de funciones
C y aliases CpuCopy/CpuFill; las ubicaciones apuntan al inicio de cada función.
No filtra PORT_PC ni demuestra alcanzabilidad, y no inventaría SWI numéricos
en ensamblador. Los candidatos sin llamadas no requieren nuevos stubs.

Prioridad: copias/descompresión (carga de mapas, sprites y combate), matrices
(intro, selección inicial y animaciones), cálculo (movimiento/animaciones).
Waits/IRQ se verificaron en T09–T12. MultiBoot está deshabilitado; reset por
flags se implementará en T19. m4a usa el backend host, no SoundDriver BIOS.

| Entrada | Archivos C | Funciones consumidoras | Estado | Ejemplos |
| --- | ---: | ---: | --- | --- |
| ArcTan | 0 | 0 | sin implementación host |  |
| ArcTan2 | 1 | 1 | host | src/battle_anim_mons.c:1363 ArcTan2_ |
| BgAffineSet | 3 | 3 | host | src/bg.c:244 SetBgAffineInternal<br>src/intro.c:2810 PanFadeAndZoomScreen<br>src/util.c:149 DoBgAffineSet |
| BitUnPack | 0 | 0 | sin implementación host |  |
| CpuFastSet | 14 | 23 | host | src/decoration.c:1933 CopyPalette<br>src/decoration.c:1938 CopyTile<br>src/easy_chat.c:3023 LoadEasyChatScreen |
| CpuSet | 88 | 248 | host | src/AgbRfu_LinkManager.c:68 rfu_LMAN_initializeManager<br>src/AgbRfu_LinkManager.c:83 rfu_LMAN_endManager<br>src/battle_anim.c:668 MoveBattlerSpriteToBG |
| Diff16bitUnFilter | 0 | 0 | sin implementación host |  |
| Diff8bitUnFilterVram | 0 | 0 | sin implementación host |  |
| Diff8bitUnFilterWram | 0 | 0 | sin implementación host |  |
| Div | 1 | 1 | host | src/librfu_rfu.c:428 rfu_REQ_configSystem |
| DivArm | 0 | 0 | host |  |
| GetBiosChecksum | 0 | 0 | sin implementación host |  |
| Halt | 0 | 0 | host |  |
| HardReset | 0 | 0 | sin implementación host |  |
| HuffUnComp | 0 | 0 | sin implementación host |  |
| IntrWait | 0 | 0 | host |  |
| LZ77UnCompVram | 19 | 41 | host | src/battle_transition.c:1406 Aqua_Init<br>src/battle_transition.c:1421 Magma_Init<br>src/battle_transition.c:1484 Aqua_SetGfx |
| LZ77UnCompWram | 18 | 44 | host | src/berry_crush.c:1942 CopyPlayerNameWindowGfxToBg<br>src/bg.c:874 CopyToBgTilemapBuffer<br>src/decompress.c:12 LZDecompressWram |
| MultiBoot | 1 | 1 | error seguro; accesorio no soportado | src/multiboot.c:28 MultiBootMain |
| ObjAffineSet | 4 | 6 | host | src/battle_anim_mons.c:1260 SetSpriteRotScale<br>src/battle_anim_mons.c:1331 TrySetSpriteRotScale<br>src/pokedex_cry_screen.c:488 SpriteCB_CryMeterNeedle |
| RLUnCompVram | 1 | 1 | host | src/contest_painting.c:419 LoadContestPaintingFrame |
| RLUnCompWram | 1 | 1 | host | src/contest_painting.c:419 LoadContestPaintingFrame |
| RegisterRamReset | 2 | 2 | stub; T19 pendiente | src/main.c:92 AgbMain<br>src/reload_save.c:13 ReloadSave |
| SoftReset | 2 | 2 | host | src/credits.c:694 Task_CreditsSoftReset<br>src/main.c:438 DoSoftReset |
| SoundBias | 0 | 0 | sin implementación host |  |
| Sqrt | 1 | 1 | host | src/battle_script_commands.c:9905 Cmd_handleballthrow |
| Stop | 0 | 0 | sin implementación host |  |
| VBlankIntrWait | 1 | 2 | host | src/ereader_helpers.c:505 EReader_Send<br>src/ereader_helpers.c:546 EReader_Recv |
