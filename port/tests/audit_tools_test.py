"""Regression for function discovery used by the read-only inventories."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from audit_callbacks import closure, functions


fixture = '''
void Alpha(void) {
    const char *literal = "} {";
    if (ready) {
        Beta();
    }
    while (pending) { Poll(); }
    switch (state) { default: break; }
}
static void Beta(void) {
    /* a comment with } { */
    Alpha();
    Release(resource);
}
'''
found = functions(fixture)
assert set(found) == {"Alpha", "Beta"}, found
assert "Beta();" in found["Alpha"][1]
assert "Release(resource)" in closure("Alpha", found)
assert closure("External", found) == ""
print("PASS inventory parser: nested blocks, literals, comments and cyclic calls")
