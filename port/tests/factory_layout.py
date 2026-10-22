"""Measure private upstream Factory UI layouts in ignored build artifacts."""
from pathlib import Path
import subprocess


def measure(project):
    source=(project/'pokeemerald/src/battle_factory_screen.c').read_text()
    structures=source[source.index('struct FactorySelectableMon\n'):source.index('static void SpriteCB_Pokeball(')]
    # Upstream definitions remain private, just like preprocessed build output.
    probe=project/'build/factory-layout.c'
    fields={'FactorySelectScreen':('cursorPos','menuCursorPos','yesNoCursorPos','mons','selectingMonsState'),
            'FactorySelectableMon':('monData','selectedId'),
            'FactorySwapScreen':('cursorPos','menuCursorPos','yesNoCursorPos','inEnemyScreen','monSwapped')}
    lines=['#include <stdio.h>','#include <stddef.h>','#include "global.h"',
           '#include "task.h"','#include "constants/battle_frontier.h"',
           '#define SELECTABLE_MONS_COUNT 6',structures,
           '_Static_assert(sizeof(void *) == 4, "MINGW32 required");',
           'int main(void) { puts("{");']
    for name,members in fields.items():
        lines.append(f'printf("\\\"{name}_size\\\":%zu,", sizeof(struct {name}));')
        for field in members:
            lines.append(f'printf("\\\"{name}_{field}\\\":%zu,", offsetof(struct {name}, {field}));')
    lines.append('puts("\\\"schema\\\":1}"); return 0; }')
    probe.write_text('\n'.join(lines),encoding='utf-8')
    exe=project/'build/factory-layout.exe'
    subprocess.run(['gcc','-std=gnu11','-DPORT_PC','-iquote','pokeemerald/include',
                    '-I','port','-include','stdlib.h',str(probe),'-o',str(exe)],cwd=project,check=True)
    (project/'build/factory-layout.json').write_bytes(subprocess.check_output([str(exe)],cwd=project))


if __name__ == '__main__':
    measure(Path(__file__).resolve().parents[2])
