# hotRoomComfort (ventilation and cooling) in ParaView:
#   pvbatch render_hvac.py <case.foam> <time> <output_dir> [orbit]
# (1) supply-air streamlines colored by T, (2) T on cuts,
# (3) PMV comfort at 1.1 m; with "orbit", frames of a 360-degree turn.
import os, sys
from paraview.simple import *

foam, t_view, out = sys.argv[1], float(sys.argv[2]), sys.argv[3]
orbit = len(sys.argv) > 4
os.makedirs(out, exist_ok=True)

r = OpenFOAMReader(FileName=foam)
r.UpdatePipelineInformation()
r.Createcelltopointfiltereddata = 1
r.MeshRegions = ["internalMesh"]
r.CellArrays = ["T", "U", "age", "PMV", "PPD", "DR"]
vol = MergeBlocks(Input=r)
vol.UpdatePipeline(t_view)
for f in ("T", "PMV", "PPD", "age", "DR"):
    print(f, [round(x, 3) for x in vol.PointData[f].GetRange()])
Umag = vol.PointData["U"].GetRange(-1)
print("|U|", [round(x, 3) for x in Umag])

def patch(label):
    p = OpenFOAMReader(FileName=foam)
    p.UpdatePipelineInformation()
    p.MeshRegions = ["patch/" + label]
    p.UpdatePipeline(t_view)
    return p

walls, inlet, outlet = patch("walls"), patch("inlet"), patch("outlet")

view = CreateView("RenderView")
view.ViewSize = [1100, 900] if orbit else [1600, 900]
view.Background = [1, 1, 1]
try:
    view.UseColorPaletteForBackground = 0
except AttributeError:
    pass
view.OrientationAxesVisibility = 0
view.ViewTime = t_view

lutT = GetColorTransferFunction("T")
lutT.ApplyPreset("Cool to Warm", True)
lutT.AutomaticRescaleRangeMode = "Never"

def colorbar(lut, title, pos=(0.9, 0.3)):
    bar = GetScalarBar(lut, view)
    bar.Title = title
    bar.ComponentTitle = ""
    bar.TitleColor = bar.LabelColor = [0.1, 0.1, 0.1]
    bar.TitleFontSize = bar.LabelFontSize = 16
    bar.ScalarBarLength = 0.4
    bar.WindowLocation = "Any Location"
    bar.Position = list(pos)
    bar.Visibility = 1

def room():
    """Translucent walls, supply grille (blue) and exhaust grille (gray)."""
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

def iso_camera():
    view.CameraFocalPoint = [2.0, 1.5, 0.7]
    view.CameraPosition = [6.6, -3.2, 4.2]
    view.CameraViewUp = [0, 0, 1]
    view.CameraViewAngle = 30
    Render(view)
    view.ResetCamera()
    view.GetActiveCamera().Dolly(1.0 if orbit else 1.25)
    Render(view)

def save(label):
    SaveScreenshot(os.path.join(out, label), view, ImageResolution=list(view.ViewSize),
                   TransparentBackground=0)
    print("ok", label)

# ---------------------------------- 1) supply-air streamlines
room()
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
colorbar(lutT, "T [K]", (0.88, 0.05) if orbit else (0.9, 0.3))
iso_camera()
if orbit:
    cam = view.GetActiveCamera()
    for i in range(72):
        Render(view)
        SaveScreenshot(os.path.join(out, f"f{i:03d}.png"), view,
                       ImageResolution=[1100, 900], TransparentBackground=0)
        cam.Azimuth(5.0)
    print("ok orbit 72 frames")
    sys.exit(0)
save("hvac_streamlines.png")

# ---------------------------------------------- 2) temperature on cuts
Hide(tb, view)
s1 = Slice(Input=vol)
s1.SliceType = "Plane"
s1.SliceType.Origin = [2.0, 0.5, 0.8]
s1.SliceType.Normal = [0, 1, 0]          # vertical, through the supply jet
s2 = Slice(Input=vol)
s2.SliceType = "Plane"
s2.SliceType.Origin = [2.0, 1.5, 0.15]
s2.SliceType.Normal = [0, 0, 1]          # horizontal, near the floor
for s in (s1, s2):
    d = Show(s, view)
    ColorBy(d, ("POINTS", "T"))
    d.Ambient, d.Diffuse = 0.35, 0.75
lutT.RescaleTransferFunction(294.0, 302.0)
note_t = Text(Text="cuts: vertical through the supply jet and horizontal 0.15 m above the floor")
dnt = Show(note_t, view)
dnt.Color = [0.15, 0.15, 0.15]
dnt.FontSize = 18
dnt.WindowLocation = "Lower Right Corner"
iso_camera()
save("hvac_temperature.png")

# ------------------------------------------ 3) PMV thermal comfort at 1.1 m
for s in (s1, s2, note_t):
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
lutP.RescaleTransferFunction(-m, m)       # 0 = neutral at the middle of the scale
colorbar(lutP, "PMV at 1.1 m")
note = Text(Text="PMV: -3 cold · 0 neutral · +3 hot (ISO 7730).  Room ~ +1.4: still warm.")
dn = Show(note, view)
dn.Color = [0.15, 0.15, 0.15]
dn.FontSize = 18
dn.WindowLocation = "Lower Right Corner"
iso_camera()
save("hvac_comfort.png")
