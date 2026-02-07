from pathlib import Path

from fastapi import FastAPI, UploadFile, File, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any

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
        # Load content into Fix Engine
        content = await file.read()
        await file.seek(0)  # Reset for downstream processing
        
        # Initialize Engine with WKT content
        from .qa.fix_engine import get_fix_engine
        engine = get_fix_engine()
        wkt_str = content.decode("utf-8")
        engine.load_wkt_content(wkt_str)
        
        result = await run_geometry_qa(file)
        result["mode"] = "geometry"
        return result
    except Exception as e:
        print(f"DEBUG: geometry_qa EXCEPTION: {e}")
        raise

# --------------------------------------------------
# APPLY FIX & EXPORT
# --------------------------------------------------
from .qa.fix_engine import get_fix_engine

class ApplyFixRequest(BaseModel):
    error_id: str
    fix_type: str  # SNAP, DELETE, SPLIT, OTHER
    parameters: Optional[Dict[str, Any]] = None

@app.post("/qa/apply-fix")
async def apply_fix(request: ApplyFixRequest):
    """
    Apply a robust fix to the geometry in memory.
    """
    engine = get_fix_engine()
    result = engine.apply_fix(request.error_id, request.fix_type, request.parameters)
    return result

@app.get("/qa/export/fixed-wkt")
async def export_fixed_wkt():
    """Download the modified WKT file."""
    engine = get_fix_engine()
    wkt_content = engine.export_fixed_wkt()
    return Response(content=wkt_content, media_type="text/plain", headers={"Content-Disposition": "attachment; filename=fixed_geometry.wkt"})

@app.get("/qa/export/fix-report")
async def export_fix_report():
    """Download the fix report."""
    engine = get_fix_engine()
    report = engine.export_report()
    return Response(content=report, media_type="text/plain", headers={"Content-Disposition": "attachment; filename=fix_report.txt"})

# --------------------------------------------------
# AI-POWERED FIX SUGGESTION (RAG + LLM)
# --------------------------------------------------
from .qa.rag_agent import get_rag_agent, sanitize_code
from .qa.osm_validator import get_osm_validator
from pydantic import BaseModel
from typing import Optional, Dict, Any

class FixRequest(BaseModel):
    error_id: str
    error_type: str
    description: str
    location: Optional[str] = None
    wkt: Optional[str] = None

class SaveFixRequest(BaseModel):
    error_type: str
    context: str
    fix_description: str
    fix_code: str

@app.post("/qa/fix-error")
async def get_fix_suggestion(request: FixRequest):
    """
    Get an AI-generated fix suggestion for an error.
    Uses RAG pipeline with local training data + LLM.
    """
    agent = get_rag_agent()
    
    error_dict = {
        "id": request.error_id,
        "type": request.error_type,
        "description": request.description,
        "location": request.location,
        "wkt": request.wkt
    }
    
    suggestion = agent.generate_fix_suggestion(error_dict)
    
    # Sanitize the generated code
    if suggestion.get("code"):
        safety_check = sanitize_code(suggestion["code"])
        suggestion["is_safe"] = safety_check["is_safe"]
        suggestion["safety_reason"] = safety_check["reason"]
    
    return suggestion

@app.post("/qa/save-fix")
async def save_fix(request: SaveFixRequest):
    """
    Save a user-approved fix to the training data.
    This enables active learning - the system learns from your corrections.
    """
    agent = get_rag_agent()
    result = agent.save_fix(
        error_type=request.error_type,
        context=request.context,
        fix_description=request.fix_description,
        fix_code=request.fix_code
    )
    return result

@app.post("/qa/validate-osm")
async def validate_with_osm(request: FixRequest):
    """
    Validate an error against OpenStreetMap data.
    Helps determine if an error is true or a false positive.
    """
    validator = get_osm_validator()
    
    error_dict = {
        "id": request.error_id,
        "type": request.error_type,
        "description": request.description,
        "location": request.location
    }
    
    result = validator.validate_dangle_error(error_dict, is_cartesian=True)
    return result
