# smallPoolFire3D in ParaView (decomposed case, processor*/):
#   pvbatch render_poolfire.py <case.foam> <time> <output_dir>          figures
#   pvbatch render_poolfire.py <case.foam> anim <output_dir>/frames     2D animation frames
#   pvbatch render_poolfire.py <case.foam> anim3d <output_dir>/frames   3D animation frames
# (1) T isosurfaces in 3D; (2) T on the mid-plane with U arrows.
import os, sys
from paraview.simple import *

foam, mode, out = sys.argv[1], sys.argv[2], sys.argv[3]
os.makedirs(out, exist_ok=True)

r = OpenFOAMReader(FileName=foam)
r.CaseType = "Decomposed Case"
r.UpdatePipelineInformation()
r.Createcelltopointfiltereddata = 1
r.MeshRegions = ["internalMesh"]
r.CellArrays = ["T", "U"]
times = [t for t in r.TimestepValues if t > 0]
vol = MergeBlocks(Input=r)
vol.UpdatePipeline(times[-1])
_b = vol.GetDataInformation().GetBounds()
H = _b[3] - _b[2]                       # domain height (y)

view = CreateView("RenderView")
view.Background = [1, 1, 1]
try:
    view.UseColorPaletteForBackground = 0
except AttributeError:
    pass
view.OrientationAxesVisibility = 0

lutT = GetColorTransferFunction("T")
lutT.ApplyPreset("Black-Body Radiation", True)
lutT.AutomaticRescaleRangeMode = "Never"

def rescale_t():
    lutT.RescaleTransferFunction(300.0, 1600.0)

def colorbar(pos, comp=0.4):
    bar = GetScalarBar(lutT, view)
    bar.Title = "T [K]"
    bar.ComponentTitle = ""
    bar.TitleColor = bar.LabelColor = [0.1, 0.1, 0.1]
    bar.TitleFontSize = bar.LabelFontSize = 16
    bar.ScalarBarLength = comp
    bar.WindowLocation = "Any Location"
    bar.Position = pos
    bar.Visibility = 1

LEVELS = ((400.0, 0.18), (700.0, 0.3), (1000.0, 0.45), (1300.0, 0.7), (1600.0, 1.0))

def colored_isosurfaces():
    """T isosurfaces colored by the temperature itself (Turbo)."""
    lut = GetColorTransferFunction("T")
    lut.ApplyPreset("Turbo", True)
    lut.AutomaticRescaleRangeMode = "Never"
    lut.RescaleTransferFunction(300.0, 1700.0)
    contours = []
    for value, opacity in LEVELS:
        c = Contour(Input=vol)
        c.ContourBy = ["POINTS", "T"]
        c.Isosurfaces = [value]
        c.ComputeScalars = 1
        # "onion" cut: removes the half facing the camera
        k = Clip(Input=c)
        k.ClipType = "Plane"
        k.ClipType.Origin = [0.0, H / 2, 0.0]
        k.ClipType.Normal = [0.67, 0.0, 0.74]
        k.Invert = 1
        d = Show(k, view)
        ColorBy(d, ("POINTS", "T"))
        d.Specular = 0.3
        contours.append(k)
    lut.RescaleTransferFunction(300.0, 1700.0)
    colorbar([0.88, 0.3], 0.4)
    return contours

def mid_plane(size):
    """T on the z = 0 plane with velocity arrows."""
    lutT.ApplyPreset("Black-Body Radiation", True)
    if H > 1.5:                       # tall domain: portrait frame
        size = [760, 1200]
    view.ViewSize = size
    sl = Slice(Input=vol)
    sl.SliceType = "Plane"
    sl.SliceType.Origin = [0, H / 2, 0]
    sl.SliceType.Normal = [0, 0, 1]
    ds = Show(sl, view)
    ColorBy(ds, ("POINTS", "T"))
    rescale_t()
    gl = Glyph(Input=sl, GlyphType="Arrow")
    gl.OrientationArray = ["POINTS", "U"]
    gl.ScaleArray = ["POINTS", "No scale array"]
    gl.ScaleFactor = 0.03 * max(1.0, H / 2)
    gl.GlyphMode = "Every Nth Point"
    gl.Stride = 37
    dg = Show(gl, view)
    ColorBy(dg, None)
    dg.DiffuseColor = dg.AmbientColor = [0.85, 0.9, 1.0]
    view.CameraFocalPoint = [0.07 * H, H / 2, 0.0]
    view.CameraPosition = [0.07 * H, H / 2, 2.05 * H]
    view.CameraViewUp = [0, 1, 0]
    view.CameraViewAngle = 30
    return sl, gl

if mode == "anim":
    mid_plane([1100, 900])
    colorbar([0.87, 0.3], 0.4)
    txt = Text()
    dt = Show(txt, view)
    dt.Color = [0.1, 0.1, 0.1]
    dt.FontSize = 22
    dt.WindowLocation = "Upper Left Corner"
    view.ViewTime = times[-1]
    Render(view)
    view.ResetCamera()
    view.GetActiveCamera().Dolly(1.2)
    for i, t in enumerate(times):
        view.ViewTime = t
        txt.Text = f"t = {t:.1f} s"
        Render(view)
        SaveScreenshot(os.path.join(out, f"f{i:03d}.png"), view,
                       ImageResolution=list(view.ViewSize), TransparentBackground=0)
    print(f"ok anim {len(times)} frames")
    sys.exit(0)

TALL = H > 1.5
SIZE3D = [900, 1200] if TALL else None

if mode == "anim3d":
    view.ViewSize = SIZE3D or [1100, 900]
    pool = OpenFOAMReader(FileName=foam)
    pool.CaseType = "Decomposed Case"
    pool.UpdatePipelineInformation()
    pool.MeshRegions = ["patch/inlet"]
    pd = Show(pool, view)
    pd.DiffuseColor = pd.AmbientColor = [0.2, 0.2, 0.25]
    ol = Show(Outline(Input=vol), view)
    ol.DiffuseColor = ol.AmbientColor = [0.6, 0.6, 0.6]
    colored_isosurfaces()
    txt = Text()
    dt = Show(txt, view)
    dt.Color = [0.1, 0.1, 0.1]
    dt.FontSize = 22
    dt.WindowLocation = "Upper Left Corner"
    note = Text(Text="temperature isosurfaces: 400, 700, 1000, 1300 and 1600 K")
    dn = Show(note, view)
    dn.Color = [0.15, 0.15, 0.15]
    dn.FontSize = 16
    dn.WindowLocation = "Lower Right Corner"
    view.ViewTime = times[-1]
    view.CameraFocalPoint = [0.0, H / 2, 0.0]
    view.CameraPosition = [1.6 * H, 1.1 * H, 1.8 * H]
    view.CameraViewUp = [0, 1, 0]
    Render(view)
    view.ResetCamera()
    cam = view.GetActiveCamera()
    cam.Dolly(1.0 if TALL else 1.2)
    for i, t in enumerate(times):
        view.ViewTime = t
        txt.Text = f"t = {t:.1f} s"
        if i:
            cam.Azimuth(1.0)
        Render(view)
        SaveScreenshot(os.path.join(out, f"f{i:03d}.png"), view,
                       ImageResolution=list(view.ViewSize), TransparentBackground=0)
    print(f"ok anim3d {len(times)} frames")
    sys.exit(0)

t_view = float(mode)
view.ViewTime = t_view
vol.UpdatePipeline(t_view)
print("T:", vol.PointData["T"].GetRange())

# ----------------------------------------------- 1) T isosurfaces
view.ViewSize = SIZE3D or [1600, 900]
pool = OpenFOAMReader(FileName=foam)
pool.CaseType = "Decomposed Case"
pool.UpdatePipelineInformation()
pool.MeshRegions = ["patch/inlet"]
pd = Show(pool, view)
pd.DiffuseColor = pd.AmbientColor = [0.2, 0.2, 0.25]
ol = Show(Outline(Input=vol), view)
ol.DiffuseColor = ol.AmbientColor = [0.6, 0.6, 0.6]

isos = colored_isosurfaces()
note = Text(Text="temperature isosurfaces: 400, 700, 1000, 1300 and 1600 K")
dn = Show(note, view)
dn.Color = [0.15, 0.15, 0.15]
dn.FontSize = 18
dn.WindowLocation = "Lower Right Corner"

view.CameraFocalPoint = [0.0, 0.45 * H, 0.0]
view.CameraPosition = [1.05 * H, 0.85 * H, 1.2 * H]
view.CameraViewUp = [0, 1, 0]
view.CameraViewAngle = 30
Render(view)
if TALL:
    view.ResetCamera()
view.GetActiveCamera().Dolly(1.05 if TALL else 1.25)
Render(view)
SaveScreenshot(os.path.join(out, "poolfire_isosurfaces.png"), view,
               ImageResolution=list(view.ViewSize), TransparentBackground=0)
print("ok iso")

# --------------------------------- 2) mid-plane: T + U arrows
for c in isos:
    Hide(c, view)
for s_ in (pool, note):
    Hide(s_, view)
Hide(FindSource("Outline1") or Outline(Input=vol), view)
Delete(view)
view = CreateView("RenderView")
view.Background = [1, 1, 1]
try:
    view.UseColorPaletteForBackground = 0
except AttributeError:
    pass
view.OrientationAxesVisibility = 0
view.ViewTime = t_view
mid_plane([1200, 1000])
colorbar([0.86, 0.3], 0.4)
Render(view)
SaveScreenshot(os.path.join(out, "poolfire_slice.png"), view,
               ImageResolution=list(view.ViewSize), TransparentBackground=0)
print("ok slice")
