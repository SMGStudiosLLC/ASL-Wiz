"""
1:6 print kit: builds every part in print mode, turns each into its print
orientation (no supports needed), lays parts out on a black plate and a white
plate, and writes STL + 3MF files.
"""
import math
import numpy as np
import trimesh

from . import params as P
from .design import Design, COLORS_PRINT
from .mesh import to_trimesh

TOL, ANG = 0.02, 0.12

# how each part is turned for printing (rotation about X in degrees)
#   shell    on its side (seat skirt on the bed): bending of the back runs along the layers
#   frames   inner face down: the smooth top surface is the visible outer face; tabs sit on the bed
#   sleeve   on its side, pin hole vertical
#   head     on its side: post layers run along its length (strong), 45-degree dovetail prints clean
#   top      upside down: writing surface on the bed (smooth), track opens upward
PRINT_ROT = {"shell": 90, "frame_L": 90, "frame_R": -90, "base": 0, "sleeve": 90, "head": 90, "top": 180}

NICE_NAMES = {
    "shell": "seat_shell", "frame_L": "frame_left", "frame_R": "frame_right",
    "base": "floor_base", "sleeve": "post_lower_sleeve", "head": "post_upper_head", "top": "desktop",
}


def build_kit_meshes(hi=P.DEFAULT_HEIGHT_INDEX, gi=P.DEFAULT_GAP_INDEX):
    d = Design("print")
    meshes = {"shell": d.shell_mesh()}
    for name, fn in [("frame_L", lambda: d.frame(+1)), ("frame_R", lambda: d.frame(-1)),
                     ("base", d.base), ("sleeve", d.sleeve), ("head", lambda: d.head(hi)),
                     ("top", lambda: d.top(hi, gi))]:
        meshes[name] = to_trimesh(fn(), TOL, ANG)
    return d, meshes


def to_print_pose(name, m):
    m = m.copy()
    R = trimesh.transformations.rotation_matrix(math.radians(PRINT_ROT[name]), [1, 0, 0])
    m.apply_transform(R)
    lo = m.bounds[0]
    m.apply_translation([-lo[0], -lo[1], -lo[2]])
    return m


def layout(meshes, names, gap=6.0, bed=(220.0, 220.0)):
    """Simple shelf packing, biggest first. Returns dict name -> placed mesh."""
    items = sorted(names, key=lambda n: -meshes[n].extents[0] * meshes[n].extents[1])
    placed, x, y, row_h = {}, 0.0, 0.0, 0.0
    for n in items:
        m = meshes[n].copy()
        ex, ey = m.extents[0], m.extents[1]
        if ex > ey and ex > bed[0] * 0.6:
            pass
        if x + ex > bed[0]:
            x, y, row_h = 0.0, y + row_h + gap, 0.0
        m.apply_translation([x, y, 0])
        placed[n] = m
        x += ex + gap
        row_h = max(row_h, ey)
    # centre the whole group on the bed
    allb = np.array([p.bounds for p in placed.values()])
    lo, hi = allb[:, 0, :2].min(0), allb[:, 1, :2].max(0)
    off = (np.array(bed) - (hi - lo)) / 2 - lo
    for m in placed.values():
        m.apply_translation([off[0], off[1], 0])
    return placed


def write_3mf(path, objects):
    """Minimal 3MF (core spec) with per-object colours. objects: list of (name, mesh, rgb_hex)."""
    import zipfile
    colours = []
    for _, _, c in objects:
        if c not in colours:
            colours.append(c)
    res = ['<basematerials id="1">']
    for c in colours:
        res.append(f'<base name="{c}" displaycolor="{c}FF"/>')
    res.append('</basematerials>')
    build = []
    for i, (name, m, c) in enumerate(objects):
        oid = i + 2
        v = "".join(f'<vertex x="{x:.4f}" y="{y:.4f}" z="{z:.4f}"/>' for x, y, z in m.vertices)
        t = "".join(f'<triangle v1="{a}" v2="{b}" v3="{cc}"/>' for a, b, cc in m.faces)
        res.append(f'<object id="{oid}" name="{name}" type="model" pid="1" pindex="{colours.index(c)}">'
                   f'<mesh><vertices>{v}</vertices><triangles>{t}</triangles></mesh></object>')
        build.append(f'<item objectid="{oid}"/>')
    model = ('<?xml version="1.0" encoding="UTF-8"?>\n'
             '<model unit="millimeter" xml:lang="en-US" '
             'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">'
             '<metadata name="Title">DELTA chair-desk</metadata>'
             f'<resources>{"".join(res)}</resources><build>{"".join(build)}</build></model>')
    ctypes = ('<?xml version="1.0" encoding="UTF-8"?>\n'
              '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
              '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
              '<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>'
              '</Types>')
    rels = ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Target="/3D/3dmodel.model" Id="rel0" '
            'Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", ctypes)
        z.writestr("_rels/.rels", rels)
        z.writestr("3D/3dmodel.model", model)
