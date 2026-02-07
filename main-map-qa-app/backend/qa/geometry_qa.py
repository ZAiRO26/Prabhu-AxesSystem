# from shapely import wkt
# from shapely.geometry import MultiLineString, box
# import matplotlib.pyplot as plt
# import uuid
# import os
#
# OUTPUT_DIR = "backend/outputs"
# os.makedirs(OUTPUT_DIR, exist_ok=True)
#
# async def run_geometry_qa(uploaded_file):
#     text = (await uploaded_file.read()).decode("utf-8")
#
#     lines = []
#     buffer = ""
#
#     for line in text.splitlines():
#         line = line.strip()
#         if not line:
#             continue
#         buffer += line + " "
#         if line.endswith(")"):
#             lines.append(wkt.loads(buffer))
#             buffer = ""
#
#     streets = MultiLineString([l.coords for l in lines])
#     street_buffer = streets.buffer(2.0)
#
#     # Example labels (synthetic for demo)
#     labels = [
#         box(7200-8, 8660-4, 7200+8, 8660+4),
#         box(7155-8, 8645-4, 7155+8, 8645+4)
#     ]
#
#     errors = []
#     bad_labels = []
#
#     for i, label in enumerate(labels):
#         if label.intersects(street_buffer):
#             severity = label.intersection(street_buffer).area / label.area
#             errors.append({
#                 "type": "label_street_overlap",
#                 "severity": round(severity, 2),
#                 "description": "Label overlaps street geometry"
#             })
#             bad_labels.append(label)
#
#     # ---- Visualization ----
#     fig, ax = plt.subplots(figsize=(6,6))
#
#     for line in streets.geoms:
#         x, y = line.xy
#         ax.plot(x, y, color="black")
#
#     for label in labels:
#         x, y = label.exterior.xy
#         ax.plot(x, y, color="green")
#
#     for label in bad_labels:
#         x, y = label.exterior.xy
#         ax.fill(x, y, color="red", alpha=0.5)
#
#     ax.set_title("Geometry QA – Label/Street Overlap")
#     ax.set_aspect("equal")
#
#     out_name = f"geometry_{uuid.uuid4().hex}.png"
#     out_path = os.path.join(OUTPUT_DIR, out_name)
#     plt.savefig(out_path)
#     plt.close()
#
#     return f"/outputs/{out_name}", errors
#
# from shapely import wkt
# from shapely.geometry import MultiLineString
# import matplotlib.pyplot as plt
# from sklearn.ensemble import IsolationForest
# import uuid
# import os
# import numpy as np
#
# OUTPUT_DIR = "backend/outputs"
# os.makedirs(OUTPUT_DIR, exist_ok=True)
#
#
# async def run_geometry_qa(uploaded_file):
#     # -----------------------------
#     # 1. Load WKT geometries
#     # -----------------------------
#     text = (await uploaded_file.read()).decode("utf-8")
#
#     lines = []
#     buffer = ""
#
#     for line in text.splitlines():
#         line = line.strip()
#         if not line:
#             continue
#         buffer += line + " "
#         if line.endswith(")"):
#             geom = wkt.loads(buffer)
#             lines.append(geom)
#             buffer = ""
#
#     # -----------------------------
#     # 2. Extract geometric features
#     # -----------------------------
#     features = []
#     for geom in lines:
#         features.append([
#             geom.length,
#             len(geom.coords)
#         ])
#
#     X = np.array(features)
#
#     # -----------------------------
#     # 3. ML-based anomaly detection
#     # -----------------------------
#     model = IsolationForest(
#         n_estimators=100,
#         contamination=0.15,
#         random_state=42
#     )
#     predictions = model.fit_predict(X)
#
#     # -----------------------------
#     # 4. Detect ONE error type
#     #    "Degenerate / Abnormally short lines"
#     # -----------------------------
#     errors = []
#     bad_indices = []
#
#     for idx, pred in enumerate(predictions):
#         if pred == -1:
#             severity = round(
#                 1.0 - (lines[idx].length / max(X[:, 0])),
#                 2
#             )
#
#             errors.append({
#                 "type": "degenerate_line_geometry",
#                 "geometry_index": idx,
#                 "severity": severity,
#                 "description": "Line geometry is abnormally short compared to peers"
#             })
#
#             bad_indices.append(idx)
#
#     # -----------------------------
#     # 5. Visualization (unchanged contract)
#     # -----------------------------
#     fig, ax = plt.subplots(figsize=(6, 6))
#
#     for i, geom in enumerate(lines):
#         x, y = geom.xy
#         if i in bad_indices:
#             ax.plot(x, y, color="red", linewidth=2)
#         else:
#             ax.plot(x, y, color="black", linewidth=1)
#
#     ax.set_title("Geometry QA – Degenerate Line Detection")
#     ax.set_aspect("equal")
#
#     out_name = f"geometry_{uuid.uuid4().hex}.png"
#     out_path = os.path.join(OUTPUT_DIR, out_name)
#     plt.savefig(out_path)
#     plt.close()
#
#     return f"/outputs/{out_name}", errors


# from shapely import wkt
# from shapely.geometry import MultiLineString
# from shapely.validation import explain_validity
# import matplotlib.pyplot as plt
# import uuid
# import os
#
# OUTPUT_DIR = "backend/outputs"
# os.makedirs(OUTPUT_DIR, exist_ok=True)
#
#
# async def run_geometry_qa(uploaded_file):
#     # --------------------------------------------------
#     # 1. Load raw WKT geometries
#     # --------------------------------------------------
#     text = (await uploaded_file.read()).decode("utf-8")
#
#     lines = []
#     buffer = ""
#
#     for line in text.splitlines():
#         line = line.strip()
#         if not line:
#             continue
#         buffer += line + " "
#         if line.endswith(")"):
#             geom = wkt.loads(buffer)
#             lines.append(geom)
#             buffer = ""
#
#     # --------------------------------------------------
#     # 2. RULE-BASED GEOMETRY VALIDATION (PRIMARY)
#     #    Single error type: invalid topology
#     # --------------------------------------------------
#     errors = []
#     invalid_indices = []
#
#     for idx, geom in enumerate(lines):
#         if not geom.is_valid:
#             errors.append({
#                 "type": "invalid_line_topology",
#                 "geometry_index": idx,
#                 "description": explain_validity(geom)
#             })
#             invalid_indices.append(idx)
#
#     # --------------------------------------------------
#     # 3. Visualization (unchanged integration contract)
#     # --------------------------------------------------
#     fig, ax = plt.subplots(figsize=(6, 6))
#
#     for i, geom in enumerate(lines):
#         x, y = geom.xy
#         if i in invalid_indices:
#             ax.plot(x, y, color="red", linewidth=2)
#         else:
#             ax.plot(x, y, color="black", linewidth=1)
#
#     ax.set_title("Geometry QA – Invalid Line Topology")
#     ax.set_aspect("equal")
#
#     out_name = f"geometry_{uuid.uuid4().hex}.png"
#     out_path = os.path.join(OUTPUT_DIR, out_name)
#     plt.savefig(out_path)
#     plt.close()
#
#     return f"/outputs/{out_name}", errors

# from shapely import wkt
# from shapely.geometry import Point
# import matplotlib.pyplot as plt
# import uuid
# import os
# import math
#
# OUTPUT_DIR = "backend/outputs"
# os.makedirs(OUTPUT_DIR, exist_ok=True)
#
# # Distance tolerance for snapping / connectivity
# TOLERANCE = 1.0
#
#
# async def run_geometry_qa(uploaded_file):
#     # --------------------------------------------------
#     # 1. Load raw WKT geometries
#     # --------------------------------------------------
#     text = (await uploaded_file.read()).decode("utf-8")
#
#     lines = []
#     buffer = ""
#
#     for line in text.splitlines():
#         line = line.strip()
#         if not line:
#             continue
#         buffer += line + " "
#         if line.endswith(")"):
#             geom = wkt.loads(buffer)
#             lines.append(geom)
#             buffer = ""
#
#     # --------------------------------------------------
#     # 2. Collect all endpoints
#     # --------------------------------------------------
#     endpoints = []  # (Point, parent_line_index)
#
#     for idx, geom in enumerate(lines):
#         coords = list(geom.coords)
#         endpoints.append((Point(coords[0]), idx))        # start
#         endpoints.append((Point(coords[-1]), idx))       # end
#
#     # --------------------------------------------------
#     # 3. Dangling endpoint detection (SINGLE RULE)
#     # --------------------------------------------------
#     errors = []
#     dangling_points = []
#
#     for i, (pt, parent_idx) in enumerate(endpoints):
#         connected = False
#
#         for j, (other_pt, other_parent_idx) in enumerate(endpoints):
#             if i == j:
#                 continue
#
#             # Allow connection to any other line
#             if pt.distance(other_pt) <= TOLERANCE:
#                 connected = True
#                 break
#
#         if not connected:
#             dangling_points.append(pt)
#             errors.append({
#                 "type": "dangling_endpoint",
#                 "geometry_index": parent_idx,
#                 "description": "Line endpoint is not connected to any other line"
#             })
#
#     # --------------------------------------------------
#     # 4. Visualization (unchanged integration contract)
#     # --------------------------------------------------
#     fig, ax = plt.subplots(figsize=(6, 6))
#
#     # Draw all lines
#     for geom in lines:
#         x, y = geom.xy
#         ax.plot(x, y, color="black", linewidth=1)
#
#     # Highlight dangling endpoints
#     for pt in dangling_points:
#         ax.scatter(pt.x, pt.y, color="red", s=30)
#
#     ax.set_title("Geometry QA – Dangling Endpoint Detection")
#     ax.set_aspect("equal")
#
#     out_name = f"geometry_{uuid.uuid4().hex}.png"
#     out_path = os.path.join(OUTPUT_DIR, out_name)
#     plt.savefig(out_path)
#     plt.close()
#
#     return f"/outputs/{out_name}", errors
from shapely import wkt
from shapely.geometry import Point, MultiLineString, LineString
from shapely.validation import explain_validity
import numpy as np
import matplotlib.pyplot as plt
import uuid
import os

# --------------------------------------------------
# Config
# --------------------------------------------------
# --------------------------------------------------
# Config
# --------------------------------------------------
OUTPUT_DIR = "backend/outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Snap tolerance for connectivity (in map units)
TOLERANCE = 0.5 
MIN_LINE_LENGTH = 2.0

# --------------------------------------------------
# Geometry Rules
# --------------------------------------------------
def find_dangles(lines_data, tolerance=TOLERANCE):
    """
    Finds endpoints of lines that do not snap to any other line endpoint 
    or vertex within the tolerance.
    """
    endpoints = []
    
    # 1. Collect all endpoints
    for item in lines_data:
        geom = item["geom"]
        idx = item["id"]
        line_no = item["line_no"]

        if geom is None or geom.is_empty:
            continue

        # Handle LineString vs MultiLineString
        geoms_list = []
        if geom.geom_type == 'LineString':
            geoms_list = [geom]
        elif geom.geom_type == 'MultiLineString':
            geoms_list = list(geom.geoms)
        
        for part in geoms_list:
            coords = list(part.coords)
            if len(coords) < 2: continue
            
            # Start point
            endpoints.append({
                "pt": Point(coords[0]), 
                "line_idx": idx,
                "line_no": line_no,
                "loc": "start", 
                "coord": coords[0]
            })
            # End point
            endpoints.append({
                "pt": Point(coords[-1]), 
                "line_idx": idx,
                "line_no": line_no, 
                "loc": "end", 
                "coord": coords[-1]
            })

    errors = []
    
    # 2. Check connectivity
    for ep in endpoints:
        is_connected = False
        pt = ep["pt"]
        my_idx = ep["line_idx"]
        
        # Check against all other lines
        for other_item in lines_data:
            other_idx = other_item["id"]
            other_geom = other_item["geom"]

            if my_idx == other_idx:
                continue 
            
            if other_geom is None or other_geom.is_empty:
                continue

            # Distance to the *geometry*
            if pt.distance(other_geom) <= tolerance:
                is_connected = True
                break
        
        if not is_connected:
            # Check for rings (self-closing LineStrings)
            is_ring = False
            my_geom = lines_data[my_idx]["geom"]
            if my_geom.geom_type == 'LineString' and my_geom.is_ring:
                 is_ring = True
            
            if not is_ring:
                errors.append({
                    "id": f"dangle-{ep['line_no']}-{ep['loc']}",
                    "type": "Dangle (Unconnected Endpoint)",
                    "geometry_index": my_idx,
                    "line_number": ep['line_no'],
                    "location": f"{ep['coord'][0]:.6f}, {ep['coord'][1]:.6f}",
                    "severity": "HIGH",
                    "description": f"Dangle at {ep['loc']} (Line {ep['line_no']}). No snap within {tolerance}m.",
                    "wkt": ep["pt"].wkt,  # Send POINT WKT, not LineString WKT
                    "error_point": ep["coord"] 
                })

    return errors

def find_short_lines(lines_data, min_len=MIN_LINE_LENGTH):
    errors = []
    for item in lines_data:
        geom = item["geom"]
        if geom is None or geom.is_empty: continue
        
        if geom.length < min_len:
             errors.append({
                "id": f"short-{item['line_no']}",
                "type": "Short Line Segment",
                "geometry_index": item["id"],
                "line_number": item['line_no'],
                "location": f"{geom.centroid.x:.6f}, {geom.centroid.y:.6f}",
                "severity": "LOW",
                "description": f"Line {item['line_no']} is too short ({geom.length:.4f}m).",
                 "wkt": geom.wkt
            })
    return errors

# --------------------------------------------------
# MAIN ENTRY POINT
# --------------------------------------------------
async def run_geometry_qa(uploaded_file):
    try:
        # 1. Load WKT with Line Numbers
        text = (await uploaded_file.read()).decode("utf-8")
        
        lines_data = [] # List of dicts: {id, line_no, geom}
        buf = ""
        start_line_no = 0
        
        raw_lines = text.splitlines()
        
        current_statement_start = 0
        
        for i, line_str in enumerate(raw_lines):
            stripped = line_str.strip()
            if not stripped: continue
            
            if not buf:
                current_statement_start = i + 1  # 1-based line number
                
            buf += stripped + " "
            
            if stripped.endswith(")"):
                try:
                    clean_wkt = buf.split(";")[-1] 
                    geom = wkt.loads(clean_wkt)
                    if geom and not geom.is_empty:
                        lines_data.append({
                            "id": len(lines_data),
                            "line_no": current_statement_start,
                            "geom": geom
                        })
                except Exception:
                    pass
                buf = ""

        if len(lines_data) < 1:
              return {
                    "output_url": None,
                    "errors": [{
                        "type": "insufficient_data",
                        "description": "No valid geometries found."
                    }],
                    "collection_wkt": []
                }

        errors = []

        # 2. Validity Checks
        for item in lines_data:
            g = item["geom"]
            if not g.is_valid:
                errors.append({
                    "id": f"invalid-{item['line_no']}",
                    "type": "Invalid Geometry",
                    "geometry_index": item["id"],
                    "line_number": item['line_no'],
                    "location": "N/A",
                    "severity": "CRITICAL",
                    "description": f"Line {item['line_no']}: {explain_validity(g)}",
                    "wkt": g.wkt
                })

        # 3. Topology Checks
        errors.extend(find_dangles(lines_data))
        errors.extend(find_short_lines(lines_data))

        # 4. Visualization
        fig, ax = plt.subplots(figsize=(8, 8))
        
        # Plot all lines grey
        for item in lines_data:
            g = item["geom"]
            try:
                if g.geom_type == 'MultiLineString':
                    for part in g.geoms:
                        x, y = part.xy
                        ax.plot(x, y, color="#64748b", linewidth=1.5, alpha=0.9, zorder=1)
                else:
                    x, y = g.xy
                    ax.plot(x, y, color="#64748b", linewidth=1.5, alpha=0.9, zorder=1)
            except:
                 pass

        # Highlight errors
        for e in errors:
            # Dangles -> Red Dots
            if "error_point" in e:
                px, py = e["error_point"]
                ax.scatter([px], [py], color="red", s=60, zorder=10, edgecolors='white', linewidth=1.5)
            
            # Line errors -> Red Lines
            # Only draw line if it's NOT a dangle (dangles are point errors now)
            if "type" in e and "Dangle" not in e["type"]:
                idx = e.get("geometry_index")
                if idx is not None:
                    g = lines_data[idx]["geom"]
                    try:
                        if g.geom_type == 'MultiLineString':
                            for part in g.geoms:
                                x, y = part.xy
                                ax.plot(x, y, color="red", linewidth=2.5, alpha=0.8, zorder=5)
                        else:
                            x, y = g.xy
                            ax.plot(x, y, color="red", linewidth=2.5, alpha=0.8, zorder=5)
                    except:
                        pass

        ax.set_title(f"Geometry QA Report: {len(errors)} Issues Found")
        ax.set_aspect("equal")
        
        # User requested axis and grid lines back
        ax.grid(True, linestyle=':', alpha=0.6)
        # plt.axis('off')  <-- REMOVED

        out_name = f"geometry_{uuid.uuid4().hex}.png"
        out_path = os.path.join(OUTPUT_DIR, out_name)
        plt.savefig(out_path, bbox_inches='tight', dpi=150)
        plt.close()

        return {
            "output_url": f"/outputs/{out_name}",
            "errors": errors,
            "collection_wkt": [item["geom"].wkt for item in lines_data]
        }
    except Exception as e:
        print(f"Exception in geometry QA: {e}")
        return {
            "output_url": None,
            "errors": [{
                "type": "processing_error",
                "description": f"Failed to process geometry: {str(e)}"
            }],
            "collection_wkt": []
        }
