"""
Engineering checks for the full-size product and the print kit:
mass / centre of gravity, tipping, post and seat stresses, backrest flex,
and ergonomic fit against anthropometric data.

These are hand-calculation-level models (rigid-body statics, 1-D beam theory)
meant to catch real problems early.  They are not a substitute for physical
BIFMA testing of a prototype.
"""
import math
import numpy as np
from shapely.geometry import MultiPoint, Point

from . import params as P

G = 9.81

# effective densities (g/cm3) = material density x solid fraction of the real part
DENSITY = {
    "shell":   (0.905, "PP impact copolymer, solid wall"),
    "frame_L": (0.75, "PA6-GF30 (1.36) gas-assist hollow, ~55% solid"),
    "frame_R": (0.75, "PA6-GF30 (1.36) gas-assist hollow, ~55% solid"),
    "base":    (0.81, "cast aluminium (2.70), cored, ~30% solid"),
    "sleeve":  (1.00, "6063-T6 aluminium extrusion, 3 mm wall"),
    "head":    (0.90, "cast aluminium head + 3 mm wall inner tube"),
    "top":     (0.80, "moulded solid-core top / HPL on particleboard"),
    "plug":    (1.10, "moulded end cap"),
    "seat_beam": (0.95, "6063-T6 aluminium tube (2.70), 2.5 mm wall"),
}


def mass_properties(meshes):
    rows, tot, mom = [], 0.0, np.zeros(3)
    for n, m in meshes.items():
        rho, note = DENSITY[n]
        kg = m.volume / 1000.0 * rho / 1000.0
        c = m.center_mass
        rows.append(dict(part=n, volume_L=round(m.volume / 1e6, 3), density=rho, mass_kg=round(kg, 2), note=note))
        tot += kg
        mom += kg * c
    return rows, tot, mom / tot


def support_polygon(meshes, zmax=1.0):
    pts = []
    for m in meshes.values():
        c = m.triangles_center
        sel = (c[:, 2] < zmax) & (m.face_normals[:, 2] < -0.9)
        if sel.any():
            pts.append(m.vertices[np.unique(m.faces[sel].ravel())][:, :2])
    return MultiPoint(np.concatenate(pts)).convex_hull


def _edges(poly):
    xy = np.asarray(poly.exterior.coords)[:-1]
    if poly.exterior.is_ccw is False:
        xy = xy[::-1]
    out = []
    for i in range(len(xy)):
        a, b = xy[i], xy[(i + 1) % len(xy)]
        d = (b - a) / np.linalg.norm(b - a)
        n = np.array([d[1], -d[0]])          # outward for a CCW ring
        out.append((a, n))
    return out


def tip_margin(poly, weight_N, cog, loads):
    """loads: list of (Fx, Fy, Fz, x, y, z) in N and mm (Fz negative = downward).
    Returns (min ratio resisting/overturning over all edges, worst edge normal).
    ratio > 1 means it does not tip."""
    worst = (math.inf, None)
    for a, n in _edges(poly):
        def d(x, y):
            return (np.array([x, y]) - a) @ n          # >0 outside
        m_over, m_res = 0.0, 0.0
        # self weight
        mw = weight_N * d(cog[0], cog[1])
        (m_over if mw > 0 else m_res).__class__
        if mw > 0:
            m_over += mw
        else:
            m_res += -mw
        for Fx, Fy, Fz, x, y, z in loads:
            # vertical part
            mv = -Fz * d(x, y)
            # horizontal part: tips about the floor edge with lever arm z
            mh = (Fx * n[0] + Fy * n[1]) * z
            for mm in (mv, mh):
                if mm > 0:
                    m_over += mm
                else:
                    m_res += -mm
        ratio = math.inf if m_over <= 1e-9 else m_res / m_over
        if ratio < worst[0]:
            worst = (ratio, n)
    return worst


def max_load_before_tip(poly, weight_N, cog, base_loads, unit_load):
    """Scale unit_load (a single load tuple for 1 N) until tipping. Returns newtons."""
    lo, hi = 0.0, 20000.0
    if tip_margin(poly, weight_N, cog, base_loads + [tuple(v * hi if i < 3 else v for i, v in enumerate(unit_load))])[0] > 1:
        return hi
    for _ in range(60):
        mid = (lo + hi) / 2
        L = tuple(v * mid if i < 3 else v for i, v in enumerate(unit_load))
        if tip_margin(poly, weight_N, cog, base_loads + [L])[0] > 1:
            lo = mid
        else:
            hi = mid
    return lo


# ------------------------------------------------------------------ beams
def section_props(ring):
    """Area, centroid v and second moment about the centroidal u-axis for a closed (u, v) polygon."""
    u, v = ring[:, 0], ring[:, 1]
    u1, v1 = np.roll(u, -1), np.roll(v, -1)
    cr = u * v1 - u1 * v
    A = cr.sum() / 2
    cv = ((v + v1) * cr).sum() / (6 * A)
    Iuu = ((v ** 2 + v * v1 + v1 ** 2) * cr).sum() / 12
    I = abs(Iuu) - abs(A) * cv ** 2
    c = max(v.max() - cv, cv - v.min())
    return abs(A), cv, I, c


def section_props_with_ribs(g, s):
    """Section properties at station s, including the under-seat ribs of the real product."""
    from .shell import SEAT_RIB_Y, SEAT_RIB_T, seat_rib_depth
    ring = g.ring(s)
    A, cv, I, c = section_props(ring)
    if g.mode != "real":
        return A, cv, I, c
    Pp, T, N = g.frame_at(s)
    parts = [(A, cv, I)]
    vmin = ring[:, 1].min()
    for yr in SEAT_RIB_Y:
        p = g.surface_point(s, yr * g.k, side=-1)
        dep = seat_rib_depth(p[0], p[2], g.k)
        if dep <= 0.5:
            continue
        v_under = float(np.dot(np.array([p[0], p[2]]) - Pp, N))
        a = SEAT_RIB_T * g.k * dep
        vc = v_under - dep / 2
        parts += [(a, vc, SEAT_RIB_T * g.k * dep ** 3 / 12)] * 2
        vmin = min(vmin, v_under - dep)
    At = sum(p[0] for p in parts)
    vbar = sum(p[0] * p[1] for p in parts) / At
    It = sum(p[2] + p[0] * (p[1] - vbar) ** 2 for p in parts)
    ct = max(ring[:, 1].max() - vbar, vbar - vmin)
    return At, vbar, It, ct


def back_flex(g, E_mpa, F_N, z_load, s_clamp):
    """Cantilever from station s_clamp to the top, horizontal force F at height z_load.
    Returns rotation (deg) at the load height, horizontal deflection (mm), peak stress (MPa), where."""
    ss = np.linspace(s_clamp, g.L, 500)
    zs = np.array([g.frame_at(s)[0][1] for s in ss])
    props = [section_props_with_ribs(g, s) for s in ss]
    I = np.array([p[2] for p in props])
    c = np.array([p[3] for p in props])
    arm = np.clip(z_load - zs, 0, None)
    M = F_N * arm                                  # N*mm
    ds = np.gradient(ss)
    theta = float(np.sum(M / (E_mpa * I) * ds))
    delta = float(np.sum(M * arm / (E_mpa * I) * ds))
    sig = M * c / I
    i = int(np.argmax(sig))
    return dict(rotation_deg=round(math.degrees(theta), 2), deflection_mm=round(delta, 2),
                peak_stress_MPa=round(float(sig[i]), 2), peak_at_z_mm=round(float(zs[i]), 1),
                peak_strain_pct=round(float(sig[i]) / E_mpa * 100, 3),
                min_I_mm4=round(float(I.min()), 2))


def seat_pan_stress(g, F_N, x_load, x_support):
    """Seat front cantilever beyond the bearing pads (1-D beam across the full shell section)."""
    s_sup = g.s_at_x(x_support)
    A, cv, I, c = section_props_with_ribs(g, s_sup)
    M = F_N * (x_load - x_support)
    return dict(section_I_mm4=round(I, 0), moment_Nm=round(M / 1000, 1), stress_MPa=round(M * c / I, 2))


def post_stress(F_N, lever_mm):
    def rect_tube(b, h, t):
        I = (b * h ** 3 - (b - 2 * t) * (h - 2 * t) ** 3) / 12
        return I / (h / 2)
    Ssl = rect_tube(P.SLEEVE[1], P.SLEEVE[0], 3.0)
    Sin = rect_tube(P.INNER[1], P.INNER[0], 3.0)
    M = F_N * lever_mm
    return dict(moment_Nm=round(M / 1000, 1), sleeve_stress_MPa=round(M / Ssl, 1),
                inner_stress_MPa=round(M / Sin, 1), yield_6063T6_MPa=214)


# -------------------------------------------------------------- ergonomics
ANTHRO = {   # cm; ANSUR II (Gordon 2014) adult proxy, see docs
    "F5": dict(popliteal=35.0, bpl=44.1, bkl=54.1, hip=31.1, thigh=14.5, elbow=18.9, shoulder=51.5, abdo=18.4),
    "F50": dict(popliteal=38.7, bpl=48.3, bkl=58.9, hip=35.3, thigh=16.7, elbow=23.3, shoulder=56.4, abdo=22.7),
    "M50": dict(popliteal=43.0, bpl=50.2, bkl=61.7, hip=34.4, thigh=18.0, elbow=24.6, shoulder=60.3, abdo=25.1),
    "M95": dict(popliteal=47.1, bpl=54.8, bkl=66.9, hip=38.7, thigh=20.7, elbow=29.1, shoulder=65.3, abdo=32.0),
    "Large": dict(popliteal=42.0, bpl=52.0, bkl=64.0, hip=54.5, thigh=24.0, elbow=25.0, shoulder=58.0, abdo=38.0),
}
SHOE = 2.5


def ergonomics(seat_h=P.SEAT_HEIGHT, seat_d=400.0, seat_w=P.SEAT_WIDTH):
    rows = []
    for who, a in ANTHRO.items():
        pop = (a["popliteal"] + SHOE) * 10
        # best desk height: elbow height above the seat surface (seat surface ~ front crest - 10 mm)
        ideal = seat_h - 10 + a["elbow"] * 10 + 20
        thigh_ok = [h for h in P.DESK_HEIGHTS if h - P.TOP_T - (seat_h - 10) >= a["thigh"] * 10 + 20]
        best = min(thigh_ok or P.DESK_HEIGHTS, key=lambda h: abs(h - ideal))    # closest to elbow height with thigh room
        gap_need = a["abdo"] * 10 + 30
        belly = P.BELLY[0]                     # the near edge curves in at the middle
        gap = next((g + belly for g in P.DESK_GAPS if g + belly >= gap_need), None)
        over = seat_h - pop
        rows.append(dict(
            who=who,
            seat_vs_popliteal_mm=round(over, 0),
            with_spine_footrest_mm=round(over - P.BASE_H, 0) if over > 30 else None,   # only worth it when well over
            seat_depth_pct_bpl=round(seat_d / (a["bpl"] * 10) * 100, 0),
            hip_room_mm=round(seat_w - a["hip"] * 10, 0),
            best_desk_height=best,
            elbow_to_desk_mm=round(best - ideal + 20, 0),
            desk_heights_with_thigh_room=thigh_ok,
            reach_setting=f"{gap:.0f} mm" if gap else f"{P.DESK_GAPS[-1] + P.BELLY[0]:.0f} mm + back flex",
            knee_x_mm=round(-5 + a["bkl"] * 10, 0),
        ))
    return rows


def pin_alignment(design):
    """Geometry check: for every height and reach setting, the pin axis must pass through
    empty space (a hole) in every part it crosses.  Also checks that the dovetail tenon
    really sits inside the desktop's track."""
    import cadquery as cq
    k = design.k
    out = []
    sleeve = design.sleeve()
    sx = P.SLEEVE[0]
    for hi, h in enumerate(P.DESK_HEIGHTS):
        head = design.head(hi)
        z = P.SLEEVE_PIN_Z * k
        probes = [cq.Vector((P.POST_X + dx) * k, 0, z) for dx in np.linspace(-sx / 2 - 3, sx / 2 + 3, 15)]
        out.append(dict(check="height pin", setting=f"{h:.0f} mm",
                        passes_head=all(not head.isInside(p, 1e-4) for p in probes),
                        passes_sleeve=all(not sleeve.isInside(p, 1e-4) for p in probes)))
    hi = P.DEFAULT_HEIGHT_INDEX
    head = design.head(hi)
    zb = (P.DESK_HEIGHTS[hi] - P.TOP_T) * k
    for gi, g in enumerate(P.DESK_GAPS):
        top = design.top(hi, gi)
        x = (P.POST_X + P.DETENT_OFF) * k
        zs = np.linspace(zb - (P.INDEX_BOSS[1] + 2) * k, zb + (P.TENON_H + 5) * k, 25)
        probes = [cq.Vector(x, 0, z) for z in zs]
        out.append(dict(check="reach pin", setting=f"{g:.0f} mm gap",
                        passes_top=all(not top.isInside(p, 1e-4) for p in probes),
                        passes_head=all(not head.isInside(p, 1e-4) for p in probes)))
    # the tenon must be inside the track: a point in the tenon's middle, above the underside
    tx = (P.POST_X - 100) * k
    pt = cq.Vector(tx, 0, zb + P.TENON_H * k * 0.5)
    out.append(dict(check="dovetail engaged", setting="tenon inside track",
                    passes_head=head.isInside(pt, 1e-4), passes_top=not design.top(hi, 1).isInside(pt, 1e-4)))
    return out
