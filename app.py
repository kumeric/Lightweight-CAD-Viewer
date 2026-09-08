# -*- coding: utf-8 -*-
"""
Lightweight CAD Viewer (STL / OBJ / PLY / STEP / IGES)
=================================================
A lightweight desktop viewer designed for quickly inspecting CAD files on
Windows without heavy software like Blender.

Supported Formats:
- STL, OBJ, PLY, VTP, etc.  : Natively supported by PyVista (VTK) as mesh files.
- STEP (.step, .stp)
  IGES (.igs, .iges)        : Loaded via OCP (pip, wheels available for Windows/Linux/macOS)
                              or pythonocc-core (conda), tessellated into triangular meshes,
                              and displayed. If both libraries are missing, a notice is displayed
                              stating STEP/IGES files cannot be opened, while other formats like
                              STL will work normally.

How to Run:
    python app.py
    python app.py path/to/file.stl   (Open file directly via command-line arguments)

Please refer to README.md in the same directory for installation instructions.
"""

import gc
import os
import sys
import traceback

import numpy as np
from PyQt5 import QtWidgets, QtCore, QtGui

import pyvista as pv
from pyvistaqt import QtInteractor

# ---------------------------------------------------------------------------
# STEP File Support - Optional Dependencies
#   1st Priority: OCP (pip install cadquery-ocp) - Pre-built wheels available for 
#                 Windows/Linux/macOS. Recommended as it supports packaging into 
#                 Windows .exe using PyInstaller.
#   2nd Priority: OCC.Core (conda install -c conda-forge pythonocc-core) - For 
#                 existing conda environments.
# Both libraries wrap the same OCCT API, but static method naming differs:
#   - OCC.Core (SWIG):  topods.Face(shape) / BRep_Tool.Triangulation(face, loc)
#   - OCP (pybind11):   TopoDS.Face_s(shape) / BRep_Tool.Triangulation_s(face, loc)
# ---------------------------------------------------------------------------
STEP_SUPPORT = True
STEP_BACKEND = None  # "ocp" or "occ"

try:
    from OCP.STEPControl import STEPControl_Reader
    from OCP.IGESControl import IGESControl_Reader
    from OCP.IFSelect import IFSelect_RetDone
    from OCP.BRepMesh import BRepMesh_IncrementalMesh
    from OCP.TopExp import TopExp_Explorer
    from OCP.TopAbs import TopAbs_FACE
    from OCP.TopoDS import TopoDS
    from OCP.BRep import BRep_Tool
    from OCP.TopLoc import TopLoc_Location

    STEP_BACKEND = "ocp"
except ImportError:
    try:
        from OCC.Core.STEPControl import STEPControl_Reader
        from OCC.Core.IGESControl import IGESControl_Reader
        from OCC.Core.IFSelect import IFSelect_RetDone
        from OCC.Core.BRepMesh import BRepMesh_IncrementalMesh
        from OCC.Core.TopExp import TopExp_Explorer
        from OCC.Core.TopAbs import TopAbs_FACE
        from OCC.Core.TopoDS import topods as TopoDS  # Match OCP naming convention to share the code below
        from OCC.Core.BRep import BRep_Tool
        from OCC.Core.TopLoc import TopLoc_Location

        STEP_BACKEND = "occ"
    except ImportError:
        STEP_SUPPORT = False


def resource_path(*parts: str) -> str:
    """Resolves a bundled resource path for both normal runs and a PyInstaller --onefile build."""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, *parts)


MESH_EXTENSIONS = {".stl", ".obj", ".ply", ".vtp", ".vtk", ".vtu"}
STEP_EXTENSIONS = {".step", ".stp"}
IGES_EXTENSIONS = {".igs", ".iges"}
CAD_EXTENSIONS = STEP_EXTENSIONS | IGES_EXTENSIONS
SUPPORTED_EXTENSIONS = MESH_EXTENSIONS | CAD_EXTENSIONS


def _static(cls, name: str):
    """Looks up a static method that may or may not carry pybind11's disambiguating
    '_s' suffix (this varies across OCP releases, e.g. TopoDS.Face vs TopoDS.Face_s)."""
    return getattr(cls, f"{name}_s", None) or getattr(cls, name)


def cad_to_polydata(filepath: str, linear_deflection: float = 0.3) -> pv.PolyData:
    """Reads a STEP or IGES file and converts it into a triangular mesh (pv.PolyData)."""
    if not STEP_SUPPORT:
        raise RuntimeError(
            "OCP or pythonocc-core is required to open STEP/IGES files.\n"
            "Installation (Recommended, pip): pip install cadquery-ocp\n"
            "Installation (Conda): conda install -c conda-forge pythonocc-core"
        )

    ext = os.path.splitext(filepath)[1].lower()
    if ext in STEP_EXTENSIONS:
        reader = STEPControl_Reader()
    elif ext in IGES_EXTENSIONS:
        reader = IGESControl_Reader()
    else:
        raise RuntimeError(f"Unsupported CAD format: {ext}")

    status = reader.ReadFile(filepath)
    if status != IFSelect_RetDone:
        raise RuntimeError(f"Failed to read CAD file: {filepath}")

    reader.TransferRoots()
    shape = reader.OneShape()

    # Tessellate geometry into triangles (smaller linear_deflection increases detail but slows down loading)
    BRepMesh_IncrementalMesh(shape, linear_deflection, False, 0.5, True)

    vertices = []
    faces = []
    offset = 0

    explorer = TopExp_Explorer(shape, TopAbs_FACE)
    while explorer.More():
        face = _static(TopoDS, "Face")(explorer.Current())

        location = TopLoc_Location()
        triangulation = _static(BRep_Tool, "Triangulation")(face, location)

        if triangulation is not None:
            transform = location.Transformation()
            nb_nodes = triangulation.NbNodes()
            for i in range(1, nb_nodes + 1):
                pnt = triangulation.Node(i)
                pnt.Transform(transform)
                vertices.append((pnt.X(), pnt.Y(), pnt.Z()))

            nb_triangles = triangulation.NbTriangles()
            for i in range(1, nb_triangles + 1):
                tri = triangulation.Triangle(i)
                n1, n2, n3 = tri.Get()
                faces.append((3, offset + n1 - 1, offset + n2 - 1, offset + n3 - 1))

            offset += nb_nodes

        explorer.Next()

    # Force garbage collection for OCCT C++ memory
    del reader
    gc.collect()
    
    if not vertices:
        raise RuntimeError("Could not find any displayable geometry (faces) in the STEP file.")

    points = np.asarray(vertices, dtype=float)
    faces_arr = np.hstack(faces).astype(np.int64)
    return pv.PolyData(points, faces_arr)


class CADViewer(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Lightweight CAD Viewer")
        icon_path = resource_path("assets", "icon.ico")
        if os.path.isfile(icon_path):
            self.setWindowIcon(QtGui.QIcon(icon_path))
        self.resize(1100, 750)
        self.setAcceptDrops(True)

        self.current_actor = None
        self.current_mesh = None
        self.current_path = None

        self._build_ui()

    # -- UI Construction -----------------------------------------------------------
    def _build_ui(self):
        self.plotter = QtInteractor(self)
        self.plotter.set_background("#2b2b2b")
        self.setCentralWidget(self.plotter.interactor)

        # Menu Bar
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")

        open_action = QtWidgets.QAction("Open...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_file_dialog)
        file_menu.addAction(open_action)

        save_shot_action = QtWidgets.QAction("Save Screenshot...", self)
        save_shot_action.triggered.connect(self.save_screenshot)
        file_menu.addAction(save_shot_action)

        file_menu.addSeparator()
        exit_action = QtWidgets.QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Toolbar
        toolbar = QtWidgets.QToolBar("Tools")
        self.addToolBar(toolbar)

        solid_action = QtWidgets.QAction("Solid", self)
        solid_action.triggered.connect(lambda: self.set_style("surface"))
        toolbar.addAction(solid_action)

        wire_action = QtWidgets.QAction("Wireframe", self)
        wire_action.triggered.connect(lambda: self.set_style("wireframe"))
        toolbar.addAction(wire_action)

        points_action = QtWidgets.QAction("Points", self)
        points_action.triggered.connect(lambda: self.set_style("points"))
        toolbar.addAction(points_action)

        toolbar.addSeparator()

        edges_action = QtWidgets.QAction("Toggle Edges", self)
        edges_action.setCheckable(True)
        edges_action.setChecked(True)
        edges_action.triggered.connect(self.toggle_edges)
        toolbar.addAction(edges_action)
        self.edges_action = edges_action

        toolbar.addSeparator()

        fit_action = QtWidgets.QAction("Fit to Screen", self)
        fit_action.triggered.connect(lambda: self.plotter.reset_camera())
        toolbar.addAction(fit_action)

        # Status Bar
        self.status = self.statusBar()
        self.status.showMessage(
            "Open a file (Ctrl+O) or drag and drop files into this window. "
            f"(STEP/IGES Support: {'Enabled (' + STEP_BACKEND + ')' if STEP_SUPPORT else 'Disabled - run pip install cadquery-ocp'})"
        )

    # -- File Open -----------------------------------------------------------
    def open_file_dialog(self):
        filters = (
            "CAD Files (*.stl *.obj *.ply *.step *.stp *.igs *.iges);;"
            "STL (*.stl);;OBJ (*.obj);;PLY (*.ply);;STEP (*.step *.stp);;"
            "IGES (*.igs *.iges);;All Files (*)"
        )
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Open CAD File", "", filters)
        if path:
            self.load_file(path)

    def load_file(self, path: str):
        ext = os.path.splitext(path)[1].lower()
        if ext not in SUPPORTED_EXTENSIONS:
            QtWidgets.QMessageBox.warning(
                self, "Unsupported Format", f"Unsupported file extension: {ext}"
            )
            return

        self.status.showMessage(f"Loading: {path} ...")
        QtWidgets.QApplication.processEvents()

        try:
            if ext in CAD_EXTENSIONS:
                mesh = cad_to_polydata(path)
            else:
                mesh = pv.read(path)
        except Exception as exc:  # noqa: BLE001
            traceback.print_exc()
            QtWidgets.QMessageBox.critical(self, "Load Failed", str(exc))
            self.status.showMessage("Load Failed")
            return

        self._display_mesh(mesh, path)

    def _display_mesh(self, mesh: pv.PolyData, path: str):
        self.plotter.clear()
        self.current_actor = self.plotter.add_mesh(
            mesh,
            color="#c9c9c9",
            show_edges=self.edges_action.isChecked(),
            edge_color="black",
            smooth_shading=True,
        )
        self.plotter.reset_camera()
        self.plotter.enable_anti_aliasing()

        self.current_mesh = mesh
        self.current_path = path
        self.setWindowTitle(f"Lightweight CAD Viewer - {os.path.basename(path)}")

        try:
            n_points = mesh.n_points
            n_cells = mesh.n_cells
            bounds = mesh.bounds
            size = (
                bounds[1] - bounds[0],
                bounds[3] - bounds[2],
                bounds[5] - bounds[4],
            )
            self.status.showMessage(
                f"{os.path.basename(path)}  |  Vertices: {n_points:,}  |  Triangles: {n_cells:,}  |  "
                f"Dimensions (X, Y, Z) ≈ ({size[0]:.2f}, {size[1]:.2f}, {size[2]:.2f})"
            )
        except Exception:
            self.status.showMessage(f"{os.path.basename(path)} successfully loaded.")

    # -- Display Options -----------------------------------------------------------
    def set_style(self, style: str):
        if self.current_actor is None:
            return
        self.current_actor.GetProperty().SetRepresentation(
            {"surface": 2, "wireframe": 1, "points": 0}[style]
        )
        self.plotter.render()

    def toggle_edges(self, checked: bool):
        if self.current_actor is None:
            return
        self.current_actor.GetProperty().SetEdgeVisibility(checked)
        self.plotter.render()

    def save_screenshot(self):
        if self.current_mesh is None:
            QtWidgets.QMessageBox.information(self, "Notice", "Please open a file first.")
            return
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Save Screenshot", "screenshot.png", "PNG (*.png)"
        )
        if path:
            self.plotter.screenshot(path)
            self.status.showMessage(f"Screenshot saved: {path}")

    # -- Override closeEvent for Safe Resource Cleanup --
    def closeEvent(self, event: QtGui.QCloseEvent):
        """Completely cleans up PyVista Interactor and associated resources when the window is closed."""
        try:
            self.plotter.close()
        except Exception:
            pass
        event.accept()
        
    # -- Drag & Drop -------------------------------------------------------
    def dragEnterEvent(self, event: QtGui.QDragEnterEvent):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls:
                # Accept only if the first file's extension matches a supported format
                path = urls[0].toLocalFile()
                ext = os.path.splitext(path)[1].lower()
                if ext in SUPPORTED_EXTENSIONS:
                    event.acceptProposedAction()
                    return
        event.ignore()
        
    def dropEvent(self, event: QtGui.QDropEvent):
        urls = event.mimeData().urls()
        if urls:
            path = urls[0].toLocalFile()
            if os.path.exists(path):
                self.load_file(path)

def main():
    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName("Lightweight CAD Viewer")
    icon_path = resource_path("assets", "icon.ico")
    if os.path.isfile(icon_path):
        app.setWindowIcon(QtGui.QIcon(icon_path))
    viewer = CADViewer()
    viewer.show()

    if len(sys.argv) > 1 and os.path.isfile(sys.argv[1]):
        viewer.load_file(sys.argv[1])

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()