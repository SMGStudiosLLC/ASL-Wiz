"""Small geometry helpers shared by the part builders."""
import math
import numpy as np
import cadquery as cq


def _unit(v):
    v = np.asarray(v, float)
    return v / np.linalg.norm(v)


def filleted_polygon(pts, radii):
    """Rounded polygon. Returns a list of segments and per-corner arc data.

    pts   : list of (x, y) vertices, counter-clockwise
    radii : fillet radius per vertex
    Segments are ('line', p0, p1) or ('arc', p0, pmid, p1). Corner data holds
    centre, radius and tangent points so callers can place features on arcs.
    """
    n = len(pts)
    P = [np.asarray(p, float) for p in pts]
    corners = []
    for i in range(n):
        a, b, c = P[i - 1], P[i], P[(i + 1) % n]
        u1, u2 = _unit(a - b), _unit(c - b)
        ang = math.acos(max(-1.0, min(1.0, float(np.dot(u1, u2)))))
        r = radii[i]
        d = r / math.tan(ang / 2)
        t_in, t_out = b + u1 * d, b + u2 * d
        bis = _unit(u1 + u2)
        centre = b + bis * (r / math.sin(ang / 2))
        mid = centre + _unit(b - centre) * r
        corners.append(dict(vertex=b, t_in=t_in, t_out=t_out, centre=centre, mid=mid, r=r, angle=ang))
    segs = []
    for i in range(n):
        c0, c1 = corners[i], corners[(i + 1) % n]
        segs.append(('arc', c0['t_in'], c0['mid'], c0['t_out']))
        segs.append(('line', c0['t_out'], c1['t_in']))
    return segs, corners


def offset_polygon(pts, dists):
    """Offset each edge i (pts[i] -> pts[i+1]) inward by dists[i]; CCW polygon."""
    n = len(pts)
    P = [np.asarray(p, float) for p in pts]
    lines = []
    for i in range(n):
        a, b = P[i], P[(i + 1) % n]
        d = _unit(b - a)
        nrm = np.array([-d[1], d[0]])      # left normal = inward for CCW
        lines.append((a + nrm * dists[i], d))
    out = []
    for i in range(n):
        (p1, d1), (p2, d2) = lines[i - 1], lines[i]
        A = np.array([d1, -d2]).T
        t = np.linalg.solve(A, p2 - p1)
        out.append(p1 + d1 * t[0])
    return out


def segs_to_wire(segs, to3d):
    """Build a closed cq.Wire from 2D segments using a 2D->3D mapping."""
    edges = []
    for s in segs:
        if s[0] == 'line':
            p0, p1 = to3d(s[1]), to3d(s[2])
            if (p1 - p0).Length > 1e-6:
                edges.append(cq.Edge.makeLine(p0, p1))
        else:
            edges.append(cq.Edge.makeThreePointArc(to3d(s[1]), to3d(s[2]), to3d(s[3])))
    return cq.Wire.assembleEdges(edges)


def rounded_rect_wire(cx, cy, w, h, r, z=0.0):
    """Rounded rectangle in an XY plane at height z."""
    return (cq.Workplane("XY", origin=(0, 0, z))
            .center(cx, cy).sketch().rect(w, h).vertices().fillet(r).finalize()
            ._getFaces()[0].outerWire())


def rrect_prism(cx, cy, w, h, r, z0, z1):
    """Vertical rounded-rectangle prism from z0 to z1."""
    return (cq.Workplane("XY", origin=(0, 0, z0)).center(cx, cy)
            .sketch().rect(w, h).vertices().fillet(r).finalize()
            .extrude(z1 - z0).val())


def box(x0, x1, y0, y1, z0, z1):
    return cq.Solid.makeBox(x1 - x0, y1 - y0, z1 - z0, cq.Vector(x0, y0, z0))


def teardrop_hole_y(x, z, y0, y1, d):
    """Horizontal hole along Y with a 45-degree teardrop roof (+Z) so it prints without support."""
    r = d / 2
    wp = cq.Workplane("XZ", origin=(0, y1, 0)).center(x, z)
    circ = wp.circle(r).extrude(y1 - y0).val()
    tri = (cq.Workplane("XZ", origin=(0, y1, 0))
           .polyline([(x - r * 0.7071, z + r * 0.7071), (x, z + r * 1.4142), (x + r * 0.7071, z + r * 0.7071), (x, z)])
           .close().extrude(y1 - y0).val())
    return circ.fuse(tri).clean()
