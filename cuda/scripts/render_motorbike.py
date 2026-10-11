# motorBike figures used in the README and in cuda/docs.
#   pvbatch render_motorbike.py <case>/mb.foam <time> <output_dir>
# <case>: decomposed case (processor*/) of the incompressibleFluid/motorBike
# tutorial; tested with ParaView 6.0.1.
# (1) bike colored by p + streamtubes colored by |U|,
# (2) symmetry-plane cut colored by |U|.
import os, sys
from paraview.simple import *

case, t_view, out = sys.argv[1], float(sys.argv[2]), sys.argv[3]
foam = os.path.join(case, "mb.foam")
open(foam, "a").close()

r = OpenFOAMReader(FileName=foam)
r.CaseType = "Decomposed Case"
r.UpdatePipelineInformation()      # before choosing regions/fields
r.Createcelltopointfiltereddata = 1
r.MeshRegions = ["internalMesh"]
r.CellArrays = ["p", "U"]
regs = list(r.GetProperty("MeshRegions").Available)
bike = [x for x in regs if "motorBike" in x and x.startswith("patch/")] \
    or [x for x in regs if "motorBike" in x]
print("bike regions:", len(bike), bike[:3])
r.UpdatePipeline(t_view)

vol = MergeBlocks(Input=r)
vol.UpdatePipeline(t_view)
surf = OpenFOAMReader(FileName=foam)
surf.CaseType = "Decomposed Case"
surf.UpdatePipelineInformation()
surf.Createcelltopointfiltereddata = 1
surf.MeshRegions = bike
surf.CellArrays = ["p", "U"]
surf.UpdatePipeline(t_view)
bikeS = MergeBlocks(Input=surf)
bikeS.UpdatePipeline(t_view)
b = bikeS.GetDataInformation().GetBounds()
print("bike bounds:", [round(x, 3) for x in b])
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
view.ViewTime = t_view

def colorbar(lut, title, view):
    bar = GetScalarBar(lut, view)
    bar.Title = title
    bar.ComponentTitle = ""
    bar.TitleColor = bar.LabelColor = [0.1, 0.1, 0.1]
    bar.TitleFontSize = bar.LabelFontSize = 16
    bar.ScalarBarLength = 0.35
    bar.Visibility = 1
    return bar

# ------------------------------------------------ 1) bike + streamtubes
dm = Show(bikeS, view)
ColorBy(dm, ("POINTS", "p"))
lutP = GetColorTransferFunction("p")
lutP.ApplyPreset("Cool to Warm", True)
lutP.AutomaticRescaleRangeMode = "Never"
lutP.RescaleTransferFunction(-600.0, 200.0)
colorbar(lutP, "p [m²/s²]", view).WindowLocation = "Any Location"
GetScalarBar(lutP, view).Position = [0.90, 0.55]

H = b[5] - b[4]
st = StreamTracer(Input=vol, SeedType="Point Cloud")
st.Vectors = ["POINTS", "U"]
st.SeedType.Center = [b[0] - 0.15 * L, cy, b[4] + 0.5 * H]
st.SeedType.Radius = 0.5 * H
st.SeedType.NumberOfPoints = 500
st.MaximumStreamlineLength = 2.2 * L
st.IntegrationDirection = "FORWARD"
# only the far half (y > center): the bike stays in front of the lines
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
colorbar(lutU, "|U| [m/s]", view).WindowLocation = "Any Location"
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

# ------------------------------------------- 2) symmetry-plane cut
Hide(tb, view)
HideScalarBarIfNotNeeded(lutU, view)
sl = Slice(Input=vol)
sl.SliceType = "Plane"
sl.SliceType.Origin = [cx, cy, cz]
sl.SliceType.Normal = [0, 1, 0]
ds = Show(sl, view)
ColorBy(ds, ("POINTS", "U", "Magnitude"))
lutU.RescaleTransferFunction(0.0, 25.0)
colorbar(lutU, "|U| [m/s]", view).WindowLocation = "Any Location"
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
