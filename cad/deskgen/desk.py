"""
Desk side: telescoping post, sliding head, desktop and track end plug.

  sleeve   lower (outer) post, pressed into the T-foot boss; one lock-pin hole (front to back)
  head     upper (inner) post with 5 height holes, plus a dovetail tenon that rides
           inside a track in the desktop's underside
  top      desktop: tapered, belly cut, pencil groove, dovetail track, 3 index holes
  plug     closes the track's far end after the desktop is slid on

Height: 5 settings, 1 in apart (25.8 to 29.7 in). The inner post is long enough to
bottom out at the lowest setting, so pulling the pin can never drop the desk lower.
Reach:  3 settings, 50 mm apart, locked by an index pin just behind the post.
"""
import math
import cadquery as cq

from . import params as P
from .geom import box, rrect_prism
from .base import sleeve_bottom_z


def underside_z(k, hi):
    return (P.DESK_HEIGHTS[hi] - P.TOP_T) * k


def _gap(k, mode, kit):
    return kit["head_gap"] if mode == "print" else P.HEAD_GAP * k


def hole_depths(k):
    """Distance of each height hole below the desk underside (aligned with the sleeve pin)."""
    return [(h - P.TOP_T - P.SLEEVE_PIN_Z) * k for h in P.DESK_HEIGHTS]


def inner_len(k, mode, kit):
    """Post long enough to rest on the socket floor at the lowest setting."""
    floor = sleeve_bottom_z(k) - (0.3 if mode == "print" else 0.0)
    return underside_z(k, 0) - _gap(k, mode, kit) - floor - (0.3 if mode == "print" else 1.0 * k)


def _teardrop_x(x0, x1, y, z, d, roof):
    """Hole along X; roof = '+z' or '+y' gives it a 45-degree peak so it prints without support."""
    r = d / 2
    cyl = cq.Solid.makeCylinder(r, x1 - x0, cq.Vector(x0, y, z), cq.Vector(1, 0, 0))
    if roof is None:
        return cyl
    if roof == "+z":
        pts = [(y - r * 0.7071, z + r * 0.7071), (y, z + r * 1.4142), (y + r * 0.7071, z + r * 0.7071), (y, z)]
    else:
        pts = [(y + r * 0.7071, z - r * 0.7071), (y + r * 1.4142, z), (y + r * 0.7071, z + r * 0.7071), (y, z)]
    tri = cq.Workplane("YZ", origin=(x0, 0, 0)).polyline(pts).close().extrude(x1 - x0).val()
    return cyl.fuse(tri).clean()


def build_sleeve(k, mode, kit=None):
    sx, sy = P.SLEEVE
    ix, iy = P.INNER
    c = kit["slide"] if mode == "print" else 1.0 * k
    z0, z1 = sleeve_bottom_z(k), P.SLEEVE_TOP * k
    outer = rrect_prism(P.POST_X * k, 0, sx * k, sy * k, P.POST_R * k, z0, z1)
    top = [e for e in outer.Edges() if abs(e.Center().z - z1) < 1e-6]
    outer = outer.fillet(3 * k if mode == "real" else 0.6, top)
    bore = rrect_prism(P.POST_X * k, 0, ix * k + 2 * c, iy * k + 2 * c, P.POST_R * k * 0.6, z0 - 1, z1 + 1)
    s = outer.cut(bore)
    # soften the bore's top edge
    rim = [e for e in s.Edges() if abs(e.Center().z - z1) < 1e-6 and abs(e.Center().x - P.POST_X * k) < ix * k / 2 + c + 0.01]
    try:
        cand = s.fillet(1.5 * k if mode == "real" else 0.3, rim)
        if cand.isValid():
            s = cand
    except Exception:
        pass
    # height pin runs front to back (X); knob sits on the far side, away from knees
    d = kit["pin_grip"] if mode == "print" else 10 * k
    x0, x1 = (P.POST_X - sx / 2) * k - 1, (P.POST_X + sx / 2) * k + 1
    hole = _teardrop_x(x0, x1, 0, P.SLEEVE_PIN_Z * k, d, "+z" if mode == "print" else None)
    return s.cut(hole).clean()


def build_head(k, mode, hi, kit=None):
    ix, iy = P.INNER
    zb = underside_z(k, hi)
    gap = _gap(k, mode, kit)
    th = P.TENON_H * k
    x0 = (P.POST_X + P.TENON_X[0]) * k
    x1 = (P.POST_X + P.TENON_X[1]) * k
    wt = P.TENON_W_TOP * k
    wb = wt - 2 * (th + gap)                       # 45-degree flanks down to the post top
    tenon = (cq.Workplane("YZ", origin=(x0, 0, 0))
             .polyline([(-wb / 2, zb - gap), (wb / 2, zb - gap), (wt / 2, zb + th), (-wt / 2, zb + th)]).close()
             .extrude(x1 - x0).val())
    ends = [e for e in tenon.Edges() if abs(e.Center().x - x0) < 1e-6 or abs(e.Center().x - x1) < 1e-6]
    for rr in ((3.0 * k, 2.0 * k) if mode == "real" else (0.4, 0.3)):
        try:
            cand = tenon.fillet(rr, ends)
            if cand.isValid():
                tenon = cand
                break
        except Exception:
            pass
    # inner post: from just under the desk down far enough to bottom out at the lowest setting
    zbot = zb - gap - inner_len(k, mode, kit)
    post = rrect_prism(P.POST_X * k, 0, ix * k, iy * k, P.POST_R * k * 0.6, zbot, zb - gap + 0.05 * k)
    bot = [e for e in post.Edges() if abs(e.Center().z - zbot) < 1e-6]
    post = post.fillet(2 * k if mode == "real" else 0.4, bot)
    head = tenon.fuse(post)
    # guide boss for the reach index pin, merged into the back of the post
    xd = (P.POST_X + P.DETENT_OFF) * k
    br, bh = P.INDEX_BOSS[0] * k, P.INDEX_BOSS[1] * k
    boss = cq.Solid.makeCylinder(br, bh + 0.1 * k, cq.Vector(xd, 0, zb - gap - bh), cq.Vector(0, 0, 1))
    try:
        boss = boss.fillet(3 * k if mode == "real" else 0.4,
                           [e for e in boss.Edges() if abs(e.Center().z - (zb - gap - bh)) < 1e-6])
    except Exception:
        pass
    head = head.fuse(boss).clean()
    # reach pin hole (vertical); snug so the pin can't fall out; in the print it is horizontal
    d = kit["pin_guide"] if mode == "print" else 10 * k
    zlo, zhi = zb - gap - bh - 1, zb + th + 1
    circ = cq.Solid.makeCylinder(d / 2, zhi - zlo, cq.Vector(xd, 0, zlo), cq.Vector(0, 0, 1))
    if mode == "print":
        r = d / 2
        roof = (cq.Workplane("XY", origin=(0, 0, zlo))
                .polyline([(xd - r * 0.7071, r * 0.7071), (xd, r * 1.4142), (xd + r * 0.7071, r * 0.7071), (xd, 0)])
                .close().extrude(zhi - zlo).val())
        circ = circ.fuse(roof)
    head = head.cut(circ)
    # height holes, front to back through the post
    d = kit["pin_hole"] if mode == "print" else 10 * k
    for dep in hole_depths(k):
        z = zb - dep
        head = head.cut(_teardrop_x((P.POST_X - ix / 2) * k - 1, (P.POST_X + ix / 2) * k + 1, 0, z, d,
                                    "+y" if mode == "print" else None))
    return head.clean()


def _track_profile(k, mode, kit, zb, shrink=0.0):
    """Track cross-section (a true offset of the tenon) as (y, z) points."""
    ch = (kit["slide"] if mode == "print" else 0.5 * k) - shrink
    ct = (kit["track_top"] if mode == "print" else 0.5 * k) - shrink
    th = P.TENON_H * k
    mouth = P.TENON_W_TOP * k - 2 * th + 2 * ch
    depth = th + ct
    top = mouth + 2 * depth
    return [(-mouth / 2, zb), (mouth / 2, zb), (top / 2, zb + depth), (-top / 2, zb + depth)], depth


def build_top(k, mode, hi, gi, kit=None):
    zt = P.DESK_HEIGHTS[hi] * k
    t = P.TOP_T * k
    xn = P.desk_near_x(gi) * k
    D, W, Wn = P.TOP_D * k, P.TOP_W * k, P.TOP_W_NEAR * k
    # tapered top: narrower at the student, wider at the far edge
    sk = (cq.Sketch().polygon([(xn, -Wn / 2), (xn + D, -W / 2), (xn + D, W / 2), (xn, Wn / 2), (xn, -Wn / 2)])
          .vertices(">X").fillet(P.TOP_CORNER_R * k)
          .reset().vertices("<X").fillet(P.TOP_CORNER_R_NEAR * k))
    top = cq.Workplane("XY", origin=(0, 0, zt - t)).placeSketch(sk).extrude(t).val()
    # gentle belly cut in the near edge (room for bigger bodies), with rounded ends
    bd, bw = P.BELLY[0] * k, P.BELLY[1] * k
    R = ((bw / 2) ** 2 + bd ** 2) / (2 * bd)
    top = top.cut(cq.Solid.makeCylinder(R, t + 2, cq.Vector(xn + bd - R, 0, zt - t - 1), cq.Vector(0, 0, 1)))
    ends = [e for e in top.Edges() if abs(abs(e.Center().y) - bw / 2) < 2 * k + 0.2 and abs(e.Center().x - xn) < 3 * k + 0.2
            and abs(e.Center().z - (zt - t / 2)) < 1e-3]
    try:
        cand = top.fillet(40 * k, ends)
        if cand.isValid():
            top = cand
    except Exception:
        pass
    er = P.TOP_EDGE_R * k
    top_edges = [e for e in top.Edges() if abs(e.Center().z - zt) < 1e-6]
    top = top.fillet(er, top_edges)
    bot_edges = [e for e in top.Edges() if abs(e.Center().z - (zt - t)) < 1e-6]
    top = top.fillet(er if mode == "real" else 0.8, bot_edges)

    # pencil groove near the far edge, with ramped wipe-out ends and a rounded rim
    xc = xn + D - P.COVE_FROM_FAR * k
    half_w, dep = P.COVE_W * k / 2, P.COVE_D * k
    rc = (half_w ** 2 + dep ** 2) / (2 * dep)
    zc = zt + rc - dep
    hl = P.COVE_LEN * k / 2
    ramp = P.COVE_RAMP * k
    pts = [cq.Vector(xc, y, zc + dz) for y, dz in [
        (-hl - 4 * k, dep * 1.25), (-hl + ramp * 0.35, dep * 0.45), (-hl + ramp, 0.0),
        (0.0, 0.0), (hl - ramp, 0.0), (hl - ramp * 0.35, dep * 0.45), (hl + 4 * k, dep * 1.25)]]
    path = cq.Wire.assembleEdges([cq.Edge.makeSpline(pts)])
    tan = (pts[1] - pts[0]).normalized()
    cutter = cq.Solid.sweep(cq.Wire.makeCircle(rc, pts[0], tan), [], path, makeSolid=True)
    top = top.cut(cutter)
    rim = [e for e in top.Edges()
           if abs(e.Center().z - zt) < 0.05 * k + 1e-6 and abs(e.Center().x - xc) < half_w + 2 * k]
    for rr in ((3.0 * k, 2.0 * k) if mode == "real" else (0.45, 0.3)):
        try:
            cand = top.fillet(rr, rim)
            if cand.isValid():
                top = cand
                break
        except Exception:
            pass

    # dovetail track underneath, open at the far edge (closed later by the plug)
    zb = zt - t
    prof, depth = _track_profile(k, mode, kit, zb - 0.01)
    tx0 = xn + P.TRACK_START * k
    track = cq.Workplane("YZ", origin=(tx0, 0, 0)).polyline(prof).close().extrude(D + 10 * k).val()
    top = top.cut(track)
    # one index hole per reach setting for the reach pin (blind, never through the writing surface)
    d = kit["pin_hole"] if mode == "print" else 10 * k
    dep_h = depth + (1.2 if mode == "print" else 8 * k)
    for g in range(len(P.DESK_GAPS)):
        xd = (P.POST_X + P.DETENT_OFF) * k - (P.desk_near_x(g) * k - xn)
        top = top.cut(cq.Solid.makeCylinder(d / 2, dep_h, cq.Vector(xd, 0, zb - 0.01), cq.Vector(0, 0, 1)))
    return top.clean()


def build_plug(k, mode, hi, gi, kit=None):
    """End plug pressed into the far end of the track after assembly (stop + finger guard)."""
    zb = underside_z(k, hi)
    shrink = kit["snug"] if mode == "print" else 0.2 * k      # press fit in the track
    prof, depth = _track_profile(k, mode, kit, zb + 0.05 * k, shrink=shrink)
    far = (P.desk_near_x(gi) + P.TOP_D) * k
    x0 = far - P.PLUG_LEN * k
    x1 = far - 0.4 * k
    plug = cq.Workplane("YZ", origin=(x0, 0, 0)).polyline(prof).close().extrude(x1 - x0).val()
    return plug.clean()
