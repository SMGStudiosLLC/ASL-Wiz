"""Exporters: STL/3MF (print), GLB + USDZ (view / iPhone AR), STEP (CAD)."""
import os
import numpy as np
import trimesh


def export_stl(m, path):
    m.export(path)


def export_glb(named, path):
    """named: list of (name, mesh, rgb 0..1). Metres, Y-up (glTF convention)."""
    scene = trimesh.Scene()
    for name, m, rgb in named:
        mm = m.copy()
        mm.apply_scale(0.001)
        mm.apply_transform(trimesh.transformations.rotation_matrix(-np.pi / 2, [1, 0, 0]))
        mat = trimesh.visual.material.PBRMaterial(
            baseColorFactor=[*rgb, 1.0], metallicFactor=0.0 if rgb[0] < 0.5 or rgb[0] > 0.9 else 0.6,
            roughnessFactor=0.55)
        mm.visual = trimesh.visual.TextureVisuals(material=mat)
        scene.add_geometry(mm, node_name=name, geom_name=name)
    scene.export(path)


def export_usdz(named, path, metallic=None):
    """USDZ for iPhone/iPad Quick Look AR. Real scale (metres), Y-up."""
    from pxr import Usd, UsdGeom, UsdShade, Sdf, Gf, UsdUtils
    metallic = metallic or {}
    tmp = path.replace(".usdz", ".usdc")
    stage = Usd.Stage.CreateNew(tmp)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)
    UsdGeom.SetStageMetersPerUnit(stage, 1.0)
    root = UsdGeom.Xform.Define(stage, "/DELTA")
    stage.SetDefaultPrim(root.GetPrim())
    for name, m, rgb in named:
        v = np.asarray(m.vertices) * 0.001
        v = np.stack([v[:, 0], v[:, 2], -v[:, 1]], 1)        # Z-up mm -> Y-up m
        mesh = UsdGeom.Mesh.Define(stage, f"/DELTA/{name}")
        mesh.CreatePointsAttr([Gf.Vec3f(*p) for p in v])
        mesh.CreateFaceVertexCountsAttr([3] * len(m.faces))
        mesh.CreateFaceVertexIndicesAttr(np.asarray(m.faces).ravel().tolist())
        mesh.CreateSubdivisionSchemeAttr("none")
        n = m.vertex_normals
        n = np.stack([n[:, 0], n[:, 2], -n[:, 1]], 1)
        mesh.CreateNormalsAttr([Gf.Vec3f(*p) for p in n])
        mesh.SetNormalsInterpolation("vertex")
        mat = UsdShade.Material.Define(stage, f"/DELTA/{name}_mat")
        sh = UsdShade.Shader.Define(stage, f"/DELTA/{name}_mat/pbr")
        sh.CreateIdAttr("UsdPreviewSurface")
        sh.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(*rgb))
        sh.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(0.5)
        sh.CreateInput("metallic", Sdf.ValueTypeNames.Float).Set(float(metallic.get(name, 0.0)))
        mat.CreateSurfaceOutput().ConnectToSource(sh.ConnectableAPI(), "surface")
        UsdShade.MaterialBindingAPI.Apply(mesh.GetPrim()).Bind(mat)
    stage.GetRootLayer().Save()
    UsdUtils.CreateNewARKitUsdzPackage(tmp, path)
    os.remove(tmp)


def export_step(named_solids, path):
    """named_solids: list of (name, cq.Shape, rgb). Coloured STEP assembly."""
    import cadquery as cq
    asm = cq.Assembly(name="DELTA_chair_desk")
    for name, s, rgb in named_solids:
        asm.add(s, name=name, color=cq.Color(*rgb, 1.0))
    asm.save(path, exportType="STEP")
