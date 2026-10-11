# smallPoolFire3D no ParaView (caso decomposto, processor*/):
#   pvbatch render_spf.py <caso.foam> <tempo> <saida_dir>          figuras
#   pvbatch render_spf.py <caso.foam> anim <saida_dir>/frames      quadros
# (1) isosuperfícies de T em 3D; (2) T no plano central com setas de U.
import os, sys
from paraview.simple import *

foam, modo, out = sys.argv[1], sys.argv[2], sys.argv[3]
os.makedirs(out, exist_ok=True)

r = OpenFOAMReader(FileName=foam)
r.CaseType = "Decomposed Case"
r.UpdatePipelineInformation()
r.Createcelltopointfiltereddata = 1
r.MeshRegions = ["internalMesh"]
r.CellArrays = ["T", "U"]
tempos = [t for t in r.TimestepValues if t > 0]
vol = MergeBlocks(Input=r)
vol.UpdatePipeline(tempos[-1])
_b = vol.GetDataInformation().GetBounds()
H = _b[3] - _b[2]                       # altura do domínio (y)

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

def escala():
    lutT.RescaleTransferFunction(300.0, 1600.0)

def barra(pos, comp=0.4):
    bar = GetScalarBar(lutT, view)
    bar.Title = "T [K]"
    bar.ComponentTitle = ""
    bar.TitleColor = bar.LabelColor = [0.1, 0.1, 0.1]
    bar.TitleFontSize = bar.LabelFontSize = 16
    bar.ScalarBarLength = comp
    bar.WindowLocation = "Any Location"
    bar.Position = pos
    bar.Visibility = 1

NIVEIS = ((400.0, 0.18), (700.0, 0.3), (1000.0, 0.45), (1300.0, 0.7), (1600.0, 1.0))

def isos_coloridas():
    """Isosuperfícies de T coloridas pela própria temperatura (Turbo)."""
    lut = GetColorTransferFunction("T")
    lut.ApplyPreset("Turbo", True)
    lut.AutomaticRescaleRangeMode = "Never"
    lut.RescaleTransferFunction(300.0, 1700.0)
    cs = []
    for valor, opac in NIVEIS:
        c = Contour(Input=vol)
        c.ContourBy = ["POINTS", "T"]
        c.Isosurfaces = [valor]
        c.ComputeScalars = 1
        # corte "em cebola": tira a metade voltada para a câmera
        k = Clip(Input=c)
        k.ClipType = "Plane"
        k.ClipType.Origin = [0.0, H / 2, 0.0]
        k.ClipType.Normal = [0.67, 0.0, 0.74]
        k.Invert = 1
        d = Show(k, view)
        ColorBy(d, ("POINTS", "T"))
        d.Specular = 0.3
        cs.append(k)
    lut.RescaleTransferFunction(300.0, 1700.0)
    barra([0.88, 0.3], 0.4)
    return cs

def plano(tamanho):
    """T no plano z = 0 com setas de velocidade."""
    lutT.ApplyPreset("Black-Body Radiation", True)
    if H > 1.5:                       # domínio alto: quadro em pé
        tamanho = [760, 1200]
    view.ViewSize = tamanho
    sl = Slice(Input=vol)
    sl.SliceType = "Plane"
    sl.SliceType.Origin = [0, H / 2, 0]
    sl.SliceType.Normal = [0, 0, 1]
    ds = Show(sl, view)
    ColorBy(ds, ("POINTS", "T"))
    escala()
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

if modo == "anim":
    plano([1100, 900])
    barra([0.87, 0.3], 0.4)
    txt = Text()
    dt = Show(txt, view)
    dt.Color = [0.1, 0.1, 0.1]
    dt.FontSize = 22
    dt.WindowLocation = "Upper Left Corner"
    view.ViewTime = tempos[-1]
    Render(view)
    view.ResetCamera()
    view.GetActiveCamera().Dolly(1.2)
    for i, t in enumerate(tempos):
        view.ViewTime = t
        txt.Text = f"t = {t:.1f} s".replace(".", ",")
        Render(view)
        SaveScreenshot(os.path.join(out, f"f{i:03d}.png"), view,
                       ImageResolution=list(view.ViewSize), TransparentBackground=0)
    print(f"ok anim {len(tempos)} quadros")
    sys.exit(0)

ALTO = H > 1.5
TAM3D = [900, 1200] if ALTO else None

if modo == "anim3d":
    view.ViewSize = TAM3D or [1100, 900]
    pool = OpenFOAMReader(FileName=foam)
    pool.CaseType = "Decomposed Case"
    pool.UpdatePipelineInformation()
    pool.MeshRegions = ["patch/inlet"]
    pd = Show(pool, view)
    pd.DiffuseColor = pd.AmbientColor = [0.2, 0.2, 0.25]
    ol = Show(Outline(Input=vol), view)
    ol.DiffuseColor = ol.AmbientColor = [0.6, 0.6, 0.6]
    isos_coloridas()
    txt = Text()
    dt = Show(txt, view)
    dt.Color = [0.1, 0.1, 0.1]
    dt.FontSize = 22
    dt.WindowLocation = "Upper Left Corner"
    nota = Text(Text="isosuperfícies de T: 400, 700, 1000, 1300 e 1600 K")
    dn = Show(nota, view)
    dn.Color = [0.15, 0.15, 0.15]
    dn.FontSize = 16
    dn.WindowLocation = "Lower Right Corner"
    view.ViewTime = tempos[-1]
    view.CameraFocalPoint = [0.0, H / 2, 0.0]
    view.CameraPosition = [1.6 * H, 1.1 * H, 1.8 * H]
    view.CameraViewUp = [0, 1, 0]
    Render(view)
    view.ResetCamera()
    cam = view.GetActiveCamera()
    cam.Dolly(1.0 if ALTO else 1.2)
    for i, t in enumerate(tempos):
        view.ViewTime = t
        txt.Text = f"t = {t:.1f} s".replace(".", ",")
        if i:
            cam.Azimuth(1.0)
        Render(view)
        SaveScreenshot(os.path.join(out, f"f{i:03d}.png"), view,
                       ImageResolution=list(view.ViewSize), TransparentBackground=0)
    print(f"ok anim3d {len(tempos)} quadros")
    sys.exit(0)

tempo = float(modo)
view.ViewTime = tempo
vol.UpdatePipeline(tempo)
print("T:", vol.PointData["T"].GetRange())

# ----------------------------------------------- 1) isosuperfícies de T
view.ViewSize = TAM3D or [1600, 900]
pool = OpenFOAMReader(FileName=foam)
pool.CaseType = "Decomposed Case"
pool.UpdatePipelineInformation()
pool.MeshRegions = ["patch/inlet"]
pd = Show(pool, view)
pd.DiffuseColor = pd.AmbientColor = [0.2, 0.2, 0.25]
ol = Show(Outline(Input=vol), view)
ol.DiffuseColor = ol.AmbientColor = [0.6, 0.6, 0.6]

isos = isos_coloridas()
nota = Text(Text="isosuperfícies de T: 400, 700, 1000, 1300 e 1600 K")
dn = Show(nota, view)
dn.Color = [0.15, 0.15, 0.15]
dn.FontSize = 18
dn.WindowLocation = "Lower Right Corner"

view.CameraFocalPoint = [0.0, 0.45 * H, 0.0]
view.CameraPosition = [1.05 * H, 0.85 * H, 1.2 * H]
view.CameraViewUp = [0, 1, 0]
view.CameraViewAngle = 30
Render(view)
if ALTO:
    view.ResetCamera()
view.GetActiveCamera().Dolly(1.05 if ALTO else 1.25)
Render(view)
SaveScreenshot(os.path.join(out, "poolfire_isosurfaces.png"), view,
               ImageResolution=list(view.ViewSize), TransparentBackground=0)
print("ok iso")

# --------------------------------- 2) plano central: T + setas de U
for c in isos:
    Hide(c, view)
for s_ in (pool, nota):
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
view.ViewTime = tempo
plano([1200, 1000])
barra([0.86, 0.3], 0.4)
Render(view)
SaveScreenshot(os.path.join(out, "poolfire_slice.png"), view,
               ImageResolution=list(view.ViewSize), TransparentBackground=0)
print("ok slice")
