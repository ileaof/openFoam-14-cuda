# Figuras do motorBike usadas no README e em cuda/docs.
#   pvbatch render_motorbike.py <caso>/mb.foam-dir <tempo> <saida_dir>
# <caso>: caso decomposto (processor*/) do tutorial
# incompressibleFluid/motorBike; testado com ParaView 6.0.1.
# Figuras do motorBike: (1) moto colorida por p + tubos de corrente por |U|,
# (2) corte no plano de simetria colorido por |U|.
import os, sys
from paraview.simple import *

case, tempo, out = sys.argv[1], float(sys.argv[2]), sys.argv[3]
foam = os.path.join(case, "mb.foam")
open(foam, "a").close()

r = OpenFOAMReader(FileName=foam)
r.CaseType = "Decomposed Case"
r.UpdatePipelineInformation()      # antes de escolher regiões/campos
r.Createcelltopointfiltereddata = 1
r.MeshRegions = ["internalMesh"]
r.CellArrays = ["p", "U"]
regs = list(r.GetProperty("MeshRegions").Available)
bike = [x for x in regs if "motorBike" in x and x.startswith("patch/")] \
    or [x for x in regs if "motorBike" in x]
print("regioes da moto:", len(bike), bike[:3])
r.UpdatePipeline(tempo)

vol = MergeBlocks(Input=r)
vol.UpdatePipeline(tempo)
surf = OpenFOAMReader(FileName=foam)
surf.CaseType = "Decomposed Case"
surf.UpdatePipelineInformation()
surf.Createcelltopointfiltereddata = 1
surf.MeshRegions = bike
surf.CellArrays = ["p", "U"]
surf.UpdatePipeline(tempo)
bikeS = MergeBlocks(Input=surf)
bikeS.UpdatePipeline(tempo)
b = bikeS.GetDataInformation().GetBounds()
print("bounds da moto:", [round(x, 3) for x in b])
cx, cy, cz = (b[0] + b[1]) / 2, (b[2] + b[3]) / 2, (b[4] + b[5]) / 2
L = b[1] - b[0]

view = CreateView("RenderView")
view.ViewSize = [1600, 900]
view.Background = [1, 1, 1]
view.OrientationAxesVisibility = 0
try:
    view.UseColorPaletteForBackground = 0
except AttributeError:
    pass
view.ViewTime = tempo

def barra(lut, titulo, view):
    bar = GetScalarBar(lut, view)
    bar.Title = titulo
    bar.ComponentTitle = ""
    bar.TitleColor = bar.LabelColor = [0.1, 0.1, 0.1]
    bar.TitleFontSize = bar.LabelFontSize = 16
    bar.ScalarBarLength = 0.35
    bar.Visibility = 1
    return bar

# ------------------------------------------------ 1) moto + tubos de corrente
dm = Show(bikeS, view)
ColorBy(dm, ("POINTS", "p"))
lutP = GetColorTransferFunction("p")
lutP.ApplyPreset("Cool to Warm", True)
lutP.AutomaticRescaleRangeMode = "Never"
lutP.RescaleTransferFunction(-600.0, 200.0)
barra(lutP, "p [m²/s²]", view).WindowLocation = "Any Location"
GetScalarBar(lutP, view).Position = [0.90, 0.55]

H = b[5] - b[4]
st = StreamTracer(Input=vol, SeedType="Point Cloud")
st.Vectors = ["POINTS", "U"]
st.SeedType.Center = [b[0] - 0.15 * L, cy, b[4] + 0.5 * H]
st.SeedType.Radius = 0.5 * H
st.SeedType.NumberOfPoints = 500
st.MaximumStreamlineLength = 2.2 * L
st.IntegrationDirection = "FORWARD"
# só a metade de trás (y > centro): a moto fica na frente das linhas
cl = Clip(Input=st)
cl.ClipType = "Plane"
cl.ClipType.Origin = [cx, cy, cz]
cl.ClipType.Normal = [0, 1, 0]
cl.Invert = 0
tb = Tube(Input=ExtractSurface(Input=cl))
tb.Radius = 0.0025 * L
dt = Show(tb, view)
ColorBy(dt, ("POINTS", "U", "Magnitude"))
lutU = GetColorTransferFunction("U")
lutU.ApplyPreset("Viridis (matplotlib)", True)
lutU.AutomaticRescaleRangeMode = "Never"
lutU.RescaleTransferFunction(0.0, 25.0)
barra(lutU, "|U| [m/s]", view).WindowLocation = "Any Location"
GetScalarBar(lutU, view).Position = [0.90, 0.08]

view.CameraFocalPoint = [cx + 0.3 * L, cy, b[4] + 0.45 * H]
view.CameraPosition = [cx - 0.55 * L, cy - 1.05 * L, b[4] + 1.0 * H]
view.CameraViewUp = [0, 0, 1]
Render(view)
view.GetActiveCamera().Dolly(1.9)
Render(view)
SaveScreenshot(os.path.join(out, "motorbike_streamlines.png"), view,
               ImageResolution=[1600, 900], TransparentBackground=0)
print("ok streamlines")

# ------------------------------------------- 2) corte no plano de simetria
Hide(tb, view)
HideScalarBarIfNotNeeded(lutU, view)
sl = Slice(Input=vol)
sl.SliceType = "Plane"
sl.SliceType.Origin = [cx, cy, cz]
sl.SliceType.Normal = [0, 1, 0]
ds = Show(sl, view)
ColorBy(ds, ("POINTS", "U", "Magnitude"))
lutU.RescaleTransferFunction(0.0, 25.0)
barra(lutU, "|U| [m/s]", view).WindowLocation = "Any Location"
GetScalarBar(lutU, view).Position = [0.92, 0.55]
ColorBy(dm, None)
dm.DiffuseColor = dm.AmbientColor = [0.75, 0.75, 0.75]
HideScalarBarIfNotNeeded(lutP, view)
GetScalarBar(lutP, view).Visibility = 0

view.CameraViewAngle = 30
view.CameraFocalPoint = [cx + 0.45 * L, cy, b[4] + 1.2 * H]
view.CameraPosition = [cx + 0.45 * L, cy - 3.0 * L, b[4] + 1.2 * H]
view.CameraViewUp = [0, 0, 1]
view.CameraParallelProjection = 0
Render(view)
SaveScreenshot(os.path.join(out, "motorbike_wake.png"), view,
               ImageResolution=[1600, 900], TransparentBackground=0)
print("ok wake")
