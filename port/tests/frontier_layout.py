"""Measure Frontier save offsets with the current i686 source per test run."""
import json
import subprocess


def measure(project, directory):
    directory.mkdir(parents=True, exist_ok=True)
    executable=directory/'frontier-layout.exe'
    subprocess.run(['gcc','-std=gnu11','-DPORT_PC','-iquote','pokeemerald/include',
                    '-I','port','-include','stdlib.h','port/tests/frontier_layout.c',
                    '-o',str(executable)],cwd=project,check=True)
    result=subprocess.check_output([str(executable)],cwd=project)
    json.loads(result)
    target=directory/'frontier-layout.json'
    temporary=target.with_suffix('.json.tmp')
    temporary.write_bytes(result)
    temporary.replace(target)
    return target
