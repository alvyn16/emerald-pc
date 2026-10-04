# Ensamblado i686 de `data/*.s`

Se intentaron los **15** archivos `.s` del checkout upstream fijado, con la cadena original `tools/preproc → GCC -E → tools/preproc -ie → GAS`, sin modificar `pokeemerald/`. Salida bajo `build/host-data-i686/` (ignorada). Comando en MINGW32: `make -B -C port -k data-objects`; resultado final **15/15 objetos, exit 0**.

| Fuente | Primera pasada COFF sin filtro | Pasada con `port/asm_compat.sed` |
| --- | --- | --- |
| `battle_ai_scripts.s`, `battle_anim_scripts.s`, `battle_scripts_1.s`, `battle_scripts_2.s` | Falla: `.section script_data, "aw", %progbits` usa sintaxis ELF | Pasan |
| `contest_ai_scripts.s`, `event_scripts.s`, `field_effect_scripts.s`, `mystery_event_script_cmd_table.s` | Mismo error de sección ELF | Pasan |
| `sound_data.s` | Falla: `.size` de `sound/music_player_table.inc` no es una directiva COFF válida | Pasa |
| `map_events.s`, `maps.s`, `mystery_gift.s` | Pasan | Pasan |
| `multiboot_berry_glitch_fix.s`, `multiboot_ereader.s`, `multiboot_pokemon_colosseum.s` | Pasan como blobs `.incbin` | Pasan |

El filtro local cambia la sección ELF a `.section script_data,"dw"` para PE/COFF y elimina `.size`, metadato de tamaño de símbolo que no altera bytes del juego. No se encontró `.thumb` ni instrucciones ARM ejecutables en estos 15 archivos de datos. Se ejecuta `objcopy --prefix-symbols=_` sobre cada objeto i686: el ABI i686 de Windows usa `_` delante de símbolos C, mientras que las etiquetas originales de los datos se ensamblan sin ese prefijo. Por ejemplo, `event_scripts.o` pasa a definir `_gText_ApprenticePleaseTeach0`, que coincide con la referencia C. Esta transformación opera solo sobre objetos ignorados en `build/`.

Como comprobación de integración, al enlazar los 306 objetos C disponibles más estos 15 objetos de datos, los símbolos distintos sin definir quedan en **666** (1.841 referencias, sin definiciones duplicadas). Muchos de los nuevos pendientes son música generada desde MIDI: **210** nombres `mus_*` y **269** `se_*`. El log está en `build/m2-link-data-final.log`; resolver las canciones corresponde al paso de enlace del ejecutable, no a los 15 `data/*.s` de esta prueba.
# Canciones generadas

El build GBA generó además 530 fuentes de canciones en `sound/songs/midi/*.s`.
`make -C port song-objects` ensambla las 530 en MINGW32. El flujo quita los
comentarios ARM `@` de la canción y de `MPlayDef.s` en archivos intermedios
ignorados bajo `build/`, ensambla sin copiar fuentes al repositorio público y
aplica el prefijo `_` de COFF a los símbolos definidos. Las 530 pasan; con los
306 objetos C, los 15 datos y las funciones BIOS host, el enlace de prueba
queda en 122 símbolos distintos sin definir (869 referencias), concentrados
en script, m4a, link/multiboot e inicio ARM.
