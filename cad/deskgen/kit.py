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
#   sleeve   standing up: the bore needs no bridging, so the post slides cleanly
#   head     on its side: post layers run along its length (strong), 45-degree dovetail prints clean
#   top      upside down: writing surface on the bed (smooth), track opens upward
PRINT_ROT = {"shell": 90, "frame_L": 90, "frame_R": -90, "base": 0, "sleeve": 0, "head": 90, "top": 180,
             "plug": 180}

NICE_NAMES = {
    "shell": "seat_shell", "frame_L": "frame_left", "frame_R": "frame_right",
    "base": "floor_base", "sleeve": "post_lower_sleeve", "head": "post_upper_head", "top": "desktop",
    "plug": "track_end_plug", "seat_beam": "seat_beam",
}


def build_kit_meshes(hi=P.DEFAULT_HEIGHT_INDEX, gi=P.DEFAULT_GAP_INDEX):
    d = Design("print")
    meshes = {"shell": d.shell_mesh()}
    for name, fn in [("frame_L", lambda: d.frame(+1)), ("frame_R", lambda: d.frame(-1)),
                     ("base", d.base), ("sleeve", d.sleeve), ("head", lambda: d.head(hi)),
                     ("top", lambda: d.top(hi, gi)), ("plug", lambda: d.plug(hi, gi))]:
        meshes[name] = to_trimesh(fn(), TOL, ANG)
    return d, meshes


def shell_support(d):
    """Breakaway support fin(s) for the shell, in assembled coordinates."""
    from .shell import support_fin_mesh
    return support_fin_mesh(d.g)


def to_print_pose(name, m):
    m = m.copy()
    R = trimesh.transformations.rotation_matrix(math.radians(PRINT_ROT[name]), [1, 0, 0])
    m.apply_transform(R)
    lo = m.bounds[0]
    m.apply_translation([-lo[0], -lo[1], -lo[2]])
    return m


def layout(meshes, names, gap=6.0, bed=(220.0, 220.0), margin=6.0):
    """Shelf packing that tries every part order and 90-degree turns about Z, and keeps the
    smallest arrangement that fits inside the bed (minus a margin for brims).
    Returns dict name -> placed mesh."""
    import itertools
    import trimesh
    ext = {n: meshes[n].extents[:2] for n in names}
    usable = np.array(bed) - 2 * margin

    def pack(order, rots):
        pos, x, y, row_h, w = {}, 0.0, 0.0, 0.0, 0.0
        for n, r in zip(order, rots):
            ex, ey = (ext[n][::-1] if r else ext[n])
            if x > 0 and x + ex > usable[0]:
                x, y, row_h = 0.0, y + row_h + gap, 0.0
            pos[n] = (x, y, r)
            x += ex + gap
            w = max(w, x - gap)
            row_h = max(row_h, ey)
        return pos, w, y + row_h

    best = None
    for order in itertools.permutations(names):
        for rots in itertools.product((0, 1), repeat=len(names)):
            pos, w, h = pack(order, rots)
            if w <= usable[0] + 1e-6 and h <= usable[1] + 1e-6:
                score = max(w, h) + 0.01 * (w + h)
                if best is None or score < best[0]:
                    best = (score, pos, w, h)
    if best is None:
        raise ValueError(f"parts {names} do not fit on a {bed} bed")
    _, pos, w, h = best
    off = (np.array(bed) - np.array([w, h])) / 2
    placed = {}
    for n, (x, y, r) in pos.items():
        m = meshes[n].copy()
        if r:
            m.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [0, 0, 1]))
        m.apply_translation(-m.bounds[0] * np.array([1, 1, 0]))
        m.apply_translation([x + off[0], y + off[1], 0])
        placed[n] = m
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
