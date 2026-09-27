"""
Desk side: telescoping post, sliding head, and the desktop.

  sleeve   lower (outer) post, plugged into the T-foot boss; one lock-pin hole
  head     upper (inner) post with 4 height holes + a dovetail wing on top
  top      desktop with a dovetail track underneath (3 index holes) and a pencil cove

Height: 4 settings, 1 in apart (26.8 / 27.8 / 28.7 / 29.7 in).
Reach:  3 settings, 50 mm apart; slides the top toward/away from the student.
"""
import math
import numpy as np
import cadquery as cq

from . import params as P
from .geom import box, rrect_prism, teardrop_hole_y
from .base import sleeve_bottom_z

TENON_H = 10.0          # dovetail depth recessed into the desktop
TENON_W_TOP = 46.0
TENON_W_BOT = 26.0      # 45-degree dovetail flanks (prints cleanly on its side)
TENON_X0_OFF = -200.0   # tenon runs from post-200 to post+20
TENON_X1_OFF = 20.0
DETENT_OFF = -160.0     # index pin location relative to the post centre
INNER_LEN = 390.0       # inner post length below the tenon


def rail_top_z(k, hi):
    return (P.DESK_HEIGHTS[hi] - P.TOP_T) * k


def hole_depths(k):
    """Depth of each height hole below the tenon's top face (aligned with the sleeve pin)."""
    return [(h - P.TOP_T - P.SLEEVE_PIN_Z) * k for h in P.DESK_HEIGHTS]


def build_sleeve(k, mode, kit=None):
    sx, sy = P.SLEEVE
    ix, iy = P.INNER
    c = kit["slide"] if mode == "print" else 1.0 * k
    z0, z1 = sleeve_bottom_z(k), P.SLEEVE_TOP * k
    outer = rrect_prism(P.POST_X * k, 0, sx * k, sy * k, P.POST_R * k, z0, z1)
    top = [e for e in outer.Edges() if abs(e.Center().z - z1) < 1e-6]
    outer = outer.fillet(3 * k if mode == "real" else 0.6, top)
    bore = rrect_prism(P.POST_X * k, 0, ix * k + 2 * c, iy * k + 2 * c, P.POST_R * k * 0.6,
                       z0 - 1, z1 + 1)
    s = outer.cut(bore)
    d = kit["pin_hole"] if mode == "print" else 10 * k
    pin = cq.Solid.makeCylinder(d / 2, sy * k + 4, cq.Vector(P.POST_X * k, -sy * k / 2 - 2, P.SLEEVE_PIN_Z * k),
                                cq.Vector(0, 1, 0))
    return s.cut(pin).clean()


def build_head(k, mode, hi, kit=None):
    ix, iy = P.INNER
    zt = rail_top_z(k, hi)
    th = TENON_H * k
    x0 = (P.POST_X + TENON_X0_OFF) * k
    x1 = (P.POST_X + TENON_X1_OFF) * k
    wt, wb = TENON_W_TOP * k, TENON_W_BOT * k
    # dovetail tenon, extruded along X
    prof = (cq.Workplane("YZ", origin=(x0, 0, 0))
            .polyline([(-wb / 2, zt - th), (wb / 2, zt - th), (wt / 2, zt), (-wt / 2, zt)]).close()
            .extrude(x1 - x0).val())
    ends = [e for e in prof.Edges() if abs(e.Center().x - x0) < 1e-6 or abs(e.Center().x - x1) < 1e-6]
    for rr in ((4.0 * k, 3.0 * k, 2.0 * k) if mode == "real" else (0.5, 0.35)):
        try:
            cand = prof.fillet(rr, ends)
            if cand.isValid():
                prof = cand
                break
        except Exception:
            pass
    # inner post hanging below the tenon
    zb = zt - th - INNER_LEN * k
    post = rrect_prism(P.POST_X * k, 0, ix * k, iy * k, P.POST_R * k * 0.6, zb, zt - th + 0.5)
    bot = [e for e in post.Edges() if abs(e.Center().z - zb) < 1e-6]
    post = post.fillet(2 * k if mode == "real" else 0.4, bot)
    head = prof.fuse(post)
    # guide boss under the tenon for the reach index pin
    xd = (P.POST_X + DETENT_OFF) * k
    boss_h = 18 * k
    boss = cq.Solid.makeCylinder(15 * k, boss_h + 0.5, cq.Vector(xd, 0, zt - th - boss_h), cq.Vector(0, 0, 1))
    try:
        boss = boss.fillet(3 * k if mode == "real" else 0.4,
                           [e for e in boss.Edges() if abs(e.Center().z - (zt - th - boss_h)) < 1e-6])
    except Exception:
        pass
    head = head.fuse(boss).clean()
    d = kit["pin_hole"] if mode == "print" else 10 * k
    zlo, zhi = zt - th - boss_h - 1, zt + 1
    if mode == "print":
        # printed lying on its side (+Y up), so this vertical hole is horizontal in the print:
        # give it a 45-degree teardrop roof toward +Y
        r = d / 2
        circ = cq.Solid.makeCylinder(r, zhi - zlo, cq.Vector(xd, 0, zlo), cq.Vector(0, 0, 1))
        roof = (cq.Workplane("XY", origin=(0, 0, zlo))
                .polyline([(xd - r * 0.7071, r * 0.7071), (xd, r * 1.4142), (xd + r * 0.7071, r * 0.7071), (xd, 0)])
                .close().extrude(zhi - zlo).val())
        head = head.cut(circ.fuse(roof))
    else:
        head = head.cut(cq.Solid.makeCylinder(d / 2, zhi - zlo, cq.Vector(xd, 0, zlo), cq.Vector(0, 0, 1)))
    # height holes, along Y (vertical in the print orientation)
    for dep in hole_depths(k):
        z = zt - dep
        hole = cq.Solid.makeCylinder(d / 2, iy * k * 2 + 2, cq.Vector(P.POST_X * k, -iy * k - 1, z), cq.Vector(0, 1, 0))
        head = head.cut(hole)
    return head.clean()


def build_top(k, mode, hi, gi, kit=None):
    zt = P.DESK_HEIGHTS[hi] * k
    t = P.TOP_T * k
    xn = P.desk_near_x(gi) * k
    D, W = P.TOP_D * k, P.TOP_W * k
    top = rrect_prism(xn + D / 2, 0, D, W, P.TOP_CORNER_R * k, zt - t, zt)
    er = P.TOP_EDGE_R * k
    top_edges = [e for e in top.Edges() if abs(e.Center().z - zt) < 1e-6]
    top = top.fillet(er, top_edges)
    bot_edges = [e for e in top.Edges() if abs(e.Center().z - (zt - t)) < 1e-6]
    top = top.fillet(er if mode == "real" else 0.8, bot_edges)

    # pencil cove with ramped, wipe-out ends
    xc = xn + D - P.COVE_FROM_FAR * k
    half_w, dep = P.COVE_W * k / 2, P.COVE_D * k
    rc = (half_w ** 2 + dep ** 2) / (2 * dep)
    zc = zt + rc - dep
    hl = P.COVE_LEN * k / 2
    ramp = 45 * k
    pts = [cq.Vector(xc, y, zc + dz) for y, dz in [
        (-hl - 4 * k, dep * 1.25), (-hl + ramp * 0.35, dep * 0.45), (-hl + ramp, 0.0),
        (0.0, 0.0), (hl - ramp, 0.0), (hl - ramp * 0.35, dep * 0.45), (hl + 4 * k, dep * 1.25)]]
    path = cq.Wire.assembleEdges([cq.Edge.makeSpline(pts)])
    tan = (pts[1] - pts[0]).normalized()
    cutter = cq.Solid.sweep(cq.Wire.makeCircle(rc, pts[0], tan), [], path, makeSolid=True)
    top = top.cut(cutter)

    # dovetail track underneath, open at the far edge
    c = kit["slide"] if mode == "print" else 0.5 * k
    th = TENON_H * k + (0.25 if mode == "print" else 0)
    wt = TENON_W_TOP * k + 2 * c
    wb = TENON_W_BOT * k + 2 * c
    zb = zt - t
    tx0 = xn + 160 * k
    track = (cq.Workplane("YZ", origin=(tx0, 0, 0))
             .polyline([(-wb / 2, zb - 0.01), (wb / 2, zb - 0.01), (wt / 2, zb + th), (-wt / 2, zb + th)]).close()
             .extrude(D + 10 * k).val())
    top = top.cut(track)
    # three index holes for the reach pin
    d = kit["pin_hole"] if mode == "print" else 10 * k
    dep_h = th + (2.2 if mode == "print" else 12 * k)
    for g in range(len(P.DESK_GAPS)):
        xd = (P.POST_X + DETENT_OFF) * k - (P.desk_near_x(g) * k - xn)
        top = top.cut(cq.Solid.makeCylinder(d / 2, dep_h, cq.Vector(xd, 0, zb - 0.01), cq.Vector(0, 0, 1)))
    return top.clean()
