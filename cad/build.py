#!/usr/bin/env python3
"""
Build every output file for the DELTA chair-desk.

    python cad/build.py            # print kit + full-size meshes (about 1 minute)
    python cad/build.py --step     # also the exact full-size STEP (adds ~6 minutes)

Outputs
    print/            1:6 kit: one STL per part (already in print orientation),
                      a 3MF plate per colour, and a coloured assembled preview
    models/           full size: GLB (any 3D viewer), USDZ (iPhone AR), STL per part, STEP
"""
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from deskgen import params as P                                  # noqa: E402
from deskgen.design import Design, COLORS_REAL                    # noqa: E402
from deskgen.kit import (build_kit_meshes, to_print_pose, layout,  # noqa: E402
                         write_3mf, NICE_NAMES)
from deskgen.mesh import to_trimesh                               # noqa: E402
from deskgen.export import export_glb, export_usdz, export_step   # noqa: E402

BLACK, WHITE = "#1D1D1F", "#F5F5F7"
KIT_COLOUR = {"shell": BLACK, "frame_L": BLACK, "frame_R": BLACK,
              "base": WHITE, "sleeve": WHITE, "head": WHITE, "top": WHITE}
ORDER = ["shell", "frame_L", "frame_R", "base", "sleeve", "head", "top"]


def build_print():
    out = os.path.join(ROOT, "print")
    os.makedirs(os.path.join(out, "stl"), exist_ok=True)
    d, meshes = build_kit_meshes()
    posed = {n: to_print_pose(n, m) for n, m in meshes.items()}
    for i, n in enumerate(ORDER, 1):
        col = "BLACK" if KIT_COLOUR[n] == BLACK else "WHITE"
        posed[n].export(os.path.join(out, "stl", f"{i:02d}_{NICE_NAMES[n]}_{col}.stl"))
    blacks = [n for n in ORDER if KIT_COLOUR[n] == BLACK]
    whites = [n for n in ORDER if KIT_COLOUR[n] == WHITE]
    for tag, names in (("BLACK", blacks), ("WHITE", whites)):
        placed = layout(posed, names, gap=8.0, bed=(200.0, 200.0))
        write_3mf(os.path.join(out, f"DELTA_1-6_{tag}_plate.3mf"),
                  [(NICE_NAMES[n], placed[n], KIT_COLOUR[n]) for n in names])
    write_3mf(os.path.join(out, "DELTA_1-6_assembled_preview.3mf"),
              [(NICE_NAMES[n], meshes[n], KIT_COLOUR[n]) for n in ORDER])
    return d, meshes, posed


def build_real(step=False):
    out = os.path.join(ROOT, "models")
    os.makedirs(os.path.join(out, "stl"), exist_ok=True)
    d = Design("real", ribs=True)
    solids = {"frame_L": d.frame(+1), "frame_R": d.frame(-1), "base": d.base(),
              "sleeve": d.sleeve(), "head": d.head(), "top": d.top()}
    meshes = {"shell": d.shell_mesh()}
    for n, s in solids.items():
        meshes[n] = to_trimesh(s, 0.15, 0.12)
    for n in ORDER:
        meshes[n].export(os.path.join(out, "stl", f"{NICE_NAMES[n]}_full-size_mm.stl"))
    named = [(NICE_NAMES[n], meshes[n], COLORS_REAL[n]) for n in ORDER]
    export_glb(named, os.path.join(out, "DELTA_chair-desk_full-size.glb"))
    metal = {NICE_NAMES[n]: 0.55 for n in ("base", "sleeve", "head")}
    export_usdz(named, os.path.join(out, "DELTA_chair-desk_AR.usdz"), metallic=metal)
    if step:
        solids["shell"] = Design("real", ribs=False).shell()
        export_step([(NICE_NAMES[n], solids[n], COLORS_REAL[n]) for n in ORDER],
                    os.path.join(out, "DELTA_chair-desk_full-size.step"))
    return d, meshes


if __name__ == "__main__":
    t = time.time()
    build_print()
    print(f"print kit done  {time.time() - t:.0f}s")
    build_real(step="--step" in sys.argv)
    print(f"full size done  {time.time() - t:.0f}s")
