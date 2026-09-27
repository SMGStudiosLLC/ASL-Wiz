"""
One-piece seat shell: seat pan, junction, flexing lower back, hourglass upper back.

The shell is lofted through ~50 cross-sections placed perpendicular to a smooth
side-profile centreline.  Every cross-section is a thin curved strip with
rolled edges and a rounded end cap, so no edge on the shell is sharp.  The two
ends (waterfall tip and top lip) taper to a round nose.
"""
import math
import numpy as np
import cadquery as cq
from scipy.interpolate import splprep, splev, PchipInterpolator
from OCP.BRepOffsetAPI import BRepOffsetAPI_ThruSections

from . import params as P


def _pchip(keys, vals):
    f = PchipInterpolator(keys, vals)
    lo, hi = keys[0], keys[-1]
    return lambda s: float(f(min(max(s, lo), hi)))


def loft(wires):
    b = BRepOffsetAPI_ThruSections(True, False, 1e-6)
    b.CheckCompatibility(False)
    for w in wires:
        b.AddWire(w.wrapped)
    b.Build()
    return cq.Solid(b.Shape())


class ShellGeom:
    """Centreline, section functions and point queries for the shell."""

    REAL_T = [4.5, 5, 5, 5, 5.5, 7.0, 9.0, 9.5, 9.0, 6.5, 6.0, 6.0, 5.5, 5, 5, 5, 4.5]
    PRINT_T = [1.5, 1.7, 1.7, 1.7, 1.7, 1.7, 1.7, 1.65, 1.45, 1.25, 1.25, 1.25, 1.35, 1.45, 1.45, 1.45, 1.4]

    def __init__(self, k=1.0, mode="real"):
        self.k, self.mode = k, mode
        ctrl = np.array(P.SHELL_PATH) * k
        self.tck, u = splprep([ctrl[:, 0], ctrl[:, 1]], s=0, k=3)
        self.uu = np.linspace(0, 1, 8000)
        xs, zs = splev(self.uu, self.tck)
        self.S = np.concatenate([[0], np.cumsum(np.hypot(np.diff(xs), np.diff(zs)))])
        self.L = float(self.S[-1])
        self.sc = np.interp(u, self.uu, self.S)
        sc = list(self.sc)
        self.fw = _pchip(sc, np.array(P.SHELL_HALF_W) * k)
        dish = np.array(P.SHELL_DISH, float)
        if mode == "print":
            for i, f in getattr(P, "SHELL_DISH_PRINT_FACTOR", {}).items():
                dish[i] *= f
        self.fd = _pchip(sc, dish * k)
        self.fr = _pchip(sc, np.array(P.SHELL_ROLL) * k)
        if mode == "real":
            # thicker, gas-assist-cored junction carries the backrest moment into the seat;
            # keeps the outside smooth (no visible ribs behind the back)
            self.ft = _pchip(sc, np.array(self.REAL_T) * k)
        else:
            self.ft = _pchip(sc, self.PRINT_T)
        # how far the edge roll turns: to vertical for the product, 45 deg for the print model
        # (the shell prints on its side, and a roll that ends horizontal would overhang)
        self.roll_end = math.pi / 2 if mode == "real" else math.radians(45)
        self.t_end0 = self.ft(0.0)
        self.t_end1 = self.ft(self.L)

    # ---- centreline ------------------------------------------------------
    def frame_at(self, s):
        uq = np.interp(s, self.S, self.uu)
        x, z = splev(uq, self.tck)
        dx, dz = splev(uq, self.tck, der=1)
        n = math.hypot(dx, dz)
        T = np.array([dx / n, dz / n])
        N = np.array([T[1], -T[0]])          # toward the sitter
        return np.array([float(x), float(z)]), T, N

    def s_at_x(self, x, lo_idx=2, hi_idx=7):
        """Arc length on the seat pan where the centreline passes X = x."""
        s0, s1 = self.sc[lo_idx], self.sc[hi_idx]
        ss = np.linspace(s0, s1, 2000)
        xs = np.array([self.frame_at(s)[0][0] for s in ss])
        i = int(np.argmin(abs(xs - x)))
        return float(ss[i])

    def thickness(self, s):
        t = self.ft(s)
        d0, d1 = self.t_end0 / 2, self.t_end1 / 2
        if s < d0:
            f = math.sqrt(max(0.12, 1 - ((d0 - s) / d0) ** 2))
            return t * f
        if s > self.L - d1:
            f = math.sqrt(max(0.12, 1 - ((s - (self.L - d1)) / d1) ** 2))
            return t * f
        return t

    # ---- cross-section ----------------------------------------------------
    def centre_curve(self, s, nA=12, nB=9):
        """Section centreline for u >= 0: returns u, v, tangent angle, and 'a' (end of flat zone)."""
        w, d, R = self.fw(s), self.fd(s), self.fr(s)
        R = min(R, 0.4 * w)
        re = self.roll_end
        a = w - R
        for _ in range(6):
            al = math.atan(2 * d * a / w ** 2)
            a = w - R * (math.sin(al) + math.sin(re))
        al = math.atan(2 * d * a / w ** 2)
        ua = np.linspace(0, a, nA, endpoint=False)
        va = d * (ua / w) ** 2
        ta = np.arctan(2 * d * ua / w ** 2)
        Pa = np.array([a, d * (a / w) ** 2])
        C = Pa + R * np.array([math.sin(al), -math.cos(al)])
        ph = np.linspace(0, re + al, nB)
        ub = C[0] - R * np.sin(al - ph)
        vb = C[1] + R * np.cos(al - ph)
        tb = al - ph
        return (np.concatenate([ua, ub]), np.concatenate([va, vb]), np.concatenate([ta, tb]), a)

    def ring(self, s, t=None, nC=5):
        t = self.thickness(s) if t is None else t
        uc, vc, tc, _ = self.centre_curve(s)
        nu, nv = -np.sin(tc), np.cos(tc)
        top = np.stack([uc + nu * t / 2, vc + nv * t / 2], 1)
        bot = np.stack([uc - nu * t / 2, vc - nv * t / 2], 1)
        e = np.array([uc[-1], vc[-1]])
        a0 = tc[-1] + math.pi / 2
        ca = np.linspace(a0, a0 - math.pi, nC + 2)[1:-1]
        cap = np.stack([e[0] + np.cos(ca) * t / 2, e[1] + np.sin(ca) * t / 2], 1)
        half = np.concatenate([top, cap, bot[::-1]])
        mir = half[::-1].copy()
        mir[:, 0] *= -1
        return np.concatenate([half, mir[1:-1]])

    def to3d(self, s, pts2):
        Pp, T, N = self.frame_at(s)
        out = []
        for u, v in pts2:
            xz = Pp + N * v
            out.append(cq.Vector(float(xz[0]), float(u), float(xz[1])))
        return out

    def surface_point(self, s, u, side=+1):
        """Point on the top (side=+1) or bottom (side=-1) skin at station s, lateral u>=0."""
        uc, vc, tc, _ = self.centre_curve(s, nA=400, nB=200)
        t = self.thickness(s)
        uu_ = uc + side * (-np.sin(tc)) * t / 2
        vv_ = vc + side * np.cos(tc) * t / 2
        # take the first branch (monotonic in u up to the roll's widest point)
        i = int(np.argmin(abs(uu_ - u)))
        Pp, T, N = self.frame_at(s)
        xz = Pp + N * vv_[i]
        return np.array([xz[0], u, xz[1]])

    def stations(self, n_mid=46):
        d0, d1 = self.t_end0 / 2, self.t_end1 / 2
        a = d0 * (1 - np.cos(np.linspace(0, math.pi / 2, 6)))
        b = np.linspace(d0, self.L - d1, n_mid)[1:-1]
        c = self.L - d1 * (1 - np.cos(np.linspace(0, math.pi / 2, 6)))[::-1]
        return np.concatenate([a, b, c])


def build_shell_body(g: ShellGeom):
    rings = [np.asarray([[v.x, v.y, v.z] for v in g.to3d(s, g.ring(s))]) for s in g.stations()]
    # One shared (averaged chord-length) parametrisation for every ring: the rings then have
    # identical knot vectors, so the loft does not merge them into one enormous surface.
    ts = []
    for r in rings:
        d = np.linalg.norm(np.diff(np.vstack([r, r[:1]]), axis=0), axis=1)
        ts.append(np.concatenate([[0.0], np.cumsum(d)]) / d.sum())
    params = list(np.mean(ts, axis=0))
    wires = []
    for r in rings:
        pts = [cq.Vector(*p) for p in r]
        wires.append(cq.Wire.assembleEdges([cq.Edge.makeSpline(pts, periodic=True, parameters=params)]))
    body = loft(wires)
    # split the single closed side face into pieces: a closed periodic face does not survive
    # a STEP round trip, a divided one does
    from OCP.ShapeUpgrade import ShapeUpgrade_ShapeDivideClosed
    div = ShapeUpgrade_ShapeDivideClosed(body.wrapped)
    div.SetNbSplitPoints(3)
    div.Perform()
    return cq.Shape.cast(div.Result())


def build_seat_fill(g: ShellGeom, s0, s1, drop, skin=+1, n=9):
    """Solid filling everything below the shell's top skin (skin=+1) or below its underside
    (skin=-1, so it only touches the shell) between stations s0..s1."""
    wires = []
    for s in np.linspace(s0, s1, n):
        uc, vc, tc, _ = g.centre_curve(s, *((12, 9) if skin > 0 else (40, 30)))
        t = g.thickness(s)
        off = t / 2 if skin > 0 else t / 2 + 0.6 * g.k      # small gap so the flat facets never cut into the wall
        top = np.stack([uc - skin * np.sin(tc) * off, vc + skin * np.cos(tc) * off], 1)
        # outer end of the rolled edge, then straight down and across the bottom
        u_ext = g.fw(s) + t * 1.5            # beyond the skirt's outermost point
        right = np.concatenate([top, [[u_ext, top[-1, 1] - t], [u_ext, -drop]]])
        left = right[::-1].copy()
        left[:, 0] *= -1
        pts2 = np.concatenate([right, left[:-1]])
        pts = g.to3d(s, pts2)
        wires.append(cq.Wire.makePolygon(pts, close=True))
    b = BRepOffsetAPI_ThruSections(True, True, 1e-6)
    b.CheckCompatibility(False)
    for w in wires:
        b.AddWire(w.wrapped)
    b.Build()
    return cq.Solid(b.Shape())


def build_ribs(g: ShellGeom, s_from, s_to, pitch, r, margin):
    """Grip ribs across the backrest's front face (half-embedded round beads)."""
    ribs = []
    s = s_from
    while s <= s_to + 1e-9:
        uc, vc, tc, a = g.centre_curve(s, nA=40, nB=2)
        t = g.thickness(s)
        keep = uc <= a - margin
        u = uc[keep]
        v = vc[keep] + np.cos(tc[keep]) * t / 2
        u2 = u - np.sin(tc[keep]) * t / 2
        half = np.stack([u2, v], 1)
        mir = half[::-1].copy()
        mir[:, 0] *= -1
        pts2 = np.concatenate([mir[:-1], half])
        pts = g.to3d(s, pts2)
        path = cq.Wire.assembleEdges([cq.Edge.makeSpline(pts)])
        tan = (pts[1] - pts[0]).normalized()
        circ = cq.Wire.makeCircle(r, pts[0], tan)
        bead = cq.Solid.sweep(circ, [], path, makeSolid=True, isFrenet=False)
        bead = bead.fuse(cq.Solid.makeSphere(r, pts[0]), cq.Solid.makeSphere(r, pts[-1]))
        ribs.append(bead)
        s += pitch
    return ribs


def build_shell_body_mesh(g: ShellGeom, n_mid=300, nA=40, nB=26, nC=8):
    """Watertight structured mesh of the shell body, from the same sections as the loft."""
    import trimesh
    import mapbox_earcut as earcut
    d0, d1 = g.t_end0 / 2, g.t_end1 / 2
    a = d0 * (1 - np.cos(np.linspace(0, math.pi / 2, 14)))
    b = np.linspace(d0, g.L - d1, n_mid)[1:-1]
    c = g.L - d1 * (1 - np.cos(np.linspace(0, math.pi / 2, 14)))[::-1]
    stations = np.concatenate([a, b, c])
    rings2, rings3 = [], []
    for s in stations:
        t = g.thickness(s)
        uc, vc, tc, _ = g.centre_curve(s, nA=nA, nB=nB)
        nu, nv = -np.sin(tc), np.cos(tc)
        top = np.stack([uc + nu * t / 2, vc + nv * t / 2], 1)
        bot = np.stack([uc - nu * t / 2, vc - nv * t / 2], 1)
        e = np.array([uc[-1], vc[-1]])
        a0 = tc[-1] + math.pi / 2
        ca = np.linspace(a0, a0 - math.pi, nC + 2)[1:-1]
        cap = np.stack([e[0] + np.cos(ca) * t / 2, e[1] + np.sin(ca) * t / 2], 1)
        half = np.concatenate([top, cap, bot[::-1]])
        mir = half[::-1].copy()
        mir[:, 0] *= -1
        ring = np.concatenate([half, mir[1:-1]])
        Pp, T, N = g.frame_at(s)
        xz = Pp[None, :] + ring[:, 1:2] * N[None, :]
        rings2.append(ring)
        rings3.append(np.stack([xz[:, 0], ring[:, 0], xz[:, 1]], 1))
    R = np.array(rings3)                   # (ns, nr, 3)
    ns, nr, _ = R.shape
    verts = R.reshape(-1, 3)
    faces = []
    idx = np.arange(ns * nr).reshape(ns, nr)
    for i in range(ns - 1):
        a_, b_ = idx[i], idx[i + 1]
        a1, b1 = np.roll(a_, -1), np.roll(b_, -1)
        faces.append(np.stack([a_, b_, b1], 1))
        faces.append(np.stack([a_, b1, a1], 1))
    faces = [np.concatenate(faces)]
    for end, flip in ((0, True), (ns - 1, False)):
        tri = earcut.triangulate_float64(rings2[end], np.array([nr], dtype=np.uint32)).reshape(-1, 3)
        tri = idx[end][tri]
        faces.append(tri[:, ::-1] if flip else tri)
    m = trimesh.Trimesh(verts, np.concatenate(faces), process=True)
    m.merge_vertices()
    if m.volume < 0:
        m.invert()
    return m


def rib_paths(g: ShellGeom, s_from, s_to, pitch, margin, n=60):
    """Centre-lines (on the front skin) and outward normals for each grip rib."""
    out = []
    s = s_from
    while s <= s_to + 1e-9:
        uc, vc, tc, a = g.centre_curve(s, nA=400, nB=2)
        t = g.thickness(s)
        keep = uc <= a - margin
        u = uc[keep] - np.sin(tc[keep]) * t / 2
        v = vc[keep] + np.cos(tc[keep]) * t / 2
        nu, nv = -np.sin(tc[keep]), np.cos(tc[keep])
        # resample to n points from -umax..umax
        uu_ = np.linspace(-u[-1], u[-1], n)
        vv_ = np.interp(abs(uu_), u, v)
        nnu = np.interp(abs(uu_), u, nu) * np.sign(uu_)
        nnv = np.interp(abs(uu_), u, nv)
        Pp, T, N = g.frame_at(s)
        pts = np.stack([Pp[0] + N[0] * vv_, uu_, Pp[1] + N[1] * vv_], 1)
        nrm = np.stack([N[0] * nnv, nnu, N[1] * nnv], 1)
        nrm /= np.linalg.norm(nrm, axis=1)[:, None]
        out.append((pts, nrm))
        s += pitch
    return out


def rib_mesh(pts, nrm, r, nseg=12, ncap=4, sink=0.0):
    """Watertight round bead along pts, centre sunk `sink` below the skin, round ends."""
    import trimesh
    pts = pts - nrm * sink
    T = np.gradient(pts, axis=0)
    T /= np.linalg.norm(T, axis=1)[:, None]
    n1 = nrm - (nrm * T).sum(1)[:, None] * T
    n1 /= np.linalg.norm(n1, axis=1)[:, None]
    n2 = np.cross(T, n1)
    ang = np.linspace(0, 2 * math.pi, nseg, endpoint=False)
    rings = [pts[i] + r * (np.cos(ang)[:, None] * n1[i] + np.sin(ang)[:, None] * n2[i]) for i in range(len(pts))]
    verts = list(np.concatenate(rings))
    faces = []
    def ring_faces(i0, i1):
        for j in range(nseg):
            a, b = i0 + j, i0 + (j + 1) % nseg
            c, d = i1 + (j + 1) % nseg, i1 + j
            faces.append([a, b, c])
            faces.append([a, c, d])
    for i in range(len(pts) - 1):
        ring_faces(i * nseg, (i + 1) * nseg)
    # hemispherical caps
    for end, sgn in ((0, -1), (len(pts) - 1, 1)):
        prev = end * nseg
        for k in range(1, ncap):
            ph = k / ncap * math.pi / 2
            ring = pts[end] + sgn * T[end] * r * math.sin(ph) + r * math.cos(ph) * (
                np.cos(ang)[:, None] * n1[end] + np.sin(ang)[:, None] * n2[end])
            base = len(verts)
            verts.extend(ring)
            if sgn > 0:
                ring_faces(prev, base)
            else:
                ring_faces(base, prev)
            prev = base
        pole = len(verts)
        verts.append(pts[end] + sgn * T[end] * r)
        for j in range(nseg):
            a, b = prev + j, prev + (j + 1) % nseg
            faces.append([a, b, pole] if sgn > 0 else [b, a, pole])
    m = trimesh.Trimesh(np.array(verts), np.array(faces), process=True)
    if m.volume < 0:
        m.invert()
    return m


# under-seat ribs (full-size product only): stiffen the seat front and carry the
# backrest's lean moment through the junction.  Hidden under the seat.
SEAT_RIB_Y = (50.0, 105.0, 155.0)   # lateral positions (mirrored)
SEAT_RIB_T = 4.5
SEAT_RIB_DEPTH = 34.0


def seat_rib_depth(x, z, k=1.0):
    """Depth profile along a rib: shallow at the front edge, full under the seat,
    fading out before the junction (the thickened junction carries the back load)."""
    D = SEAT_RIB_DEPTH * k
    if x > 330 * k:
        return D * max(0.0, (405 * k - x) / (75 * k)) ** 0.8
    if x < 95 * k:
        # die out before the seat curls up into the back, so nothing shows from behind
        return D * max(0.0, (x - 38 * k) / (57 * k)) ** 0.7
    return D


def seat_rib_meshes(g: ShellGeom):
    import trimesh
    k = g.k
    out = []
    s0 = g.s_at_x(404 * k, 1, 6)
    s1 = g.s_at_x(38 * k, 3, 7)
    ss = np.linspace(s0, s1, 90)
    for yr in SEAT_RIB_Y:
        for side in (+1, -1):
            y = side * yr * k
            top, bot = [], []
            for s in ss:
                p = g.surface_point(s, abs(y), side=-1)
                Pp, T, N = g.frame_at(s)
                dep = max(0.6 * k, seat_rib_depth(p[0], p[2], k))
                q_in = np.array([p[0] + N[0] * 1.0 * k, y, p[2] + N[1] * 1.0 * k])   # overlap into the shell
                q_out = np.array([p[0] - N[0] * dep, y, p[2] - N[1] * dep])
                top.append(q_in)
                bot.append(q_out)
            top, bot = np.array(top), np.array(bot)
            h = SEAT_RIB_T * k / 2
            verts = np.concatenate([top + [0, -h, 0], bot + [0, -h, 0], top + [0, h, 0], bot + [0, h, 0]])
            n = len(ss)
            idx = lambda a, i: a * n + i
            faces = []
            for i in range(n - 1):
                for a, b, flip in ((0, 1, False), (2, 3, True), (0, 2, True), (1, 3, False)):
                    f1 = [idx(a, i), idx(b, i), idx(b, i + 1)]
                    f2 = [idx(a, i), idx(b, i + 1), idx(a, i + 1)]
                    if flip:
                        f1, f2 = f1[::-1], f2[::-1]
                    faces += [f1, f2]
            for i, flip in ((0, True), (n - 1, False)):
                q = [idx(0, i), idx(1, i), idx(3, i), idx(2, i)]
                f1, f2 = [q[0], q[1], q[2]], [q[0], q[2], q[3]]
                if flip:
                    f1, f2 = f1[::-1], f2[::-1]
                faces += [f1, f2]
            m = trimesh.Trimesh(verts, np.array(faces), process=True)
            if m.volume < 0:
                m.invert()
            out.append((m, abs(yr * k)))
    return out



def support_fin_mesh(g: ShellGeom, gap=0.2, width=0.8, min_h=0.7):
    """Breakaway support for the print: a thin wall standing on the bed under the stretch of
    the shell's lower side edge that curves up off the bed (the back's waist).  Assembled
    coordinates; the bed is the shell's -Y extreme."""
    import trimesh
    ss = np.linspace(g.sc[6], g.sc[14], 400)
    ext = []
    for s in ss:
        uc, vc, tc, _ = g.centre_curve(s, nA=4, nB=24)
        t = g.thickness(s)
        u_out = uc[-1] + t / 2
        Pp, T, N = g.frame_at(s)
        xz = Pp + N * vc[-1]
        ext.append((s, u_out, xz, N))
    y_bed = -max(e[1] for e in [(0, g.fw(x) + g.thickness(x) / 2) for x in np.linspace(0, g.L, 800)])
    runs, cur = [], []
    for s, u_out, xz, N in ext:
        h = (-u_out - gap) - y_bed
        if h >= min_h:
            cur.append((xz, N, h))
        elif cur:
            runs.append(cur)
            cur = []
    if cur:
        runs.append(cur)
    meshes = []
    for run in runs:
        if len(run) < 3:
            continue
        verts, faces = [], []
        n = len(run)
        for xz, N, h in run:
            for off in (-width / 2, width / 2):
                p = xz + N * off
                verts.append([p[0], y_bed, p[1]])
                verts.append([p[0], y_bed + h, p[1]])
        idx = lambda i, side, top: 4 * i + 2 * side + top
        for i in range(n - 1):
            for a, b in (((0, 0), (0, 1)), ((1, 1), (1, 0)), ((0, 1), (1, 1)), ((1, 0), (0, 0))):
                q = [idx(i, *a), idx(i, *b), idx(i + 1, *b), idx(i + 1, *a)]
                faces += [[q[0], q[1], q[2]], [q[0], q[2], q[3]]]
        for i, flip in ((0, False), (n - 1, True)):
            q = [idx(i, 0, 0), idx(i, 1, 0), idx(i, 1, 1), idx(i, 0, 1)]
            f1, f2 = [q[0], q[1], q[2]], [q[0], q[2], q[3]]
            faces += ([f1[::-1], f2[::-1]] if flip else [f1, f2])
        m = trimesh.Trimesh(np.array(verts), np.array(faces), process=True)
        if m.volume < 0:
            m.invert()
        meshes.append(m)
    return meshes
