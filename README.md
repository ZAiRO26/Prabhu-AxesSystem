# Axes Systems QA Tool - Masai Hackathon v1.0

A dual-mode Map Quality Assurance tool designed to validate cartographic data. It supports both **Geometry validation** (checking for topological errors like dangles and short segments in WKT files) and **Image analysis** (detecting structural anomalies in map images).

![Screenshot](https://via.placeholder.com/800x400?text=Axes+Systems+QA+Dashboard)

## 🚀 Features

*   **Geometry QA**: 
    *   Parses WKT (Well-Known Text) files.
    *   Detects **Dangles** (disconnected endpoints) and **Short Segments**.
    *   Visualizes errors on an interactive map with Red/Blue highlighting.
    *   Provides a "Virtual Road Network" overlay to see errors in context.
    *   Exports reports in JSON and TXT formats.
*   **Image QA**:
    *   Analyzes map images for structural inconsistencies using OpenCV.
    *   Generates heatmaps of potential anomaly zones.

## 🛠️ Tech Stack

*   **Frontend**: React, Vite, Leaflet (Map visualization), Tailwind CSS.
*   **Backend**: Python, FastAPI, Shapely (Geometry analysis), OpenCV (Image processing).

## 📋 Prerequisites

*   [Node.js](https://nodejs.org/) (v16+)
*   [Python](https://www.python.org/) (v3.9+)

---

## 🏃‍♂️ Getting Started

### 1. Backend Setup (FastAPI)

The backend handles the geometry processing and image analysis algorithms.

1.  Navigate to the app directory:
    ```bash
    cd main-map-qa-app
    ```

2.  Create a virtual environment (optional but recommended):
    ```bash
    python -m venv venv
    # Windows
    .\venv\Scripts\activate
    # Mac/Linux
    source venv/bin/activate
    ```

3.  Install dependencies:
    ```bash
    pip install -r requirement.txt
    ```

4.  Start the Backend Server:
    ```bash
    python -m uvicorn backend.main:app --reload --port 8000
    ```
    The backend will run at `http://localhost:8000`.

### 2. Frontend Setup (React)

The frontend provides the user interface for uploading files and viewing results.

1.  Open a new terminal and navigate to the frontend directory:
    ```bash
    cd main-map-qa-app/frontend
    ```

2.  Install Node dependencies:
    ```bash
    npm install
    ```

3.  Start the Development Server:
    ```bash
    npm run dev
    ```
    The frontend will normally run at `http://localhost:5173`.

---

## 💡 How to Use

1.  Open your browser and search `http://localhost:5173`.
2.  **Select QA Mode**:
    *   **Geometry**: Upload a `.wkt` or `.txt` file containing WKT geometries. The tool will parse it, find broken links (dangles), and display them on the map. Use the "Hide/Show Network" toggle to see the valid roads vs. errors.
    *   **Image**: Upload a map image (`.png`, `.jpg`). The tool will analyze it for solid patches and anomalies.
3.  **View Results**: Click on any error in the sidebar to zoom into it on the map.
4.  **Export**: Use the "TXT" or "JSON" buttons to download the audit report.

## 📁 Project Structure

```
HackArena_AxesSystem/
├── main-map-qa-app/
│   ├── backend/             # Python FastAPI logic
│   │   ├── main.py          # Entry point
│   │   ├── qa/              # QA Algorithms (geometry_qa.py, image_qa.py)
│   │   └── outputs/         # Generated reports
│   ├── frontend/            # React Application
│   │   ├── src/
│   │   │   ├── components/  # MapViewer, UI Components
│   │   │   └── App.jsx      # Main Application logic
│   └── requirement.txt      # Python dependencies
```
