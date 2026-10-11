"""Inventory BIOS call names/locations; never emit upstream source or assets."""
from pathlib import Path
import re
from audit_callbacks import functions


def main():
    project = Path(__file__).resolve().parents[2]
    checkout = project / 'pokeemerald'
    header = (checkout / 'include/gba/syscall.h').read_text()
    names = set(re.findall(r'^\w+[\w *]*\b(\w+)\([^;\n]*\);', header, re.M))
    names.update(('DivArm', 'IntrWait', 'Halt', 'ArcTan', 'BitUnPack', 'HuffUnComp',
                  'Diff8bitUnFilterWram', 'Diff8bitUnFilterVram', 'Diff16bitUnFilter',
                  'SoundBias', 'Stop', 'HardReset', 'GetBiosChecksum'))
    aliases = {'CpuCopy16': 'CpuSet', 'CpuCopy32': 'CpuSet',
               'CpuFill16': 'CpuSet', 'CpuFill32': 'CpuSet',
               'CpuFastCopy': 'CpuFastSet', 'CpuFastFill': 'CpuFastSet'}
    hits = {name: [] for name in sorted(names)}
    for path in sorted((checkout / 'src').rglob('*.c')):
        for function, (line, body) in functions(path.read_text(errors='replace')).items():
            for call in set(re.findall(r'\b(\w+)\s*\(', body)):
                name = aliases.get(call, call)
                if name in hits:
                    hits[name].append(f'{path.relative_to(checkout).as_posix()}:{line} {function}')
    own = (project / 'port/bios.c').read_text()
    implemented = functions(own)
    rows = []
    for name, locations in hits.items():
        files = len({location.split(':')[0] for location in locations})
        status = 'host' if name in implemented else 'sin implementación host'
        if name == 'RegisterRamReset': status = 'stub; T19 pendiente'
        if name == 'MultiBoot': status = 'error seguro; accesorio no soportado'
        rows.append(f'| {name} | {files} | {len(locations)} | {status} | '
                    + '<br>'.join(locations[:3]) + ' |')
    output = '''# Inventario BIOS (T18)

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
'''
    (project / 'port/docs/bios-inventory.md').write_text(
        output + '\n'.join(rows) + '\n', encoding='utf-8', newline='\n')
    print(f'{len(hits)} entradas; {sum(bool(v) for v in hits.values())} con consumidores C')


if __name__ == '__main__':
    main()
