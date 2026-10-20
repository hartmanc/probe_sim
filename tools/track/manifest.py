"""The evidence manifest's machine-readable lines (tools/track/compare/<id>/manifest.md), stdlib only.

Disposition lines (codify round, 20 Oct 2026): the coverage gate (tools/track/gates/coverageGate.ts) accepts a MISSING
inventory row of a kind outside its must-cover kinds (wall, fence, kerb, tyre wall, bridge) only when the manifest
carries a table row for it whose last cell is its disposition:

    | kind | side | s (m) | what | source | <type>: <text> |

type is one of
    placed: <object name> (...)       the object stands in the package, beyond the gate's +-15 m match (a stand seen across
                                      the infield, a mast seen ahead); the name must match an object of that kind
    assigned: <round>                 handed to another round; kind building only (the 21 Oct 2026 rule)
    rejected: <evidence>              the row is not a physical object of the package (a person, a temporary item, an
                                      old Street View object the recent footage contradicts), with the evidence named
    not resolvable: <captures, why>   the place was examined and the object cannot be placed from the evidence; names
                                      the captures examined
The gate validates each line (coverageGate.dispositionProblem) and fails on any MISSING row without a valid one.

    python3 -I tools/track/manifest.py <track id>     prints the disposition lines it finds
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DISPOSITION_TYPES = ("placed", "assigned", "rejected", "not resolvable")
INVENTORY_KINDS = ("wall", "fence", "kerb", "tyre_wall", "tyre_stack", "stand", "station", "bridge", "building", "mast", "cone_line")
_TYPE = re.compile(r"(placed|assigned|rejected|not resolvable):\s*(.*)$")


def parse_dispositions(lines):
    """Every markdown table row whose first cell is an inventory kind, whose third cell is a station (m) and whose last
    cell starts with a disposition type; returns [{kind, side, s, type, text, what}]."""
    out = []
    for line in lines:
        if not line.lstrip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 4 or cells[0] not in INVENTORY_KINDS:
            continue
        m = _TYPE.match(cells[-1])
        if not m:
            continue
        try:
            s = float(cells[2])
        except ValueError:
            continue
        out.append({"kind": cells[0], "side": cells[1], "s": s, "type": m.group(1), "text": m.group(2).strip(), "what": cells[3]})
    return out


def manifest_path(track_id):
    return os.path.join(HERE, "compare", track_id, "manifest.md")


def manifest_dispositions(track_id):
    """The disposition lines of the track's evidence manifest; [] without a manifest."""
    path = manifest_path(track_id)
    if not os.path.exists(path):
        return []
    with open(path) as fh:
        return parse_dispositions(fh)


if __name__ == "__main__":
    d = manifest_dispositions(sys.argv[1])
    for x in d:
        print(json.dumps(x))
    print(f"{len(d)} disposition lines in {os.path.relpath(manifest_path(sys.argv[1]))}", file=sys.stderr)
