#!/usr/bin/env python3
"""
Render the image set in renders/ (run cad/build.py first).

    python cad/render_all.py
"""
import math
import os
import sys

import numpy as np
import trimesh
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from deskgen import params as P                          # noqa: E402
from deskgen.design import Design                         # noqa: E402
from deskgen.mesh import to_trimesh                       # noqa: E402
from deskgen.kit import build_kit_meshes, to_print_pose, layout, NICE_NAMES  # noqa: E402
from deskgen.render import render                         # noqa: E402

OUT = os.path.join(ROOT, "renders")
BG = (0.955, 0.955, 0.96)
MAT = {"shell": "black_pp", "seat_beam": "black_pp", "frame_L": "black_pp", "frame_R": "black_pp",
       "base": "alu", "sleeve": "alu", "head": "alu", "top": "white", "plug": "white"}
KITMAT = {"shell": "black_pla", "frame_L": "black_pla", "frame_R": "black_pla",
          "base": "white_pla", "sleeve": "white_pla", "head": "white_pla", "top": "white_pla", "plug": "white_pla"}
INK = (40, 40, 44)
SUB = (110, 110, 118)


def font(size, bold=False):
    for f in (["DejaVuSans-Bold.ttf"] if bold else ["DejaVuSans.ttf"]):
        for d in ("/usr/share/fonts/truetype/dejavu", "/usr/share/fonts/TTF", "/usr/share/fonts"):
            p = os.path.join(d, f)
            if os.path.exists(p):
                return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def caption(path, title, sub=None):
    """Title band above the image so text is always legible."""
    im = Image.open(path).convert("RGB")
    band = 130
    out = Image.new("RGB", (im.width, im.height + band), (255, 255, 255))
    out.paste(im, (0, band))
    d = ImageDraw.Draw(out)
    d.text((48, 30), title, fill=INK, font=font(34, True))
    if sub:
        d.text((48, 80), sub, fill=SUB, font=font(22))
    out.save(path)


def real_meshes(hi=P.DEFAULT_HEIGHT_INDEX, gi=P.DEFAULT_GAP_INDEX, d=None, shell=None):
    d = d or Design("real", ribs=True)
    m = {"shell": shell if shell is not None else d.shell_mesh()}
    for n, f in [("seat_beam", d.seat_beam), ("frame_L", lambda: d.frame(+1)), ("frame_R", lambda: d.frame(-1)),
                 ("base", d.base), ("sleeve", d.sleeve), ("head", lambda: d.head(hi)),
                 ("top", lambda: d.top(hi, gi)), ("plug", lambda: d.plug(hi, gi))]:
        m[n] = to_trimesh(f(), 0.15, 0.12)
    return d, m


def items(meshes, mats=MAT, opacity=1.0):
    return [(m, mats[n], opacity) for n, m in meshes.items()]


def to_px(info, p):
    W, H = info["size"]
    rel = np.asarray(p, float) - info["ctr"]
    u, v = rel @ info["right"], rel @ info["up"]
    s = (H / 2) / info["scale"]
    return (W / 2 + u * s, H / 2 - v * s)


def dim_line(d, a, b, text, off=(0, 0), fnt=None, col=INK, above=False):
    fnt = fnt or font(22)
    a = (a[0] + off[0], a[1] + off[1])
    b = (b[0] + off[0], b[1] + off[1])
    d.line([a, b], fill=col, width=2)
    ang = math.atan2(b[1] - a[1], b[0] - a[0])
    for p, sgn in ((a, 1), (b, -1)):
        for da in (0.45, -0.45):
            q = (p[0] + sgn * 14 * math.cos(ang + da), p[1] + sgn * 14 * math.sin(ang + da))
            d.line([p, q], fill=col, width=2)
    mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
    if above:
        my -= 26
    tw = d.textlength(text, font=fnt)
    box = (mx - tw / 2 - 6, my - 15, mx + tw / 2 + 6, my + 15)
    d.rectangle(box, fill=(246, 246, 247))
    d.text((mx - tw / 2, my - 13), text, fill=col, font=fnt)


def mm_in(v):
    return f"{v:.0f} mm  /  {v / 25.4:.1f} in"


# ------------------------------------------------------------------ manikin
def capsule(p0, p1, r):
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
    L = np.linalg.norm(p1 - p0)
    c = trimesh.creation.capsule(height=max(L, 1e-3), radius=r, count=[16, 16])
    z = np.array([0, 0, 1.0])
    d = (p1 - p0) / max(L, 1e-9)
    ax = np.cross(z, d)
    if np.linalg.norm(ax) > 1e-9:
        ang = math.acos(np.clip(z @ d, -1, 1))
        c.apply_transform(trimesh.transformations.rotation_matrix(ang, ax))
    elif d[2] < 0:
        c.apply_transform(trimesh.transformations.rotation_matrix(math.pi, [1, 0, 0]))
    c.apply_translation((p0 + p1) / 2)
    return c


def manikin(a, seat_surface_z, feet_z, desk_z, back_x=12.0, lean_deg=11.0):
    """Simple seated figure from anthropometric data (cm), in the design's coordinates (mm)."""
    cm, y = 10.0, 95.0
    r_t = a["abdo"] * cm * 0.40                       # torso half-depth
    hip = np.array([back_x + r_t + 8, 0, seat_surface_z + r_t * 0.8])
    thigh_r = a["thigh"] * cm * 0.46
    pop = a["popliteal"] * cm + 25                    # with shoes
    knee_z = max(feet_z + pop + 40, seat_surface_z + thigh_r)
    knee = np.array([back_x + a["bkl"] * cm - 50, 0, knee_z])
    shin = pop - 30
    ankle_z = feet_z + 70
    dz = knee[2] - ankle_z
    if dz >= shin:
        ankle = knee + np.array([0, 0, -shin])        # feet dangle
    else:
        ankle = np.array([knee[0] + math.sqrt(shin ** 2 - dz ** 2) * 0.35, 0, ankle_z])
        ankle[0] = knee[0] + math.sqrt(max(shin ** 2 - (knee[2] - ankle[2]) ** 2, 0.0)) * 0.35
    toe = ankle + np.array([150, 0, -45])
    t = math.radians(lean_deg)
    sh_h = a["shoulder"] * cm - r_t * 0.8
    shoulder = hip + np.array([-sh_h * math.sin(t), 0, sh_h * math.cos(t)])
    neck = shoulder + np.array([-10, 0, 60])
    head_c = neck + np.array([10, 0, 115])
    elbow = np.array([shoulder[0] + 60, 0, seat_surface_z + a["elbow"] * cm])
    hand = np.array([elbow[0] + 250, 0, max(desk_z + 22, elbow[2])])
    parts = []
    for sgn in (-1, 1):
        o = np.array([0, sgn * y, 0])
        parts += [capsule(hip + o, knee + o, thigh_r), capsule(knee + o, ankle + o, 46),
                  capsule(ankle + o, toe + o, 36),
                  capsule(shoulder + o * 1.8, elbow + o * 2.0, 40), capsule(elbow + o * 2.0, hand + o * 1.5, 34)]
    parts.append(capsule(hip, shoulder - np.array([0, 0, 40]), r_t))
    parts.append(capsule(shoulder + np.array([0, -165, 0]), shoulder + np.array([0, 165, 0]), 55))
    parts.append(capsule(neck - np.array([0, 0, 40]), neck + np.array([0, 0, 30]), 45))
    head = trimesh.creation.icosphere(subdivisions=3, radius=95)
    head.apply_translation(head_c)
    parts.append(head)
    return trimesh.util.concatenate(parts)


def main():
    os.makedirs(OUT, exist_ok=True)
    d, M = real_meshes()
    shell_mesh = M["shell"]

    info = render(items(M), os.path.join(OUT, "01_hero.png"), bg_flat=BG, view=(-1.0, -1.35, 0.62))
    caption(os.path.join(OUT, "01_hero.png"), "DELTA chair-desk",
            "One-piece flexing shell  /  rounded-triangle frames  /  centre spine  /  sliding, height-adjustable top")
    render(items(M), os.path.join(OUT, "02_rear.png"), bg_flat=BG, view=(-1.25, 0.95, 0.55))
    caption(os.path.join(OUT, "02_rear.png"), "Rear three-quarter",
            "Smooth one-piece back: no slots, no fasteners and no metal anywhere near your hair")

    # side elevation with dimensions
    p = os.path.join(OUT, "03_side_elevation.png")
    info = render(items(M), p, view=(0, -1, 0), ortho=True, ssao=False, zoom=0.95, bg_flat=(1, 1, 1), floor=False,
                  target=np.array([380.0, 0.0, 400.0]))
    im = Image.open(p).convert("RGB")
    dr = ImageDraw.Draw(im)
    hi, gi = P.DEFAULT_HEIGHT_INDEX, P.DEFAULT_GAP_INDEX
    xn = P.desk_near_x(gi)
    far = xn + P.TOP_D
    zt = P.DESK_HEIGHTS[hi]
    xmin = float(min(m.bounds[0][0] for m in M.values()))
    xmax = float(max(m.bounds[1][0] for m in M.values()))
    ztop = float(shell_mesh.bounds[1][2])
    dim_line(dr, to_px(info, (xmin, 0, -60)), to_px(info, (xmax, 0, -60)),
             f"overall {mm_in(xmax - xmin)}  (reach {P.DESK_GAPS[gi]:.0f})")
    dim_line(dr, to_px(info, (far + 70, 0, 0)), to_px(info, (far + 70, 0, zt)),
             f"desk {P.DESK_HEIGHTS[0]:.0f}-{P.DESK_HEIGHTS[-1]:.0f} mm")
    dim_line(dr, to_px(info, (455, 0, 0)), to_px(info, (455, 0, P.SEAT_HEIGHT)), f"seat {P.SEAT_HEIGHT:.0f} mm")
    dim_line(dr, to_px(info, (xmin - 60, 0, 0)), to_px(info, (xmin - 60, 0, ztop)), mm_in(ztop))
    dim_line(dr, to_px(info, (P.BACK_X_AT_ELBOW, 0, zt + 70)), to_px(info, (xn, 0, zt + 70)),
             "reach " + "/".join(f"{g:.0f}" for g in P.DESK_GAPS) + " mm", above=True)
    im.save(p)
    caption(p, "Side elevation", "Dimensions in mm. Reach is measured from the backrest at elbow height "
            "to the desk's near corners (20 mm more at the middle of the curved edge).")

    # front elevation and plan
    p = os.path.join(OUT, "04_front_elevation.png")
    info = render(items(M), p, view=(1, 0, 0), ortho=True, ssao=False, zoom=0.95, bg_flat=(1, 1, 1), floor=False,
                  target=np.array([0.0, 0.0, 400.0]))
    im = Image.open(p).convert("RGB")
    dr = ImageDraw.Draw(im)
    dim_line(dr, to_px(info, (0, -P.TOP_W / 2, P.DESK_HEIGHTS[hi] + 80)),
             to_px(info, (0, P.TOP_W / 2, P.DESK_HEIGHTS[hi] + 80)), f"desk far edge {mm_in(P.TOP_W)}")
    dim_line(dr, to_px(info, (0, -P.TFOOT_HALF_W, -60)), to_px(info, (0, P.TFOOT_HALF_W, -60)),
             f"floor footprint {mm_in(2 * P.TFOOT_HALF_W)}")
    im.save(p)
    caption(p, "Front elevation (from the teacher's side)", "Single centre post; both sides of the seat are open")

    p = os.path.join(OUT, "05_plan.png")
    info = render(items(M), p, view=(0.0001, 0, 1), up=(1, 0, 0), ortho=True, ssao=False, zoom=0.92,
                  bg_flat=(1, 1, 1), floor=False)
    im = Image.open(p).convert("RGB")
    dr = ImageDraw.Draw(im)
    dim_line(dr, to_px(info, (xn - 40, -P.TOP_W_NEAR / 2, 900)), to_px(info, (xn - 40, P.TOP_W_NEAR / 2, 900)),
             f"near edge {P.TOP_W_NEAR:.0f}")
    dim_line(dr, to_px(info, (far + 45, -P.TOP_W / 2, 900)), to_px(info, (far + 45, P.TOP_W / 2, 900)),
             f"far edge {P.TOP_W:.0f}")
    im.save(p)
    caption(p, "Plan", "Tapered top: narrow at the student for easy side entry, wide where the work happens")

    # underside (model flipped so the studio lights reach it)
    flip = trimesh.transformations.rotation_matrix(math.pi, [1, 0, 0])
    Mf = {n: m.copy().apply_transform(flip) for n, m in M.items()}
    render(items(Mf), os.path.join(OUT, "06_underside.png"), bg_flat=BG, view=(-0.9, 1.0, 0.75), floor=False)
    caption(os.path.join(OUT, "06_underside.png"), "Underside",
            "Moulded ribs under the seat; bearing pads where the frames meet the shell; dovetail slide under the top")

    # back texture close-up
    tgt = np.array([0.0, 0.0, P.SEAT_HEIGHT + 230])
    render([(shell_mesh, ((0.16, 0.16, 0.17), 0.85, 0.55, 30))], os.path.join(OUT, "07_grip_texture.png"),
           target=tgt, view=(1.0, -0.6, 0.35), zoom=1.8, bg_flat=BG, floor=False, size=(1600, 1200))
    caption(os.path.join(OUT, "07_grip_texture.png"), "Grip texture",
            "Fine moulded ribs across the backrest so you do not slide; smooth everywhere else for easy cleaning")

    # fit: small and tall student
    from deskgen.analysis import ANTHRO
    tiles = []
    for who, label, hi2, gi2 in (("F5", "Small: 5th percentile female", 0, 0),
                                  ("M95", "Tall: 95th percentile male", 3, 3),
                                  ("Large", "Larger body: 54 cm hips, 38 cm belly depth", 2, 3)):
        d2, M2 = real_meshes(hi2, gi2, d=d, shell=shell_mesh)
        a = dict(ANTHRO[who])
        pop = a["popliteal"] * 10 + 25
        feet = P.BASE_H if pop < P.SEAT_HEIGHT else 0.0
        man = manikin(a, P.SEAT_HEIGHT - 15, feet, P.DESK_HEIGHTS[hi2])
        pth = os.path.join(OUT, f"_fit_{who}.png")
        render(items(M2) + [(man, "person", 1.0)], pth, view=(0, -1, 0), ortho=True, ssao=False, zoom=0.74,
               bg_flat=(1, 1, 1), floor=False, size=(1200, 1300),
               target=np.array([370, 0, 690]))
        im = Image.open(pth).convert("RGB")
        dr = ImageDraw.Draw(im)
        dr.rectangle((0, 0, im.width, 130), fill=(255, 255, 255))
        dr.text((40, 40), label, fill=INK, font=font(30, True))
        sub = (f"desk {P.DESK_HEIGHTS[hi2]:.0f} mm, reach {P.DESK_GAPS[gi2]:.0f} mm"
               + ("; feet on the spine footrest" if feet > 0 else "; feet on the floor"))
        dr.text((40, 84), sub, fill=SUB, font=font(22))
        tiles.append(im)
        os.remove(pth)
    W = sum(t.width for t in tiles)
    fit = Image.new("RGB", (W, tiles[0].height), (255, 255, 255))
    x = 0
    for t in tiles:
        fit.paste(t, (x, 0))
        x += t.width
    fit.save(os.path.join(OUT, "08_fit_students.png"))

    # adjustability: lowest/nearest and highest/farthest desk ghosted over the default
    ghost = []
    for hi2, gi2 in ((0, 0), (len(P.DESK_HEIGHTS) - 1, len(P.DESK_GAPS) - 1)):
        dd = Design("real")
        ghost += [(to_trimesh(dd.top(hi2, gi2), 0.3, 0.2), "person", 1.0),
                  (to_trimesh(dd.head(hi2), 0.3, 0.2), "person", 1.0)]
    p = os.path.join(OUT, "09_adjustment_range.png")
    render(items(M) + ghost, p, view=(0, -1, 0), ortho=True, ssao=False, zoom=1.05, bg_flat=(1, 1, 1), floor=False)
    caption(p, "Adjustment range",
            f"Height {P.DESK_HEIGHTS[0]:.0f}-{P.DESK_HEIGHTS[-1]:.0f} mm in {len(P.DESK_HEIGHTS)} steps; "
            f"reach {P.DESK_GAPS[0]:.0f}-{P.DESK_GAPS[-1]:.0f} mm in {len(P.DESK_GAPS)} steps (ghosted: the extremes)")

    # print kit: exploded + plates
    dk, K = build_kit_meshes()
    ex = {"shell": (0, 0, 22), "frame_L": (0, 22, 0), "frame_R": (0, -22, 0), "base": (0, 0, -16),
          "sleeve": (0, 0, 6), "head": (0, 0, 30), "top": (0, 0, 50), "plug": (14, 0, 50)}
    Ke = {n: m.copy().apply_translation(ex[n]) for n, m in K.items()}
    render(items(Ke, KITMAT), os.path.join(OUT, "10_print_kit_exploded.png"), bg_flat=BG,
           view=(-1.0, -1.3, 0.7), floor=False)
    caption(os.path.join(OUT, "10_print_kit_exploded.png"), "1:6 print kit, exploded",
            "8 parts: 3 black, 5 white. Pins are short pieces of 1.75 mm filament.")
    from deskgen.kit import shell_support
    shell_print = trimesh.util.concatenate([K["shell"]] + shell_support(dk))
    posed = {n: to_print_pose(n, (shell_print if n == "shell" else m)) for n, m in K.items()}
    blk = layout(posed, ["shell", "frame_L", "frame_R"], gap=8, bed=(200, 200))
    wht = layout(posed, ["base", "sleeve", "head", "top", "plug"], gap=8, bed=(200, 200))
    for n, m in wht.items():
        m.apply_translation([230, 0, 0])
    plates = [(m, "black_pla") for m in blk.values()] + [(m, "white_pla") for m in wht.values()]
    beds = []
    for x0 in (0, 230):
        b = trimesh.creation.box(extents=[200, 200, 1.0])
        b.apply_translation([x0 + 100, 100, -0.6])
        beds.append((b, ((0.60, 0.61, 0.64), 0.9, 0.1, 10)))
    render(plates + beds, os.path.join(OUT, "11_print_plates.png"), bg_flat=BG,
           view=(0.0, -0.0001, 1.0), up=(0, 1, 0), ortho=True, ssao=False, floor=False, size=(1800, 1000), zoom=1.15)
    caption(os.path.join(OUT, "11_print_plates.png"), "Print plates (200 x 200 mm)",
            "Left: black PLA. Right: white PLA. Every part is already oriented to print without supports.")
    print("renders written to", OUT)


if __name__ == "__main__":
    main()
