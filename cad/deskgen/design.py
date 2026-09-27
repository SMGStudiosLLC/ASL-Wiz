"""
Builds every part of the DELTA chair-desk in one of two modes:

  Design("real")   full-size product geometry (mm), for STEP / renders / AR
  Design("print")  1:6 handheld model, with print-friendly walls, grip ribs,
                   tabs/sockets, a dovetail slide and pin holes

Parts are returned already placed in the assembled position (world coords).
"""
import cadquery as cq

from . import params as P
from .shell import ShellGeom, build_shell_body, build_seat_fill
from .frames import FrameOutline, build_frame
from .base import build_base
from .desk import build_sleeve, build_head, build_top, build_plug
from .geom import box, rrect_prism

COLORS_REAL = {
    "shell": (0.11, 0.11, 0.12), "frame_L": (0.11, 0.11, 0.12), "frame_R": (0.11, 0.11, 0.12),
    "seat_beam": (0.11, 0.11, 0.12),
    "base": (0.62, 0.63, 0.65), "sleeve": (0.62, 0.63, 0.65), "head": (0.62, 0.63, 0.65),
    "top": (0.95, 0.95, 0.96), "plug": (0.95, 0.95, 0.96),
}
COLORS_PRINT = {
    "shell": "black", "frame_L": "black", "frame_R": "black",
    "base": "white", "sleeve": "white", "head": "white", "top": "white", "plug": "white",
}


class Design:
    def __init__(self, mode="real", ribs=None):
        self.mode = mode
        self.k = 1.0 if mode == "real" else P.KIT_SCALE
        k = self.k
        self.kit = dict(P.KIT)
        self.ribs = (mode == "print") if ribs is None else ribs
        self.g = ShellGeom(k, mode)
        s = self.g.s_at_x(P.FRAME_APEX_X * k)
        yc = (P.FRAME_Y_OUT - P.FRAME_T / 2) * k
        under = self.g.surface_point(s, yc, side=-1)[2]
        self.shell_under_at_apex = under
        self.apex_top_z = under - P.PAD_H * k
        self.outline = FrameOutline(k, self.apex_top_z)
        self._cache = {}

    # --------------------------------------------------------------- shell
    def shell_components(self, skin=+1):
        """Body, pads, sockets and ribs as separate B-rep solids (combined later).
        skin=+1: pads reach up through the shell wall (for mesh unions);
        skin=-1: pads stop at the shell's underside (touching solids for the STEP)."""
        key = ("shell_comp", skin)
        if key in self._cache:
            return self._cache[key]
        k, g = self.k, self.g
        body = None                      # B-rep body built lazily in shell() (slow loft)
        xa = self.outline.apex_centre[0]
        s_front, s_back = g.s_at_x(xa + 75 * k), g.s_at_x(xa - 75 * k)
        fill = build_seat_fill(g, s_front, s_back, drop=120 * k, skin=skin, n=9 if skin > 0 else 25)
        yin, yout = P.FRAME_Y_IN * k, P.FRAME_Y_OUT * k
        prism = self.frame_prism()
        add, sub = [body], []
        pad_prof = self.pad_solid()
        for side in (+1, -1):
            pb, pr = pad_prof, prism
            if side < 0:
                pb, pr = pb.mirror("XZ"), prism.mirror("XZ")
            add.append(pb.intersect(fill).cut(pr).clean())
        if self.mode == "print":
            kp = self.kit
            c = kp["snug"]
            for side in (+1, -1):
                sock = box(xa - kp["tab_len"] / 2 - c, xa + kp["tab_len"] / 2 + c,
                           yin - c, yin + kp["tab_t"] + c,
                           self.apex_top_z - 3, self.apex_top_z + kp["tab_h"] + 0.3)
                sub.append(sock if side > 0 else sock.mirror("XZ"))
        self._cache[key] = (add, sub)
        return add, sub

    def shell_mesh(self, tol=None, ang=0.15):
        """Shell as a watertight mesh: structured body mesh + pads/ribs/sockets via manifold3d."""
        from .mesh import to_trimesh, to_manifold, from_manifold
        import manifold3d as mf
        from .shell import build_shell_body_mesh
        tol = tol if tol is not None else (0.25 if self.mode == "real" else 0.03)
        add, sub = self.shell_components()
        body = build_shell_body_mesh(self.g)
        mans = [to_manifold(body)] + [to_manifold(to_trimesh(s, tol, ang)) for s in add[1:]]
        if self.mode == "real":
            from .shell import seat_rib_meshes
            for rm, _ in seat_rib_meshes(self.g):
                mans.append(to_manifold(rm))
        if self.ribs:
            from .shell import rib_paths, rib_mesh
            if self.mode == "print":
                pitch, r, margin = self.kit["rib_pitch"], self.kit["rib_h"], 1.6
            else:
                pitch, r, margin = 5.0, 1.1, 10.0
            g = self.g
            for pts, nrm in rib_paths(g, g.sc[9] + 2 * pitch, g.sc[14] - 3 * pitch, pitch, margin):
                mans.append(to_manifold(rib_mesh(pts, nrm, r, sink=0.05 * r)))
        res = mf.Manifold.batch_boolean(mans, mf.OpType.Add)
        cut = [to_manifold(to_trimesh(s, tol, ang)) for s in sub]
        if self.mode == "real":
            cut.append(to_manifold(to_trimesh(self.seat_beam(clearance=1.0), tol, ang)))
        if cut:
            res = res - mf.Manifold.batch_boolean(cut, mf.OpType.Add)
        return from_manifold(res)

    def shell(self):
        """Exact B-rep shell for the STEP export: the lofted shell plus the two bearing pads as
        touching solids in one compound (OpenCASCADE booleans against the loft are unreliable).
        Leaves out the grip ribs and the under-seat ribs, which only exist in the meshes."""
        add, sub = self.shell_components(skin=-1)
        if self.mode == "real":
            sub = sub + [self.seat_beam(clearance=1.0)]
        sub = sub + self._skirt_keepout()
        pads = [p.cut(*sub).clean() for p in add[1:]]
        return cq.Compound.makeCompound([build_shell_body(self.g)] + pads)

    def _skirt_keepout(self, gap=0.6):
        """Solids covering the curled side edges of the seat (inside face outward, down to just
        below the edge's lowest point), used to keep the STEP's pads out of the shell wall."""
        import numpy as np
        g, k = self.g, self.k
        xa = self.outline.apex_centre[0]
        xs = np.linspace(xa - 140 * k, xa + 140 * k, 29)
        inner, lows = [], []
        for x in xs:
            st = g.s_at_x(x)
            ring = g.ring(st)
            side = ring[ring[:, 0] > g.fw(st) - g.fr(st)]           # the curled part of the edge
            pts = np.array([[p.x, p.y, p.z] for p in g.to3d(st, side)])
            lows.append(pts[:, 2].min() - gap * k)
            inner.append(g.fw(st) - g.thickness(st) / 2 - 2.0 * k)    # inside face of the edge's vertical part
        y0 = float(min(inner))
        out = []
        for sgn in (+1, -1):
            prof = [(float(x), float(z)) for x, z in zip(xs, lows)] + [(float(xs[-1]), 2000.0 * k), (float(xs[0]), 2000.0 * k)]
            wp = cq.Workplane("XZ", origin=(0, 0, 0)).polyline(prof).close()
            solid = wp.extrude(-(400 * k)).val().translate(cq.Vector(0, y0, 0))   # XZ extrudes toward -Y
            out.append(solid if sgn > 0 else solid.mirror("XZ"))
        return out

    def seat_beam(self, clearance=0.0):
        """Hidden aluminium cross beam under the seat, bolted to both frame apexes (real product).
        Carries the seat across its width and ties the two frames together."""
        k, g = self.k, self.g
        xa = self.outline.apex_centre[0]
        s = g.s_at_x(xa)
        ztop = g.surface_point(s, 0.0, side=-1)[2] - 0.5 * k
        bx, bz = P.SEAT_BEAM
        c = clearance * k
        y = P.FRAME_Y_IN * k + c
        beam = box(xa - bx * k / 2 - c, xa + bx * k / 2 + c, -y, y, ztop - bz * k - c, ztop + c)
        long_edges = [e for e in beam.Edges() if abs(e.Center().y) < 1e-6]
        return beam.fillet(6 * k + c, long_edges)

    def pad_solid(self, r_f=P.PAD_BLEND_R):
        """Bearing pad: a moulded fillet flowing from the frame's round apex up into the seat.

        Side profile = region above the apex arc and below the seat, bounded front and
        back by concave fillet arcs tangent to both the apex arc and the seat underside.
        """
        import math
        import numpy as np
        k, g = self.k, self.g
        C = np.array(self.outline.apex_centre)
        R = self.outline.apex_r
        rf = r_f * k
        yc = (P.FRAME_Y_OUT - P.FRAME_T / 2) * k
        pts = {}
        for sgn in (-1, +1):
            # iterate: seat underside height where the fillet meets the seat
            zl = self.shell_under_at_apex
            for _ in range(5):
                zc = zl - rf
                dz = zc - C[1]
                dx = math.sqrt((R + rf) ** 2 - dz ** 2)
                xf = C[0] + sgn * dx
                zl = g.surface_point(g.s_at_x(xf), yc, side=-1)[2]
            zc = zl - rf
            dz = zc - C[1]
            dx = math.sqrt((R + rf) ** 2 - dz ** 2)
            xf = C[0] + sgn * dx
            F = np.array([xf, zc])
            d = (C - F) / np.linalg.norm(C - F)
            t_arc = F + d * rf                      # tangent point on the apex arc
            t_seat = np.array([xf, zl])             # tangent point under the seat
            up = np.array([0.0, 1.0])
            mdir = (d + up) / np.linalg.norm(d + up)
            mid = F + mdir * rf
            pts[sgn] = (t_seat, mid, t_arc)
        (sL, mL, aL), (sR, mR, aR) = pts[-1], pts[+1]
        ztop = max(sL[1], sR[1]) + 60 * k
        # outer face flush with the skirt's outermost point, so it sits on the bed in the print pose
        flush = self.g.ft(self.g.sc[5]) / 2
        y0 = P.FRAME_Y_OUT * k + flush
        widen = 60 * k
        wp = (cq.Workplane("XZ", origin=(0, y0, 0))
              .moveTo(sL[0], ztop).lineTo(sL[0], sL[1])
              .threePointArc((mL[0], mL[1]), (aL[0], aL[1]))
              .lineTo(aR[0], aR[1])
              .threePointArc((mR[0], mR[1]), (sR[0], sR[1]))
              .lineTo(sR[0], ztop).close())
        pad = wp.extrude(P.FRAME_T * k + flush + widen).val()
        # 45-degree gusset on the inner face: keeps  Y >= y_in - (Z - z_ref)
        # (self-supporting when the shell prints on its side, and reads as a moulded rib)
        y_in = P.FRAME_Y_IN * k
        z_ref = self.apex_top_z - 8 * k
        zlo, zhi = z_ref - 300 * k, z_ref + 300 * k
        cut = (cq.Workplane("YZ", origin=(sL[0] - 5 * k, 0, 0))
               .polyline([(y_in + z_ref - zlo, zlo), (y_in + z_ref - zhi, zhi), (-2000 * k, zhi), (-2000 * k, zlo)])
               .close().extrude(sR[0] - sL[0] + 10 * k).val())
        return pad.cut(cut).clean()

    def frame_prism(self):
        """Solid region of the frame outline (no window, no rounding), for trimming the pads."""
        from .geom import segs_to_wire
        k = self.k
        y0 = P.FRAME_Y_OUT * k + 1

        def to3d(p):
            return cq.Vector(float(p[0]), y0, float(p[1]))

        ow = segs_to_wire(self.outline.segs, to3d)
        if self.mode == "real":
            # 0.3 mm assembly clearance so faceted meshes of pad and apex never overlap
            ow = ow.offset2D(0.3, "arc")[0]
        f = cq.Face.makeFromWires(ow, [])
        return cq.Solid.extrudeLinear(f, cq.Vector(0, -(P.FRAME_T * k + 2), 0))

    # --------------------------------------------------------- other parts
    def frame(self, side):
        return build_frame(self.outline, side, self.mode, self.kit)

    def base(self):
        return build_base(self.k, self.mode, self.kit)

    def sleeve(self):
        return build_sleeve(self.k, self.mode, self.kit)

    def head(self, hi=P.DEFAULT_HEIGHT_INDEX):
        return build_head(self.k, self.mode, hi, self.kit)

    def top(self, hi=P.DEFAULT_HEIGHT_INDEX, gi=P.DEFAULT_GAP_INDEX):
        return build_top(self.k, self.mode, hi, gi, self.kit)

    def plug(self, hi=P.DEFAULT_HEIGHT_INDEX, gi=P.DEFAULT_GAP_INDEX):
        return build_plug(self.k, self.mode, hi, gi, self.kit)

    def parts(self, hi=P.DEFAULT_HEIGHT_INDEX, gi=P.DEFAULT_GAP_INDEX):
        return {
            "shell": None,          # use shell_mesh() / shell()
            "frame_L": self.frame(+1),
            "frame_R": self.frame(-1),
            "base": self.base(),
            "sleeve": self.sleeve(),
            "head": self.head(hi),
            "top": self.top(hi, gi),
            "plug": self.plug(hi, gi),
        }
