"""Offscreen product renders with VTK (EGL). Studio lighting, soft floor shadow, SSAO."""
import math
import numpy as np
import vtk
from vtk.util.numpy_support import numpy_to_vtk, numpy_to_vtkIdTypeArray
from PIL import Image


def _polydata(m):
    pts = vtk.vtkPoints()
    pts.SetData(numpy_to_vtk(np.ascontiguousarray(m.vertices, dtype=np.float64), deep=True))
    f = np.asarray(m.faces, dtype=np.int64)
    cells = np.hstack([np.full((len(f), 1), 3, dtype=np.int64), f]).ravel()
    ca = vtk.vtkCellArray()
    ca.SetCells(len(f), numpy_to_vtkIdTypeArray(cells, deep=True))
    pd = vtk.vtkPolyData()
    pd.SetPoints(pts)
    pd.SetPolys(ca)
    nrm = vtk.vtkPolyDataNormals()
    nrm.SetInputData(pd)
    nrm.SetFeatureAngle(38)
    nrm.SplittingOn()
    nrm.ConsistencyOn()
    nrm.AutoOrientNormalsOff()
    nrm.Update()
    return nrm.GetOutput()


def baked_shadow(meshes, lo, hi, light=(0.45, 0.6, -1.0), res=1400, pad=0.9, strength=0.42):
    """Soft floor shadow + contact occlusion as an RGB texture, returned with its XY extent."""
    from PIL import ImageDraw, ImageFilter
    import fast_simplification
    span = (hi[:2] - lo[:2])
    c = (hi[:2] + lo[:2]) / 2
    half = max(span) * (0.5 + pad)
    x0, y0 = c - half
    size = 2 * half
    def canvas():
        return Image.new("L", (res, res), 0)
    def to_px(xy):
        return np.stack([(xy[:, 0] - x0) / size * res, (1 - (xy[:, 1] - y0) / size) * res], 1)
    L = np.array(light, float)
    L /= np.linalg.norm(L)
    z0 = lo[2]
    layers = {"dir": canvas(), "c1": canvas(), "c2": canvas(), "c3": canvas()}
    draws = {k: ImageDraw.Draw(v) for k, v in layers.items()}
    for m in meshes:
        v, f = np.asarray(m.vertices), np.asarray(m.faces)
        if len(f) > 30000:
            v, f = fast_simplification.simplify(v.astype(np.float32), f.astype(np.int32), target_count=30000)
        h = v[:, 2] - z0
        proj = v[:, :2] - (h / L[2])[:, None] * L[:2]
        pd = to_px(proj)
        pv = to_px(v[:, :2])
        tri_h = h[f].min(1)
        pdl, pvl = pd.tolist(), pv.tolist()
        for t, hh in zip(f.tolist(), tri_h.tolist()):
            draws["dir"].polygon([tuple(pdl[i]) for i in t], fill=255)
            q = [tuple(pvl[i]) for i in t]
            if hh < 40:
                draws["c1"].polygon(q, fill=255)
            if hh < 160:
                draws["c2"].polygon(q, fill=255)
            if hh < 450:
                draws["c3"].polygon(q, fill=255)
    px_per_mm = float(res / size)
    def blur(im, mm):
        return np.asarray(im.filter(ImageFilter.GaussianBlur(float(max(1.0, mm * px_per_mm)))), float) / 255
    sh = (0.55 * blur(layers["dir"], 28) + 0.55 * blur(layers["c1"], 6)
          + 0.35 * blur(layers["c2"], 22) + 0.22 * blur(layers["c3"], 60))
    sh = np.clip(sh, 0, 1) * strength
    return sh, (x0, y0, size)


MATERIALS = {
    # colour, diffuse, specular, specular power
    "black_pp": ((0.105, 0.105, 0.115), 0.85, 0.42, 22),
    "black_pla": ((0.07, 0.07, 0.08), 0.9, 0.45, 40),
    "white": ((0.93, 0.93, 0.94), 0.85, 0.25, 30),
    "white_pla": ((0.95, 0.95, 0.95), 0.85, 0.3, 40),
    "alu": ((0.66, 0.67, 0.69), 0.75, 0.6, 60),
    "ghost": ((0.55, 0.62, 0.72), 0.9, 0.1, 10),
    "person": ((0.62, 0.74, 0.90), 0.85, 0.15, 12),
}


def render(items, out, view=(-1.0, -1.25, 0.72), target=None, up=(0, 0, 1), size=(1800, 1200),
           ortho=False, zoom=1.0, floor=True, bg=((0.97, 0.97, 0.975), (0.86, 0.86, 0.875)),
           ssao=True, shadows=False, fov=24, supersample=2, extra=None, bg_flat=None):
    """items: list of (trimesh, material_name or (rgb, diff, spec, power), opacity)."""
    W, H = size[0] * supersample, size[1] * supersample
    ren = vtk.vtkRenderer()
    rw = vtk.vtkRenderWindow()
    rw.SetOffScreenRendering(1)
    rw.SetSize(W, H)
    rw.AddRenderer(ren)
    if bg_flat is None:
        ren.GradientBackgroundOn()
        ren.SetBackground(*bg[1])
        ren.SetBackground2(*bg[0])
    else:
        ren.SetBackground(*bg_flat)

    allpts = []
    for it in items:
        m, mat = it[0], it[1]
        op = it[2] if len(it) > 2 else 1.0
        col, dif, spec, pw = MATERIALS[mat] if isinstance(mat, str) else mat
        mp = vtk.vtkPolyDataMapper()
        mp.SetInputData(_polydata(m))
        a = vtk.vtkActor()
        a.SetMapper(mp)
        p = a.GetProperty()
        p.SetColor(*col)
        p.SetDiffuse(dif)
        p.SetSpecular(spec)
        p.SetSpecularPower(pw)
        p.SetAmbient(0.12)
        p.SetOpacity(op)
        p.SetInterpolationToPhong()
        ren.AddActor(a)
        allpts.append(np.asarray(m.bounds))
    b = np.array(allpts)
    lo, hi = b[:, 0, :].min(0), b[:, 1, :].max(0)
    ctr = (lo + hi) / 2 if target is None else np.array(target, float)
    diag = float(np.linalg.norm(hi - lo))

    if floor:
        z0 = lo[2] - 0.0005 * diag
        floor_rgb = np.array(bg_flat if bg_flat is not None else bg[1])
        sh, (fx0, fy0, fsize) = baked_shadow([it[0] for it in items], lo, hi)
        tex = (floor_rgb[None, None, :] * (1 - sh[:, :, None]) * 255).astype(np.uint8)
        img = vtk.vtkImageData()
        img.SetDimensions(tex.shape[1], tex.shape[0], 1)
        arr = numpy_to_vtk(np.ascontiguousarray(tex[::-1].reshape(-1, 3)), deep=True,
                           array_type=vtk.VTK_UNSIGNED_CHAR)
        arr.SetNumberOfComponents(3)
        img.GetPointData().SetScalars(arr)
        vt = vtk.vtkTexture()
        vt.SetInputData(img)
        vt.InterpolateOn()
        pl = vtk.vtkPlaneSource()
        pl.SetOrigin(fx0, fy0, z0)
        pl.SetPoint1(fx0 + fsize, fy0, z0)
        pl.SetPoint2(fx0, fy0 + fsize, z0)
        fm = vtk.vtkPolyDataMapper()
        fm.SetInputConnection(pl.GetOutputPort())
        fa = vtk.vtkActor()
        fa.SetMapper(fm)
        fa.SetTexture(vt)
        fa.GetProperty().LightingOff()
        ren.AddActor(fa)
        # seamless: infinite floor beyond the texture in the flat background colour
        big = vtk.vtkPlaneSource()
        R = diag * 60
        big.SetOrigin(ctr[0] - R, ctr[1] - R, z0 - 0.3)
        big.SetPoint1(ctr[0] + R, ctr[1] - R, z0 - 0.3)
        big.SetPoint2(ctr[0] - R, ctr[1] + R, z0 - 0.3)
        bm = vtk.vtkPolyDataMapper()
        bm.SetInputConnection(big.GetOutputPort())
        ba = vtk.vtkActor()
        ba.SetMapper(bm)
        ba.GetProperty().LightingOff()
        ba.GetProperty().SetColor(*floor_rgb)
        ren.AddActor(ba)
        shadows = False

    if extra:
        for a in extra(ren):
            ren.AddActor(a)

    cam = ren.GetActiveCamera()
    v = np.array(view, float)
    v /= np.linalg.norm(v)
    dist = diag * 2.4 / zoom
    cam.SetFocalPoint(*ctr)
    cam.SetPosition(*(ctr + v * dist))
    cam.SetViewUp(*up)
    cam.SetViewAngle(fov)
    if ortho:
        cam.ParallelProjectionOn()
        cam.SetParallelScale(diag * 0.36 / zoom)
    ren.ResetCameraClippingRange()

    # lights: key, fill, rim
    ren.RemoveAllLights()
    def light(pos, inten, col=(1, 1, 1)):
        L = vtk.vtkLight()
        L.SetPositional(False)
        L.SetFocalPoint(*ctr)
        L.SetPosition(*(ctr + np.array(pos, float) * diag * 3))
        L.SetIntensity(inten)
        L.SetColor(*col)
        ren.AddLight(L)
        return L
    light((-0.6, -1.0, 1.5), 0.95)
    light((1.2, -0.4, 0.5), 0.35, (0.95, 0.97, 1.0))
    light((0.4, 1.2, 0.9), 0.45)
    light((0.0, 0.0, 1.0), 0.25)

    try:
        passes = vtk.vtkRenderStepsPass()
        seq = passes
        if shadows:
            sh = vtk.vtkShadowMapPass()
            sh.GetShadowMapBakerPass().SetResolution(4096)
            op_ = vtk.vtkSequencePass()
            col = vtk.vtkRenderPassCollection()
            col.AddItem(sh.GetShadowMapBakerPass())
            col.AddItem(sh)
            op_.SetPasses(col)
            cam_pass = vtk.vtkCameraPass()
            cam_pass.SetDelegatePass(op_)
            seq = cam_pass
        if ssao:
            ao = vtk.vtkSSAOPass()
            ao.SetRadius(diag * 0.02)
            ao.SetBias(diag * 0.0008)
            ao.SetKernelSize(128)
            ao.BlurOn()
            ao.SetDelegatePass(seq)
            ren.SetPass(ao)
        elif shadows:
            ren.SetPass(seq)
    except Exception:
        pass

    rw.SetMultiSamples(0)
    rw.Render()
    w2i = vtk.vtkWindowToImageFilter()
    w2i.SetInput(rw)
    w2i.SetInputBufferTypeToRGB()
    w2i.ReadFrontBufferOff()
    w2i.Update()
    img = w2i.GetOutput()
    dims = img.GetDimensions()
    from vtk.util.numpy_support import vtk_to_numpy
    arr = vtk_to_numpy(img.GetPointData().GetScalars()).reshape(dims[1], dims[0], -1)[::-1]
    im = Image.fromarray(arr.astype(np.uint8))
    if supersample > 1:
        im = im.resize(size, Image.LANCZOS)
    im.save(out)
    info = dict(ctr=ctr, scale=(diag * 0.36 / zoom) if ortho else None, size=size,
                right=np.cross(-v, np.array(up, float)) / np.linalg.norm(np.cross(-v, np.array(up, float))),
                up=np.array(up, float))
    return info
