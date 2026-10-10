"""Inventory register names, consumers and lexical writes; emit metadata only."""

from collections import defaultdict
from pathlib import Path
import re
import subprocess

from audit_callbacks import functions


def main() -> None:
    project = Path(__file__).resolve().parents[2]
    source = project / "pokeemerald"
    revision = subprocess.check_output(["git", "-C", str(source), "rev-parse", "HEAD"], text=True).strip()
    registers = defaultdict(lambda: {"uses": set(), "writes": set()})
    for path in sorted((source / "src").glob("*.c")):
        for function, (line, body) in functions(path.read_text(errors="replace")).items():
            for match in re.finditer(r"\b(REG_(?!ADDR_|OFFSET_)[A-Z][A-Z0-9_]*|GPIO_PORT_[A-Z_]+)\b", body):
                name = match[0]
                if name == "REG_BASE":
                    continue
                location = f"{path.relative_to(source).as_posix()}:{line} {function}"
                registers[name]["uses"].add(location)
                tail = body[match.end():]
                # Function-like macros with simple arguments and scalar lvalues.
                tail = re.sub(r"^\s*\([^()]*\)", "", tail)
                if re.match(r"\s*(?:[+\-*/&|^]?=(?!=)|\+\+|--)", tail):
                    registers[name]["writes"].add(location)
    rows = []
    for name, record in sorted(registers.items()):
        consumers = "<br>".join(sorted(record["uses"]))
        writes = "<br>".join(sorted(record["writes"])) or "—"
        rows.append(f"| {name} | {consumers} | {writes} |")
    output = project / "port/docs/register-inventory.md"
    header = f'''# Inventario léxico de registros

Upstream analizado: `{revision}`. {len(registers)} nombres usados dentro
de funciones C. Generador: `python port/tools/audit_registers.py`.
Ubicaciones indican el inicio de la función, no la línea de la expresión.
La columna usos incluye lecturas y escrituras; escribe señala candidatos
con operadores de asignación/incremento detrás del nombre. No distingue
ramas PORT_PC, expande macros ni resuelve alias de puntero. No es una lista
de accesos efectivos del binario. Análisis manual adicional y contrato en
[register-model.md](register-model.md); especialmente GPU_REG, DmaSet,
IntrEnable, timerL/timerH y ensamblador.

| Registro | Funciones consumidoras | Escrituras candidatas |
| --- | --- | --- |
'''
    output.write_text(header + "\n".join(rows) + "\n", encoding="utf-8")
    print(f"{len(registers)} register names; {output}")


if __name__ == "__main__":
    main()
