/* Minimal host-side reproduction of a GBA-style map pointer table. */
    .section .rdata,"dr"
    .globl map_pointer_table
map_pointer_table:
    .4byte map_first
    .4byte map_second
map_first:
    .byte 1
map_second:
    .byte 2
