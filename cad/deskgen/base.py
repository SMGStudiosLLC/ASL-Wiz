"""
Floor base: one low 'I' shape on the floor.

  cross bar   joins the two side frames' front feet (under the seat front); its ends
              stay square where they bolt against the frames
  spine       runs along the centreline to the desk; widens into a footrest pad where
              shorter students' feet land
  T-foot      under the desk's far end; wide for side stability

Nothing on the floor sticks out past the desktop's outline, and the only bar is on the
centreline, so both sides of the seat are open for turning.
"""
import cadquery as cq

from . import params as P
from .geom import box, rrect_prism


def sleeve_bottom_z(k):
    return 17.0 * k


def build_base(k, mode, kit=None):
    h = P.BASE_H * k
    x0, x1 = P.CROSSBAR_X
    xc = (x0 + x1) / 2
    yin = P.FRAME_Y_IN
    tx0, tx1 = P.TFOOT_X
    fx0, fx1 = P.FOOTREST_X
    r = P.BASE_PLAN_R * k
    sk = (cq.Sketch()
          .push([((x0 + x1) / 2 * k, 0)]).rect((x1 - x0) * k, 2 * yin * k)
          .push([((xc + tx0 + 40) / 2 * k, 0)]).rect((tx0 + 40 - xc) * k, P.SPINE_W * k)
          .push([((fx0 + fx1) / 2 * k, 0)]).rect((fx1 - fx0) * k, 2 * P.FOOTREST_HALF_W * k)
          .push([((tx0 + tx1) / 2 * k, 0)]).rect((tx1 - tx0) * k, 2 * P.TFOOT_HALF_W * k)
          .clean()
          .reset().vertices().fillet(r)
          # square the cross-bar ends again where they butt against the frames
          .push([(xc * k, (yin - 30) * k), (xc * k, -(yin - 30) * k)]).rect((x1 - x0) * k, 60 * k, mode="a")
          .clean())
    base = cq.Workplane("XY").placeSketch(sk).extrude(h).val()
    top_edges = [e for e in base.Edges()
                 if abs(e.Center().z - h) < 1e-6 and abs(abs(e.Center().y) - yin * k) > 0.5 * k]
    base = base.fillet(12 * k, top_edges)
    bot_edges = [e for e in base.Edges()
                 if abs(e.Center().z) < 1e-6 and abs(abs(e.Center().y) - yin * k) > 0.5 * k]
    base = base.fillet((0.5 if mode == "print" else 3 * k), bot_edges)

    # socket boss for the desk post, blended into the T-foot
    bx, by, bz = P.POST_BOSS
    boss = rrect_prism(P.POST_X * k, 0, bx * k, by * k, 24 * k, 0, bz * k)
    top = [e for e in boss.Edges() if abs(e.Center().z - bz * k) < 1e-6]
    boss = boss.fillet(14 * k, top)
    base = base.fuse(boss).clean()

    sx, sy = P.SLEEVE
    c = kit["snug"] if mode == "print" else 0.5 * k
    pocket = rrect_prism(P.POST_X * k, 0, sx * k + 2 * c, sy * k + 2 * c, P.POST_R * k + c,
                         sleeve_bottom_z(k) - (0.3 if mode == "print" else 0), bz * k + 1)
    base = base.cut(pocket).clean()
    rim = [e for e in base.Edges() if abs(e.Center().z - bz * k) < 1e-6
           and abs(e.Center().x - P.POST_X * k) < (sx / 2 + 2) * k + c and abs(e.Center().y) < (sy / 2 + 2) * k + c]
    try:
        cand = base.fillet(2.0 * k if mode == "real" else 0.3, rim)
        if cand.isValid():
            base = cand
    except Exception:
        pass

    if mode == "print":
        kp = kit
        for s in (+1, -1):
            yface = s * yin * k
            y0, y1 = sorted([yface, yface + s * kp["xbar_tab_depth"]])
            if s > 0:
                y0 -= 1.0
            else:
                y1 += 1.0
            tab = box(xc * k - kp["xbar_tab_len"] / 2, xc * k + kp["xbar_tab_len"] / 2, y0, y1, 0.0, kp["xbar_tab_h"])
            # lead-in chamfer on the tab's top outer edge
            try:
                sel = [e for e in tab.Edges() if abs(e.Center().z - kp["xbar_tab_h"]) < 1e-6
                       and abs(abs(e.Center().y) - abs(y1 if s > 0 else y0)) < 1e-6]
                tab = tab.chamfer(kp["chamfer"], None, sel)
            except Exception:
                pass
            base = base.fuse(tab).clean()
    return base
