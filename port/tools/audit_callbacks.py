"""Read-only lexical inventory of callback resources and synchronous loaders.

Names and locations only; no upstream code or asset content is emitted.
This is a candidate inventory, not a C compiler or a lifetime proof.
"""

from pathlib import Path
import re
import subprocess


def functions(text: str) -> dict:
    # Preserve offsets while hiding comments and literals from brace scanning.
    masked = re.sub(r'/\*.*?\*/|//[^\n]*|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'',
                    lambda match: ''.join('\n' if c == '\n' else ' ' for c in match[0]),
                    text, flags=re.S)
    result = {}
    previous_end = 0
    pattern = r'^[\w *]+\b(\w+)\s*\([^;{}]*\)\s*\{'
    for match in re.finditer(pattern, masked, re.M):
        # Do not interpret nested if/switch/while blocks as C functions.
        if match.start() < previous_end or match[1] in ('if', 'switch', 'while', 'for'):
            continue
        start = match.end()
        depth, end = 1, start
        while end < len(masked) and depth:
            depth += (masked[end] == '{') - (masked[end] == '}')
            end += 1
        result[match[1]] = (text.count('\n', 0, match.start()) + 1,
                           masked[start:end - 1])
        previous_end = end
    return result


def closure(name: str, funcs: dict) -> str:
    pending, seen, bodies = [name], set(), []
    while pending:
        current = pending.pop()
        if current in seen or current not in funcs:
            continue
        seen.add(current)
        body = funcs[current][1]
        bodies.append(body)
        pending.extend(re.findall(r'\b(\w+)\s*\(', body))
    return '\n'.join(bodies)


def main() -> None:
    project = Path(__file__).resolve().parents[2]
    checkout = project / 'pokeemerald'
    revision = subprocess.check_output(['git', '-C', str(checkout), 'rev-parse', 'HEAD'],
                                       text=True).strip()
    rows, loaders, files = [], [], set()
    waits = r'\b(FreeTempTileDataBuffersIfPossible|IsDma3ManagerBusyWithBgCopy)\s*\('
    for path in sorted((checkout / 'src').glob('*.c')):
        funcs = functions(path.read_text(encoding='utf-8', errors='replace'))
        relative = path.relative_to(checkout).as_posix()
        released = {}
        for name, (line, body) in funcs.items():
            for root in re.findall(r'\b(?:Free|FREE_AND_SET_NULL|TRY_FREE_AND_SET_NULL)\s*\(\s*(\w+)', body):
                released.setdefault(root, []).append(f'{name}:{line}')
        for name, (line, body) in funcs.items():
            if name in ('SetVBlankCallback', 'SetHBlankCallback'):
                continue
            for registration in re.finditer(r'\bSet(VBlank|HBlank)Callback\s*\(\s*([^,)]+)', body):
                files.add(relative)
                target = registration[2].strip().lstrip('&')
                if target in ('NULL', '0'):
                    continue
                reachable = closure(target, funcs)
                roots = sorted(set(re.findall(r'\b(\w+)\s*->', reachable)) & released.keys())
                resources = '; '.join(f'{root} → {", ".join(released[root])}' for root in roots)
                status = resources or ('sin raíz liberada detectada' if target in funcs else 'destino dinámico/externo')
                rows.append(f'| {relative}:{line} {name} | {registration[1]} → {target} | {status} |')
            if re.search(r'\bwhile\s*\(', body) and re.search(waits, closure(name, funcs)):
                consumers = ', '.join(sorted(set(re.findall(waits, closure(name, funcs)))))
                loaders.append(f'| {relative}:{line} | {name} | {consumers} |')
    output = project / 'port/docs/callback-inventory.md'
    header = f'''# Inventario reproducible de callbacks y cargas

Checkout analizado: `{revision}`. {len(files)} archivos registran callbacks,
{len(rows)} registros no nulos; {len(loaders)} funciones con while alcanzan
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
'''
    tail = '''
## Loops con dependencias DMA alcanzables

No toda función listada se bloquea: algunas repiten tareas con límites
internos o retornan al loop principal. Los sondeos pueden pertenecer a otra
rama del mismo grafo de llamadas. Verificar cada consumidor antes de parchear.

| Ubicación | Función con while | Sondeo alcanzable |
| --- | --- | --- |
'''
    output.write_text(header + '\n'.join(rows) + '\n' + tail + '\n'.join(loaders) + '\n',
                      encoding='utf-8')
    print(f'{len(files)} callback files; {len(rows)} registrations; {len(loaders)} loader candidates; {output}')


if __name__ == '__main__':
    main()
