"""Exporters: STL/3MF (print), GLB + USDZ (view / iPhone AR), DAE (SketchUp), STEP (CAD)."""
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


def export_dae(named, path, max_faces=None):
    """Collada for SketchUp (File > Import): millimetres, Z-up, one named, coloured node per part.
    max_faces: {name: triangle budget}; parts over budget are decimated (SketchUp slows down on
    very dense meshes, and the grip texture is kept by the budget on the seat shell)."""
    import collada
    from collada import material, source, geometry, scene as cscene
    max_faces = max_faces or {}
    mesh = collada.Collada()
    mesh.assetInfo.unitname = "millimeter"
    mesh.assetInfo.unitmeter = 0.001
    mesh.assetInfo.upaxis = collada.asset.UP_AXIS.Z_UP
    nodes = []
    for name, m, rgb in named:
        budget = max_faces.get(name)
        if budget and len(m.faces) > budget:
            import fast_simplification
            v, f = fast_simplification.simplify(np.asarray(m.vertices, np.float32), np.asarray(m.faces),
                                                target_reduction=1.0 - budget / len(m.faces))
            m = trimesh.Trimesh(v, f, process=True)
        eff = material.Effect(f"{name}_fx", [], "lambert", diffuse=(*rgb, 1.0))
        mat = material.Material(f"{name}_mat", f"{name}_mat", eff)
        mesh.effects.append(eff)
        mesh.materials.append(mat)
        vsrc = source.FloatSource(f"{name}_v", np.asarray(m.vertices, float).ravel(), ("X", "Y", "Z"))
        nsrc = source.FloatSource(f"{name}_n", np.asarray(m.face_normals, float).ravel(), ("X", "Y", "Z"))
        geom = geometry.Geometry(mesh, f"{name}_geom", name, [vsrc, nsrc])
        il = source.InputList()
        il.addInput(0, "VERTEX", f"#{name}_v")
        il.addInput(1, "NORMAL", f"#{name}_n")
        fi = np.asarray(m.faces)
        ni = np.repeat(np.arange(len(fi))[:, None], 3, axis=1)
        idx = np.stack([fi, ni], axis=2).ravel()
        geom.primitives.append(geom.createTriangleSet(idx, il, f"{name}_matref"))
        mesh.geometries.append(geom)
        matnode = cscene.MaterialNode(f"{name}_matref", mat, inputs=[])
        nodes.append(cscene.Node(name, children=[cscene.GeometryNode(geom, [matnode])]))
    root = cscene.Node("DELTA_chair_desk", children=nodes)
    sc = cscene.Scene("scene", [root])
    mesh.scenes.append(sc)
    mesh.scene = sc
    mesh.write(path)


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
    Usd.ModelAPI(root.GetPrim()).SetKind("component")
    allv = np.concatenate([np.asarray(m.vertices) for _, m, _ in named])
    centre = (allv.min(0) + allv.max(0)) / 2
    centre[2] = 0.0                                         # keep the floor at zero
    for name, m, rgb in named:
        v = (np.asarray(m.vertices) - centre) * 0.001
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
