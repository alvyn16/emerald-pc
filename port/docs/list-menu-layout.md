# Por qué falla `ListMenuTooLargeForTaskData` en x86-64

`pokeemerald/src/list_menu.c:18` exige `sizeof(struct ListMenu) <= sizeof(((struct Task *)NULL)->data)`. La comprobación existe porque el código interpreta `gTasks[listTaskId].data` como `struct ListMenu *` (por ejemplo, `src/list_menu.c:396`). `Task.data` está declarado en `include/task.h:20` como `s16 data[16]`: **32 bytes** en ambos entornos.

`struct ListMenu` (`include/list_menu.h:82`) contiene `struct ListMenuTemplate template`, dos `u16` (`scrollOffset`, `selectedRow`) y cuatro `u8` (`unk_1C`, `unk_1D`, `taskId`, `unk_1F`). La plantilla (`include/list_menu.h:60`) contiene **tres punteros** que crecen de 4 a 8 bytes:

1. `const struct ListMenuItem *items`
2. `void (*moveCursorFunc)(...)`
3. `void (*itemPrintFunc)(...)`

| Medida u offset | GBA / ABI de 32 bits | MINGW64 x86-64 |
| --- | ---: | ---: |
| `sizeof(void *)` | 4 | 8 |
| `ListMenuTemplate.items` | 0 | 0 |
| `ListMenuTemplate.moveCursorFunc` | 4 | 8 |
| `ListMenuTemplate.itemPrintFunc` | 8 | 16 |
| `ListMenuTemplate.totalItems` | 12 | 24 |
| `ListMenuTemplate.windowId` | 16 | 28 |
| `sizeof(struct ListMenuTemplate)` | **24** | **40** |
| `ListMenu.scrollOffset` | 24 | 40 |
| `ListMenu.selectedRow` | 26 | 42 |
| `ListMenu.taskId` | 30 | 46 |
| `sizeof(struct ListMenu)` | **32** | **48** |
| `sizeof(Task.data)` | **32** | **32** |

Cada uno de los tres punteros añade cuatro bytes en x86-64 (**12 bytes**). Además, la alineación de `ListMenuTemplate` sube de 4 a 8 y agrega **4 bytes** de relleno final. El resultado es `32 <= 32` en GBA y `48 <= 32`, falso, en x86-64. La estructura sobrescribiría 16 bytes fuera de `Task.data` si se ignorara la aserción.

Las cifras de x86-64 y del ABI de 32 bits se midieron compilando un programa de prueba con las cabeceras originales mediante GCC MINGW64 e i686 de MSYS2. La cifra GBA también se deduce directamente de los campos de ancho fijo y sus alineaciones de 32 bits; el build ARM original supera la aserción. El probe local está en `build/list-menu-layout.c`, ignorado por Git. No se alteró pokeemerald.
