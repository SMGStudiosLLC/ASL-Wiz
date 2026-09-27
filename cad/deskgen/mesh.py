"""Tessellation and fast mesh booleans (manifold3d) for the output files."""
import numpy as np
import trimesh
import manifold3d as mf


def to_trimesh(solid, tol=0.2, ang=0.2):
    verts, tris = solid.tessellate(tol, ang)
    v = np.array([[p.x, p.y, p.z] for p in verts], dtype=np.float64)
    f = np.array(tris, dtype=np.int64)
    m = trimesh.Trimesh(v, f, process=True)
    m.merge_vertices()
    if not m.is_watertight:
        # tiny end-cap faces can tessellate with a mismatched edge; drop and re-close them
        m.update_faces(m.nondegenerate_faces())
        m.remove_unreferenced_vertices()
        m.merge_vertices(digits_vertex=5)
        trimesh.repair.fill_holes(m)
        trimesh.repair.fix_normals(m)
    return m


def to_manifold(m: trimesh.Trimesh):
    mesh = mf.Mesh(vert_properties=np.asarray(m.vertices, dtype=np.float32),
                   tri_verts=np.asarray(m.faces, dtype=np.uint32))
    man = mf.Manifold(mesh)
    if man.status() != mf.Error.NoError:
        raise RuntimeError(f"not manifold: {man.status()}")
    return man


def from_manifold(man) -> trimesh.Trimesh:
    out = man.to_mesh()
    return trimesh.Trimesh(np.asarray(out.vert_properties)[:, :3], np.asarray(out.tri_verts), process=True)


def combine(add, sub=(), tol=0.2, ang=0.2):
    """Union of B-rep solids in `add`, minus solids in `sub`, via manifold3d. Returns trimesh."""
    mans = [to_manifold(to_trimesh(s, tol, ang)) for s in add]
    res = mf.Manifold.batch_boolean(mans, mf.OpType.Add) if len(mans) > 1 else mans[0]
    if sub:
        cut = [to_manifold(to_trimesh(s, tol, ang)) for s in sub]
        cutter = mf.Manifold.batch_boolean(cut, mf.OpType.Add) if len(cut) > 1 else cut[0]
        res = res - cutter
    return from_manifold(res)
