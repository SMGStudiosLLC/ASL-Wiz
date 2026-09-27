"""
Verification: mesh health, printability, fits and interference.
Every number in docs/VERIFICATION.md comes from these functions.
"""
import itertools
import math
import numpy as np
import trimesh

from .mesh import to_manifold, from_manifold


def mesh_health(m: trimesh.Trimesh):
    return dict(watertight=bool(m.is_watertight), winding=bool(m.is_winding_consistent),
                volume_mm3=float(m.volume), euler=int(m.euler_number), faces=int(len(m.faces)))


def printability(m: trimesh.Trimesh, max_angle=45.0, bed_eps=0.25, min_cluster=0.8):
    """m must already be in its print pose (bed at z = 0)."""
    n = m.face_normals
    c = m.triangles_center
    a = m.area_faces
    bed = (c[:, 2] < 0.05) & (n[:, 2] < -0.95)
    lim = -math.cos(math.radians(max_angle))
    over = (n[:, 2] < lim) & (c[:, 2] > bed_eps)
    # cluster overhanging faces
    clusters = []
    if over.any():
        idx = np.where(over)[0]
        sub = m.submesh([idx], append=True, repair=False)
        for comp in sub.split(only_watertight=False):
            area = float(comp.area)
            if area < min_cluster:
                continue
            fn = comp.face_normals
            worst = float(np.degrees(np.arccos(np.clip(-fn[:, 2], -1, 1))).min())
            clusters.append(dict(area_mm2=round(area, 2), centre=[round(v, 1) for v in comp.centroid],
                                 z=round(float(comp.bounds[0][2]), 2),
                                 steepest_from_horizontal_deg=round(worst, 1),
                                 span_mm=round(float(max(comp.extents[:2])), 2)))
    clusters.sort(key=lambda d: -d["area_mm2"])
    return dict(bed_contact_mm2=round(float(a[bed].sum()), 1),
                overhang_area_mm2=round(float(a[over].sum()), 2),
                overhang_clusters=clusters[:8],
                extents_mm=[round(v, 1) for v in m.extents])


def wall_thickness(m: trimesh.Trimesh, n=4000, seed=1):
    """Ray-cast inward from random surface points; returns percentiles of local thickness (mm)."""
    rng = np.random.default_rng(seed)
    pts, fi = trimesh.sample.sample_surface(m, n, seed=seed)
    dirs = -m.face_normals[fi]
    origins = pts + dirs * 1e-4
    loc, ray_idx, _ = m.ray.intersects_location(origins, dirs, multiple_hits=False)
    d = np.full(n, np.nan)
    d[ray_idx] = np.linalg.norm(loc - origins[ray_idx], axis=1)
    d = d[np.isfinite(d)]
    return dict(p1=round(float(np.percentile(d, 1)), 2), p5=round(float(np.percentile(d, 5)), 2),
                median=round(float(np.median(d)), 2))


def interference(meshes: dict, ignore=0.05):
    """Pairwise overlap volume between assembled parts (mm3). Contact is fine, overlap is not."""
    mans = {k: to_manifold(v) for k, v in meshes.items()}
    out = []
    for a, b in itertools.combinations(mans, 2):
        ba, bb = meshes[a].bounds, meshes[b].bounds
        if np.any(ba[1] < bb[0] - 0.01) or np.any(bb[1] < ba[0] - 0.01):
            continue
        v = (mans[a] ^ mans[b]).volume()
        if v > ignore:
            out.append((a, b, round(float(v), 3)))
    return out


def min_gap(ma: trimesh.Trimesh, mb: trimesh.Trimesh, n=6000):
    """Approximate minimum surface-to-surface distance between two meshes (mm)."""
    pts, _ = trimesh.sample.sample_surface(ma, n, seed=3)
    _, dist, _ = trimesh.proximity.closest_point(mb, pts)
    return float(dist.min())
