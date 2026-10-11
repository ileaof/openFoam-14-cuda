# hotRoomComfort (ventilação e refrigeração) no ParaView:
#   pvbatch render_hvac.py <caso.foam> <tempo> <saida_dir> [orbita]
# (1) linhas de corrente do insuflamento coloridas por T, (2) T em cortes,
# (3) conforto PMV a 1,1 m; com "orbita", quadros de uma volta de 360 graus.
import os, sys
from paraview.simple import *

foam, tempo, out = sys.argv[1], float(sys.argv[2]), sys.argv[3]
orbita = len(sys.argv) > 4
os.makedirs(out, exist_ok=True)

r = OpenFOAMReader(FileName=foam)
r.UpdatePipelineInformation()
r.Createcelltopointfiltereddata = 1
r.MeshRegions = ["internalMesh"]
r.CellArrays = ["T", "U", "age", "PMV", "PPD", "DR"]
vol = MergeBlocks(Input=r)
vol.UpdatePipeline(tempo)
for f in ("T", "PMV", "PPD", "age", "DR"):
    print(f, [round(x, 3) for x in vol.PointData[f].GetRange()])
Umag = vol.PointData["U"].GetRange(-1)
print("|U|", [round(x, 3) for x in Umag])

def patch(nome):
    p = OpenFOAMReader(FileName=foam)
    p.UpdatePipelineInformation()
    p.MeshRegions = ["patch/" + nome]
    p.UpdatePipeline(tempo)
    return p

walls, inlet, outlet = patch("walls"), patch("inlet"), patch("outlet")

view = CreateView("RenderView")
view.ViewSize = [1100, 900] if orbita else [1600, 900]
view.Background = [1, 1, 1]
try:
    view.UseColorPaletteForBackground = 0
except AttributeError:
    pass
view.OrientationAxesVisibility = 0
view.ViewTime = tempo

lutT = GetColorTransferFunction("T")
lutT.ApplyPreset("Cool to Warm", True)
lutT.AutomaticRescaleRangeMode = "Never"

def barra(lut, titulo, pos=(0.9, 0.3)):
    bar = GetScalarBar(lut, view)
    bar.Title = titulo
    bar.ComponentTitle = ""
    bar.TitleColor = bar.LabelColor = [0.1, 0.1, 0.1]
    bar.TitleFontSize = bar.LabelFontSize = 16
    bar.ScalarBarLength = 0.4
    bar.WindowLocation = "Any Location"
    bar.Position = list(pos)
    bar.Visibility = 1

def sala():
    """Paredes translúcidas, grelhas de insuflamento (azul) e exaustão (cinza)."""
    dw = Show(walls, view)
    dw.DiffuseColor = dw.AmbientColor = [0.8, 0.8, 0.82]
    dw.Opacity = 0.12
    di = Show(inlet, view)
    di.DiffuseColor = di.AmbientColor = [0.1, 0.35, 0.95]
    do = Show(outlet, view)
    do.DiffuseColor = do.AmbientColor = [0.25, 0.25, 0.25]
    ol = Show(Outline(Input=vol), view)
    ol.DiffuseColor = ol.AmbientColor = [0.45, 0.45, 0.45]
    return dw

def camera_iso():
    view.CameraFocalPoint = [2.0, 1.5, 0.7]
    view.CameraPosition = [6.6, -3.2, 4.2]
    view.CameraViewUp = [0, 0, 1]
    view.CameraViewAngle = 30
    Render(view)
    view.ResetCamera()
    view.GetActiveCamera().Dolly(1.0 if orbita else 1.25)
    Render(view)

def salvar(nome):
    SaveScreenshot(os.path.join(out, nome), view, ImageResolution=list(view.ViewSize),
                   TransparentBackground=0)
    print("ok", nome)

# ---------------------------------- 1) linhas de corrente do insuflamento
sala()
st = StreamTracer(Input=vol, SeedType="Point Cloud")
st.Vectors = ["POINTS", "U"]
st.SeedType.Center = [0.03, 0.5, 1.2]
st.SeedType.Radius = 0.12
st.SeedType.NumberOfPoints = 120
st.MaximumStreamlineLength = 14.0
st.MaximumSteps = 60000
st.IntegrationDirection = "FORWARD"
st2 = StreamTracer(Input=vol, SeedType="Line")
st2.Vectors = ["POINTS", "U"]
st2.SeedType.Point1 = [0.3, 0.3, 0.8]
st2.SeedType.Point2 = [3.7, 2.7, 0.8]
st2.SeedType.Resolution = 24
st2.MaximumStreamlineLength = 14.0
st2.MaximumSteps = 60000
st2.IntegrationDirection = "BOTH"
tb = Tube(Input=ExtractSurface(Input=AppendDatasets(Input=[st, st2])))
tb.Radius = 0.006
dt = Show(tb, view)
ColorBy(dt, ("POINTS", "T"))
lutT.ApplyPreset("Turbo", True)
lutT.RescaleTransferFunction(294.0, 302.0)
barra(lutT, "T [K]", (0.88, 0.05) if orbita else (0.9, 0.3))
camera_iso()
if orbita:
    cam = view.GetActiveCamera()
    for i in range(72):
        Render(view)
        SaveScreenshot(os.path.join(out, f"f{i:03d}.png"), view,
                       ImageResolution=[1100, 900], TransparentBackground=0)
        cam.Azimuth(5.0)
    print("ok orbita 72 quadros")
    sys.exit(0)
salvar("hvac_streamlines.png")

# ---------------------------------------------- 2) temperatura em cortes
Hide(tb, view)
s1 = Slice(Input=vol)
s1.SliceType = "Plane"
s1.SliceType.Origin = [2.0, 0.5, 0.8]
s1.SliceType.Normal = [0, 1, 0]          # vertical, pelo jato de insuflamento
s2 = Slice(Input=vol)
s2.SliceType = "Plane"
s2.SliceType.Origin = [2.0, 1.5, 0.15]
s2.SliceType.Normal = [0, 0, 1]          # horizontal, perto do piso
for s in (s1, s2):
    d = Show(s, view)
    ColorBy(d, ("POINTS", "T"))
    d.Ambient, d.Diffuse = 0.35, 0.75
lutT.RescaleTransferFunction(294.0, 302.0)
notaT = Text(Text="cortes: vertical pelo jato de insuflamento e horizontal a 0,15 m do piso")
dnt = Show(notaT, view)
dnt.Color = [0.15, 0.15, 0.15]
dnt.FontSize = 18
dnt.WindowLocation = "Lower Right Corner"
camera_iso()
salvar("hvac_temperature.png")

# ------------------------------------------ 3) conforto térmico PMV a 1,1 m
for s in (s1, s2, notaT):
    Hide(s, view)
HideScalarBarIfNotNeeded(lutT, view)
GetScalarBar(lutT, view).Visibility = 0
s3 = Slice(Input=vol)
s3.SliceType = "Plane"
s3.SliceType.Origin = [2.0, 1.5, 1.1]
s3.SliceType.Normal = [0, 0, 1]
d3 = Show(s3, view)
ColorBy(d3, ("POINTS", "PMV"))
d3.Ambient, d3.Diffuse = 0.35, 0.75
lutP = GetColorTransferFunction("PMV")
lutP.ApplyPreset("Cool to Warm", True)
lutP.AutomaticRescaleRangeMode = "Never"
a, b = vol.PointData["PMV"].GetRange()
m = max(abs(a), abs(b), 0.5)
lutP.RescaleTransferFunction(-m, m)       # 0 = neutro no centro da escala
barra(lutP, "PMV a 1,1 m")
nota = Text(Text="PMV: -3 frio · 0 neutro · +3 quente (ISO 7730).  Sala ~ +1,4: ainda quente.")
dn = Show(nota, view)
dn.Color = [0.15, 0.15, 0.15]
dn.FontSize = 18
dn.WindowLocation = "Lower Right Corner"
camera_iso()
salvar("hvac_comfort.png")
