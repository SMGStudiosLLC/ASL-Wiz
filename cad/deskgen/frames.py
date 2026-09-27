"""
Side frames: two rounded triangles, one under each side of the seat.

Each frame is a closed ring (a window through the middle), with the rear-bottom
corner cut off by a large round so the frame reads as a heel rather than a
spike.  The apex sits under the sit bones and nests into a bearing pad moulded
under the seat shell.
"""
import math
import numpy as np
import cadquery as cq

from . import params as P
from .geom import filleted_polygon, offset_polygon, segs_to_wire, box


class FrameOutline:
    def __init__(self, k, apex_top_z):
        self.k = k
        F = np.array(P.FRAME_FRONT) * k
        R = np.array(P.FRAME_REAR) * k
        xa = P.FRAME_APEX_X * k
        radii = [P.FRAME_R_REAR * k, P.FRAME_R_FRONT * k, P.FRAME_R_APEX * k]
        za = apex_top_z + 60 * k
        for _ in range(40):
            pts = [R, F, np.array([xa, za])]
            segs, corners = filleted_polygon(pts, radii)
            top = corners[2]["centre"][1] + corners[2]["r"]
            za += apex_top_z - top
            if abs(apex_top_z - top) < 1e-6:
                break
        self.pts, self.radii, self.segs, self.corners = pts, radii, segs, corners
        self.apex_centre = corners[2]["centre"]
        self.apex_r = corners[2]["r"]
        self.apex_top_z = apex_top_z
        inner = offset_polygon(pts, [P.FRAME_RUNNER_W * k, P.FRAME_LEG_W * k, P.FRAME_LEG_W * k])
        wr = P.FRAME_WIN_R
        self.inner_pts = inner
        self.inner_segs, self.inner_corners = filleted_polygon(inner, [wr[2] * k, wr[0] * k, wr[1] * k])

    def floor_contact(self):
        """X range where the frame bottom sits on the floor."""
        return self.corners[0]["t_out"][0], self.corners[1]["t_in"][0]


def build_frame(outline: FrameOutline, side, mode, kit=None):
    """side = +1 (student's left, +Y) or -1 (right). Returns a solid in world position."""
    k = outline.k
    y_out = P.FRAME_Y_OUT * k
    t = P.FRAME_T * k

    def to3d(p):
        return cq.Vector(float(p[0]), y_out, float(p[1]))

    ow = segs_to_wire(outline.segs, to3d)
    iw = segs_to_wire(outline.inner_segs, to3d)
    face = cq.Face.makeFromWires(ow, [iw])
    solid = cq.Solid.extrudeLinear(face, cq.Vector(0, -t, 0))
    planar = [f for f in solid.Faces() if f.geomType() == "PLANE" and abs(f.normalAt().y) > 0.99]
    edges = [e for f in planar for e in f.Edges()]
    r = P.FRAME_EDGE_R * k
    solid = solid.fillet(r, edges)

    if mode == "print":
        kp = kit
        cx = outline.apex_centre[0]
        y_in = y_out - t
        # tab that plugs up into the seat's bearing pad; flush with the inner face,
        # which is the face on the print bed, so the tab never overhangs
        tab = box(cx - kp["tab_len"] / 2, cx + kp["tab_len"] / 2,
                  y_in, y_in + kp["tab_t"],
                  outline.apex_top_z - 1.2, outline.apex_top_z + kp["tab_h"])
        solid = solid.fuse(tab).clean()
        # socket on the inner face for the base cross bar
        xc = (P.CROSSBAR_X[0] + P.CROSSBAR_X[1]) / 2 * k
        c = kp["snug"]
        pocket = box(xc - kp["xbar_tab_len"] / 2 - c, xc + kp["xbar_tab_len"] / 2 + c,
                     y_in - 0.01, y_in + kp["xbar_tab_depth"] + 0.25,
                     -1.0, kp["xbar_tab_z0"] + kp["xbar_tab_h"] + c)      # open at the bottom: frame drops onto the tab
        solid = solid.cut(pocket).clean()

    if side < 0:
        solid = solid.mirror("XZ")
    return solid
