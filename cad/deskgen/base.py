"""
Floor base: one low 'I' shape on the floor.

  cross bar   joins the two side frames' front feet (under the seat front)
  spine       runs along the centreline to the desk
  T-foot      under the desk's far end; wide for side stability, and a footrest

Nothing on the floor sticks out past the desktop's footprint, and the only bar
is on the centreline, so both sides of the seat are open for turning.
"""
import cadquery as cq

from . import params as P
from .geom import box, rrect_prism


def build_base(k, mode, kit=None):
    h = P.BASE_H * k
    x0, x1 = P.CROSSBAR_X
    xc = (x0 + x1) / 2
    yin = P.FRAME_Y_IN
    tx0, tx1 = P.TFOOT_X
    sk = (cq.Sketch()
          .push([((x0 + x1) / 2 * k, 0)]).rect((x1 - x0) * k, 2 * yin * k)
          .push([((xc + tx0 + 40) / 2 * k, 0)]).rect((tx0 + 40 - xc) * k, P.SPINE_W * k)
          .push([((tx0 + tx1) / 2 * k, 0)]).rect((tx1 - tx0) * k, 2 * P.TFOOT_HALF_W * k)
          .clean()
          .reset().vertices().fillet(24 * k))
    base = cq.Workplane("XY").placeSketch(sk).extrude(h).val()
    top_edges = [e for e in base.Edges()
                 if abs(e.Center().z - h) < 1e-6]
    base = base.fillet(12 * k, top_edges)
    bot_edges = [e for e in base.Edges() if abs(e.Center().z) < 1e-6]
    base = base.fillet((0.5 if mode == "print" else 3 * k), bot_edges)

    # socket boss for the desk post
    bx, by, bz = P.POST_BOSS
    boss = rrect_prism(P.POST_X * k, 0, bx * k, by * k, 22 * k, 0, bz * k)
    top = [e for e in boss.Edges() if abs(e.Center().z - bz * k) < 1e-6]
    boss = boss.fillet(10 * k, top)
    base = base.fuse(boss).clean()

    sx, sy = P.SLEEVE
    c = kit["snug"] if mode == "print" else 0.5 * k
    depth = P.POST_BOSS[2] * k - sleeve_bottom_z(k)
    pocket = rrect_prism(P.POST_X * k, 0, sx * k + 2 * c, sy * k + 2 * c, P.POST_R * k + c,
                         sleeve_bottom_z(k) - (0.3 if mode == "print" else 0), bz * k + 1)
    base = base.cut(pocket).clean()

    if mode == "print":
        kp = kit
        for s in (+1, -1):
            yface = s * yin * k
            y0, y1 = sorted([yface, yface + s * kp["xbar_tab_depth"]])
            # overlap into the bar so the union is solid
            if s > 0:
                y0 -= 1.0
            else:
                y1 += 1.0
            tab = box(xc * k - kp["xbar_tab_len"] / 2, xc * k + kp["xbar_tab_len"] / 2,
                      y0, y1, kp["xbar_tab_z0"], kp["xbar_tab_z0"] + kp["xbar_tab_h"])
            base = base.fuse(tab).clean()
    return base


def sleeve_bottom_z(k):
    return 17.0 * k
