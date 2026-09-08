# Lightweight CAD Viewer

A lightweight desktop viewer to quickly check **STL / OBJ / PLY / STEP / IGES** files on Windows without heavy software like Blender. It embeds a VTK-based 3D view (PyVista) inside a PyQt5 window, resulting in a minimal installation footprint and near-instant launch times.

## 0. Install & Run via WSL2 + Docker (Recommended)

Use this method if you prefer to isolate your environment completely inside Docker without managing a local Python environment. Thanks to **WSLg** (built into Windows 11, available via updates for Windows 10), the GUI window from the container seamlessly renders directly onto your Windows desktop without requiring a separate X server.

### Prerequisites

* Windows 11 (or Windows 10 with WSLg installed) + WSL2
* **Docker Desktop for Windows** with WSL2 integration enabled, or Docker Engine installed directly inside your WSL2 distro (`docker` and `docker compose` commands must be available)
* Verification: Run `echo $DISPLAY` in your WSL2 terminal. If it returns a value like `:0`, WSLg is operating normally.

### File Structure

```
cad_viewer/
├── app.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── CADViewer.spec       # PyInstaller build spec (bakes in the app icon + assets/)
├── .github/workflows/
│   └── build-windows.yml  # Builds CADViewer.exe on a real Windows runner (GitHub Actions)
├── assets/
│   └── icon.ico          # App icon, embedded into CADViewer.exe and shown in the window title bar
├── windows/
│   ├── install.bat        # Double-click to create Desktop/Start Menu shortcuts
│   └── Create-Shortcut.ps1
├── tools/
│   └── generate_icon.py  # Dev utility to regenerate assets/icon.ico
├── run.sh          # Build and run in one command
├── package.sh       # Package the image into a tarball
└── examples/           # CAD files placed here are mounted to /data (auto-generated)

```

### Build + Run

```bash
# Inside the cad_viewer directory in your WSL2 terminal
chmod +x run.sh package.sh
./run.sh

```

* The initial run takes a few minutes to build the image due to large packages like `vtk` and `cadquery-ocp` (subsequent runs are nearly instant as the image is cached).
* The viewer window will open directly on your Windows desktop.
* To open STEP/IGES/STL files, place them in the `examples/` folder and select `/data/filename` via "File → Open", or pass the file path directly as an argument as shown below:

```bash
./run.sh ~/Downloads/part.step

```

### Using Docker Compose Directly

```bash
docker compose build
docker compose run --rm cadviewer

```

### Troubleshooting Blank Screen or Rendering Issues

1. While `xhost` errors rarely occur under WSLg, if the window fails to appear, ensure that GUI support (WSLg) is enabled in your Windows WSL settings (`wsl --update` to fetch the latest version).
2. If rendering glitches occur due to GPU acceleration issues, uncomment `LIBGL_ALWAYS_SOFTWARE=1` in `docker-compose.yml` to force software rendering.

### Image Packaging (Deployment to Other PCs/Environments)

```bash
./package.sh          # Generates cadviewer.tar
# On another WSL2/Linux environment:
docker load -i cadviewer.tar
docker compose up      # Or use run.sh as usual

```

This single `cadviewer.tar` file allows you to restore and run the identical environment completely offline without an internet connection.

---

## 0-1. Packaging into a Standalone Windows Executable (.exe)

If you develop inside your WSL2/Docker environment but want a standalone `CADViewer.exe` that runs on Windows with a simple double-click (no installation required), build it via GitHub Actions.

> **Note on File Size**: Because GUI and graphics stacks like `PyQt5 + VTK` are heavy, the compiled file size will be large even when bundled into a single executable via the `--onefile` option (typically around 200–400MB). This is completely normal.

> **Why not cross-compile locally with Wine?** An earlier version of this project shipped a `build-windows.sh` that cross-compiled the `.exe` inside WSL2 using `tobix/pywine` (Windows Python running under Wine). In practice, PyInstaller crashes partway through under Wine with `Unimplemented function ucrtbase.dll.crealf` — a missing C-runtime math function that the current VTK/numpy versions depend on. Since this is a hard incompatibility (not a flaky/occasional failure), that script was removed. GitHub Actions builds on a genuine Windows runner and doesn't hit this issue.

### Building via GitHub Actions

A `.github/workflows/build-windows.yml` file is already included in this repository.

1. Push this folder to a GitHub repository (Run `git init && git add . && git commit -m init`, then add your origin in the WSL2 terminal).
2. Navigate to your GitHub repository page → **Actions** tab → **Build Windows exe** → Click **Run workflow** (Alternatively, pushing a version tag like `git tag v1.0 && git push --tags` triggers the build automatically).
3. Once the build completes, download `CADViewer-windows.zip` from the **Artifacts** section and extract it. The zip contains `CADViewer.exe` plus `install.bat` and `Create-Shortcut.ps1`.
4. Double-click `install.bat` (in the same extracted folder) once — it creates a **Desktop icon and a Start Menu shortcut** for CAD Viewer, both using the app's icon, so you can launch it afterwards just like any other Windows program.

### Packaging Notes

* The STEP/IGES support library has been updated from `pythonocc-core` (conda-exclusive) to **`cadquery-ocp` (pip-compatible with native Windows wheels)**, allowing you to bundle STEP/IGES support seamlessly without needing conda.
* The build runs from `CADViewer.spec`, which already bakes in the app icon (`assets/icon.ico`) and bundles the `assets/` folder into the executable — no extra flags needed. Run `python tools/generate_icon.py` (requires `pip install pillow`) if you ever want to regenerate or customize the icon.
* The `--windowed` flag baked into the spec suppresses the background console window. If you need to view console logs for debugging, set `console=True` in `CADViewer.spec` and rebuild.

### Using the Icon on Windows

Once you have `CADViewer.exe`, place it in a permanent folder (e.g., `C:\Program Files\CADViewer\` or anywhere under your user profile) together with `windows/install.bat` and `windows/Create-Shortcut.ps1`, then double-click `install.bat`. This creates:

* A **Desktop shortcut** ("CAD Viewer") showing the app icon.
* A **Start Menu shortcut** ("CAD Viewer") under Programs, so it's searchable via the Start menu.

You can also drag the Desktop icon onto the taskbar to pin it. Because the icon is embedded directly in `CADViewer.exe`, it also shows up correctly in File Explorer, Alt+Tab, and the taskbar without any extra setup.

---

## 1. Installation (Native Windows Python without Docker)

### Setup (Pip Only, Supports STL/OBJ/PLY/STEP/IGES)

```bat
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

```

Since `requirements.txt` includes `cadquery-ocp` (OCP bindings) for STEP/IGES support, the single installation command above configures your environment to open STL, OBJ, PLY, **STEP (.step, .stp)**, and **IGES (.igs, .iges)** files natively using pip. Conda is not required.

> Note: While historical versions required the conda-exclusive `pythonocc-core` for STEP/IGES support, `app.py` now natively supports both backends (prioritizing OCP, falling back to OCC.Core if missing). If you have an existing conda environment with `pythonocc-core` installed, it will continue to function normally.

## 2. Running the Application

```bat
python app.py

```

Alternatively, open a specific CAD file directly at launch:

```bat
python app.py C:\examples\part.step

```

## 3. How to Use

* **Open Files**: Go to **File → Open (Ctrl+O)** or simply **drag and drop** files directly into the window.
* **Top Toolbar**: Switch display modes between Solid, Wireframe, and Points. Toggle edge visibility On/Off, or reset the camera view to fit the screen.
* **Mouse Controls**: Left-click and drag to rotate, right-click and drag (or use the scroll wheel) to zoom, and middle-click (wheel click) and drag to pan.
* **Export**: Use **File → Save Screenshot** to export the current 3D viewport as a PNG image.

## 4. Packaging to .exe on Native Windows

If Python is already installed natively on your Windows host machine, you can package the application directly from your terminal:

```bat
pip install pyinstaller
pyinstaller --noconfirm --clean CADViewer.spec

```

The compiled binary will be located in `dist\CADViewer.exe`, already carrying the app icon (`assets/icon.ico`, baked in via `CADViewer.spec`). Including full STEP/IGES support (`cadquery-ocp`) increases the file size to several hundred megabytes, which is expected behavior. Afterwards, copy `windows\install.bat` and `windows\Create-Shortcut.ps1` next to `dist\CADViewer.exe` and double-click `install.bat` to create the Desktop/Start Menu icon (see "Using the Icon on Windows" above).

To handle this compilation inside a WSL2/Docker environment instead, refer to section **"0-1. Packaging into a Standalone Windows Executable (.exe)"** above.

## 5. Additional Technical Notes

* Formats like STL, OBJ, and PLY load rapidly and reliably as they are natively supported by the core VTK architecture.
* STEP and IGES files are mathematically approximated into triangles (tessellated) for real-time 3D rendering. You can adjust the `linear_deflection` variable inside the `cad_to_polydata()` function in `app.py`. Decreasing this value yields higher visual precision at the cost of rendering performance, while increasing it accelerates loading times but results in coarser mesh surfaces.