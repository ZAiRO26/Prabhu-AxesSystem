from pathlib import Path

from fastapi import FastAPI, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

# Local imports (relative, correct)
from .qa.image_qa import run_image_qa
from .qa.geometry_qa import run_geometry_qa

# --------------------------------------------------
# App initialization
# --------------------------------------------------
app = FastAPI(
    title="Map Quality Assurance Tool",
    description="Dual-mode QA for cartographic data (Image + Geometry)",
    version="1.0.0",
)

# --------------------------------------------------
# CORS Middleware (Enable Frontend Access)
# --------------------------------------------------
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For dev only. In prod, specify ["http://localhost:5173"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------
# Path resolution (CRITICAL & CORRECT)
# --------------------------------------------------
# backend/main.py -> backend/
BASE_DIR = Path(__file__).resolve().parent

# backend/.. -> main-map-qa-app/
PROJECT_ROOT = BASE_DIR.parent

# main-map-qa-app/static/
STATIC_DIR = PROJECT_ROOT / "static"

# main-map-qa-app/backend/outputs/
OUTPUTS_DIR = BASE_DIR / "outputs"
OUTPUTS_DIR.mkdir(exist_ok=True)

# --------------------------------------------------
# Static file serving
# --------------------------------------------------
app.mount(
    "/static",
    StaticFiles(directory=STATIC_DIR),
    name="static",
)

# --------------------------------------------------
# Serve generated output images
# --------------------------------------------------
app.mount(
    "/outputs",
    StaticFiles(directory=OUTPUTS_DIR),
    name="outputs",
)

# --------------------------------------------------
# Serve frontend UI
# --------------------------------------------------
@app.get("/", response_class=FileResponse)
def serve_ui():
    """
    Serves the main HTML UI
    """
    index_file = STATIC_DIR / "index.html"
    return FileResponse(index_file)

# --------------------------------------------------
# IMAGE-BASED QA
# --------------------------------------------------
@app.post("/qa/image")
async def image_qa(file: UploadFile = File(...)):
    """
    Image-based QA using OpenCV.
    Detects structural anomalies in map images.
    """
    output_path, errors = await run_image_qa(file)

    if output_path is None:
        return JSONResponse(
            status_code=400,
            content={"mode": "image", "errors": errors},
        )

    return {
        "mode": "image",
        "errors": errors,
        "output_url": output_path,
    }

# --------------------------------------------------
# GEOMETRY-BASED QA
# --------------------------------------------------
@app.post("/qa/geometry")
async def geometry_qa(file: UploadFile = File(...)):
    """
    Geometry-based QA using Shapely.
    Validates vector geometry and detects structural anomalies.
    """

    print(f"DEBUG: specific geometry_qa called with file: {file.filename}")
    try:
        result = await run_geometry_qa(file)
        result["mode"] = "geometry"
        return result
    except Exception as e:
        print(f"DEBUG: geometry_qa EXCEPTION: {e}")
        raise
