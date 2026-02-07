# import cv2
# import numpy as np
# import matplotlib.pyplot as plt
# import uuid
# import os
#
# OUTPUT_DIR = "backend/outputs"
# os.makedirs(OUTPUT_DIR, exist_ok=True)
#
# async def run_image_qa(uploaded_file):
#     # ---- Load image ----
#     file_bytes = np.frombuffer(await uploaded_file.read(), np.uint8)
#     img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
#
#     if img is None:
#         return None, [{
#             "type": "invalid_image",
#             "confidence": 1.0,
#             "description": "Uploaded file is not a valid image"
#         }]
#
#     original = img.copy()
#
#     # ---- Step 1: Preprocessing ----
#     gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
#     blurred = cv2.GaussianBlur(gray, (5, 5), 0)
#
#     # ---- Step 2: Edge Detection ----
#     edges = cv2.Canny(blurred, threshold1=50, threshold2=150)
#
#     # ---- Step 3: Line Detection (Hough Transform) ----
#     lines = cv2.HoughLinesP(
#         edges,
#         rho=1,
#         theta=np.pi / 180,
#         threshold=100,
#         minLineLength=40,
#         maxLineGap=15
#     )
#
#     # ---- Step 4: QA Heuristics ----
#     h, w = edges.shape
#     edge_density = np.sum(edges > 0) / (h * w)
#
#     line_count = 0
#     if lines is not None:
#         line_count = len(lines)
#
#     # Simple anomaly rule
#     anomaly_score = 1.0 - min(edge_density * 5, 1.0)
#
#     errors = []
#
#     if edge_density < 0.01 or line_count < 10:
#         errors.append({
#             "type": "missing_or_broken_roads",
#             "confidence": round(anomaly_score, 2),
#             "description": "Low road structure detected (possible missing or broken roads)"
#         })
#
#     # ---- Step 5: Visualization ----
#     vis = original.copy()
#
#     if lines is not None:
#         for l in lines:
#             x1, y1, x2, y2 = l[0]
#             cv2.line(vis, (x1, y1), (x2, y2), (0, 255, 0), 2)
#
#     if errors:
#         cv2.putText(
#             vis,
#             "Possible road anomaly detected",
#             (20, 40),
#             cv2.FONT_HERSHEY_SIMPLEX,
#             1,
#             (0, 0, 255),
#             2
#         )
#
#     # ---- Save output ----
#     out_name = f"image_{uuid.uuid4().hex}.png"
#     out_path = os.path.join(OUTPUT_DIR, out_name)
#     cv2.imwrite(out_path, vis)
#
#     return f"/outputs/{out_name}", errors
#
#
# import cv2
# import numpy as np
# import uuid
# import os
#
# OUTPUT_DIR = "backend/outputs"
# os.makedirs(OUTPUT_DIR, exist_ok=True)
#
# """
# Training instructions:
# 1. Collect 5–10 screenshots of CORRECT map outputs
# 2. For each image, compute:
#    - edge_density
#    - line_count
# 3. Set the minimum acceptable values below based on those examples
# """
#
# # Learned baseline from "good" images (example values)
# GOOD_IMAGE_BASELINE = {
#     "min_edge_density": 0.015,
#     "min_line_count": 15
# }
#
#
# async def run_image_qa(uploaded_file):
#     # --------------------------------------------------
#     # 1. Load image
#     # --------------------------------------------------
#     file_bytes = np.frombuffer(await uploaded_file.read(), np.uint8)
#     img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
#
#     if img is None:
#         return None, [{
#             "type": "invalid_image",
#             "confidence": 1.0,
#             "description": "Uploaded file is not a valid image"
#         }]
#
#     original = img.copy()
#
#     # --------------------------------------------------
#     # 2. Preprocessing
#     # --------------------------------------------------
#     gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
#     blurred = cv2.GaussianBlur(gray, (5, 5), 0)
#
#     # --------------------------------------------------
#     # 3. Edge detection
#     # --------------------------------------------------
#     edges = cv2.Canny(blurred, threshold1=50, threshold2=150)
#
#     h, w = edges.shape
#     edge_density = np.sum(edges > 0) / (h * w)
#
#     # --------------------------------------------------
#     # 4. Line detection (Hough Transform)
#     # --------------------------------------------------
#     lines = cv2.HoughLinesP(
#         edges,
#         rho=1,
#         theta=np.pi / 180,
#         threshold=100,
#         minLineLength=40,
#         maxLineGap=15
#     )
#
#     line_count = 0
#     if lines is not None:
#         line_count = len(lines)
#
#     # --------------------------------------------------
#     # 5. Rule + learned baseline comparison (AI-assisted)
#     # --------------------------------------------------
#     errors = []
#
#     if (
#         edge_density < GOOD_IMAGE_BASELINE["min_edge_density"]
#         or line_count < GOOD_IMAGE_BASELINE["min_line_count"]
#     ):
#         confidence = round(
#             1.0 - min(
#                 edge_density / GOOD_IMAGE_BASELINE["min_edge_density"],
#                 line_count / GOOD_IMAGE_BASELINE["min_line_count"],
#                 1.0
#             ),
#             2
#         )
#
#         errors.append({
#             "type": "missing_or_broken_roads",
#             "confidence": confidence,
#             "description": "Detected low road structure compared to trained baseline"
#         })
#
#     # --------------------------------------------------
#     # 6. Visualization (show WHERE the issue is)
#     # --------------------------------------------------
#     vis = original.copy()
#
#     if lines is not None:
#         xs, ys = [], []
#         for l in lines:
#             x1, y1, x2, y2 = l[0]
#             cv2.line(vis, (x1, y1), (x2, y2), (0, 255, 0), 2)
#             xs.extend([x1, x2])
#             ys.extend([y1, y2])
#
#         if errors:
#             min_x, max_x = min(xs), max(xs)
#             min_y, max_y = min(ys), max(ys)
#             cv2.rectangle(
#                 vis,
#                 (min_x, min_y),
#                 (max_x, max_y),
#                 (0, 0, 255),
#                 2
#             )
#
#     if errors:
#         cv2.putText(
#             vis,
#             "Missing / Broken Roads Detected",
#             (20, 40),
#             cv2.FONT_HERSHEY_SIMPLEX,
#             1,
#             (0, 0, 255),
#             2
#         )
#
#     # --------------------------------------------------
#     # 7. Save output
#     # --------------------------------------------------
#     out_name = f"image_{uuid.uuid4().hex}.png"
#     out_path = os.path.join(OUTPUT_DIR, out_name)
#     cv2.imwrite(out_path, vis)
#
#     return f"/outputs/{out_name}", errors

import cv2
import numpy as np
import pickle
import uuid
import os
from sklearn.ensemble import IsolationForest

# -------------------------------------------------------------------
# Config
# -------------------------------------------------------------------
OUTPUT_DIR = "backend/outputs"
BASELINE_PATH = "backend/image_baseline.pkl"
GOOD_IMAGE_DIR = "good_images"  # folder with baseline screenshots

os.makedirs(OUTPUT_DIR, exist_ok=True)


# --------------------------------------------------
# Feature Extraction
# --------------------------------------------------
def extract_image_features(img):
    # ---- Preprocess ----
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # ---- Edge Detection ----
    edges = cv2.Canny(blurred, 50, 150)
    h, w = edges.shape
    edge_density = np.sum(edges > 0) / (h * w)

    # ---- Line Detection ----
    lines = cv2.HoughLinesP(
        edges,
        rho=1,
        theta=np.pi / 180,
        threshold=50,
        minLineLength=40,
        maxLineGap=15
    )

    line_count = 0
    avg_line_len = 0.0
    orientations = []

    if lines is not None:
        line_count = len(lines)
        lengths = []
        for l in lines:
            x1, y1, x2, y2 = l[0]
            lengths.append(np.hypot(x2 - x1, y2 - y1))
            orientations.append(np.arctan2((y2 - y1), (x2 - x1)))
        avg_line_len = np.mean(lengths) if lengths else 0.0

    # ---- Connected Components (edges) ----
    num_labels, _, stats, _ = cv2.connectedComponentsWithStats(edges, connectivity=8)
    connected_components = num_labels - 1  # exclude background

    # ---- Coverage (rows & columns) ----
    row_coverage = np.mean(np.any(edges > 0, axis=1))
    col_coverage = np.mean(np.any(edges > 0, axis=0))

    # ---- Orientation Variance ----
    orientation_variance = float(np.var(orientations)) if orientations else 0.0

    return [
        edge_density,
        line_count,
        avg_line_len,
        orientation_variance,
        connected_components,
        row_coverage,
        col_coverage
    ]


# --------------------------------------------------
# Baseline Builder
# --------------------------------------------------
def build_baseline():
    """
    Read images from GOOD_IMAGE_DIR,
    compute features, then set:
      BASE_MEAN, BASE_STD, IF_MODEL
    and save to BASELINE_PATH
    """
    feature_list = []
    if not os.path.isdir(GOOD_IMAGE_DIR):
        return None, None, None

    for fname in os.listdir(GOOD_IMAGE_DIR):
        path = os.path.join(GOOD_IMAGE_DIR, fname)
        img = cv2.imread(path)
        if img is None:
            continue
        feature_list.append(extract_image_features(img))

    if not feature_list:
        return None, None, None

    X = np.array(feature_list)
    mean = X.mean(axis=0)
    std = X.std(axis=0)

    # train simple IsolationForest
    if_model = IsolationForest(n_estimators=100, contamination=0.1, random_state=42)
    if_model.fit(X)

    # save baseline
    baseline = {"mean": mean, "std": std, "if_model": if_model}
    try:
        with open(BASELINE_PATH, "wb") as f:
            pickle.dump(baseline, f)
    except:
        pass

    return mean, std, if_model


# --------------------------------------------------
# Load or build baseline once
# --------------------------------------------------
BASE_MEAN, BASE_STD, IF_MODEL = None, None, None

if os.path.exists(BASELINE_PATH):
    try:
        with open(BASELINE_PATH, "rb") as f:
            baseline = pickle.load(f)
            BASE_MEAN = baseline.get("mean")
            BASE_STD = baseline.get("std")
            IF_MODEL = baseline.get("if_model")
    except Exception as e:
        # failed to load -> rebuild
        BASE_MEAN, BASE_STD, IF_MODEL = build_baseline()
else:
    BASE_MEAN, BASE_STD, IF_MODEL = build_baseline()


# --------------------------------------------------
# Anomaly Detection Helpers
# --------------------------------------------------
ZSCORE_THRESHOLD = 3.0

FEATURE_NAMES = [
    "edge_density",
    "line_count",
    "avg_line_length",
    "orientation_variance",
    "connected_components",
    "row_coverage",
    "col_coverage"
]

def zscore_anomalies_vector(features):
    if BASE_MEAN is None or BASE_STD is None:
        return []

    features = np.array(features)
    z = np.abs((features - BASE_MEAN) / (BASE_STD + 1e-9))

    anomalies = []
    for idx, val in enumerate(z):
        feature_name = FEATURE_NAMES[idx]

        # if baseline std is very small, use % deviation
        if BASE_STD[idx] < 0.01:
            diff = abs(features[idx] - BASE_MEAN[idx])
            perc = diff / (BASE_MEAN[idx] + 1e-9)

            if perc > 0.2:  # 20% baseline deviation
                anomalies.append({
                    "type": "image_zscore_anomaly",
                    "feature": feature_name,
                    "severity": round(min(perc, 1.0), 2),
                    "description": f"{feature_name} deviates {round(perc*100,1)}% from baseline"
                })
        else:
            # normal z-score based detection
            if val > ZSCORE_THRESHOLD:
                severity = round(min(val / (ZSCORE_THRESHOLD * 2), 1.0), 2)
                anomalies.append({
                    "type": "image_zscore_anomaly",
                    "feature": feature_name,
                    "severity": severity,
                    "description": f"{feature_name} Z-score {round(float(val),2)}"
                })
    return anomalies


def isolation_forest_anomaly(features):
    if IF_MODEL is None:
        return []

    X = np.array(features).reshape(1, -1)
    pred = IF_MODEL.predict(X)

    if pred == -1:
        return [{
            "type": "image_ml_anomaly",
            "severity": 0.6,
            "description": "Isolation Forest flagged this image as unusual"
        }]
    return []


def detect_solid_patches(img):
    """
    Detects large solid/homogeneous regions that might be occlusions or anomalies.
    """
    # 1. Compute Gradient magnitude
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Sobel gradient
    grad_x = cv2.Sobel(gray, cv2.CV_16S, 1, 0, ksize=3)
    grad_y = cv2.Sobel(gray, cv2.CV_16S, 0, 1, ksize=3)
    abs_grad_x = cv2.convertScaleAbs(grad_x)
    abs_grad_y = cv2.convertScaleAbs(grad_y)
    grad = cv2.addWeighted(abs_grad_x, 0.5, abs_grad_y, 0.5, 0)

    # 2. Threshold: Low gradient = flat/solid area
    # We use a relatively high threshold (e.g., 20) to catch semi-flat areas too
    _, flat_mask = cv2.threshold(grad, 20, 255, cv2.THRESH_BINARY_INV)

    # 3. Clean up noise: Open then Close
    # Smaller kernel to allow smaller shapes (like the circle)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    clean_mask = cv2.morphologyEx(flat_mask, cv2.MORPH_OPEN, kernel)
    clean_mask = cv2.morphologyEx(clean_mask, cv2.MORPH_CLOSE, kernel)

    # 4. Connected Components
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(clean_mask, connectivity=8)

    h, w = img.shape[:2]
    total_area = h * w
    # Lower area threshold to 1% to catch the circle
    min_patch_area = total_area * 0.01  

    anomalies = []

    # 5. Analyze components (skip label 0 which is background/edges)
    for i in range(1, num_labels):
        area = stats[i, cv2.CC_STAT_AREA]
        
        if area > min_patch_area:
            # Check color: Map background is usually light/white.
            # If the patch is NOT white/light, it's an anomaly (like the blue box).
            
            # Create a mask for this component
            component_mask = (labels == i).astype(np.uint8) * 255
            mean_color = cv2.mean(img, mask=component_mask)[:3]
            
            # Simple heuristic: "Lightness"
            # If average brightness is low (< 220), it's dark -> Anomaly
            brightness = np.mean(mean_color)
            
            # Check saturation
            patch_color_px = np.uint8([[mean_color]])
            hsv_px = cv2.cvtColor(patch_color_px, cv2.COLOR_BGR2HSV)
            saturation = hsv_px[0][0][1]

            # White/Light Gray background usually has High Brightness OR Very Low Saturation
            is_white_bg = brightness > 225 and saturation < 30
            
            if not is_white_bg:
                x = stats[i, cv2.CC_STAT_LEFT]
                y = stats[i, cv2.CC_STAT_TOP]
                width = stats[i, cv2.CC_STAT_WIDTH]
                height = stats[i, cv2.CC_STAT_HEIGHT]
                
                anomalies.append({
                    "type": "visual_occlusion_patch",
                    "severity": 0.85,
                    "description": f"Solid patch detected (Area: {int(area)}px)",
                    "bbox": [int(x), int(y), int(width), int(height)]
                })

    return anomalies


# --------------------------------------------------
# MAIN ENTRY POINT for FastAPI
# --------------------------------------------------
async def run_image_qa(uploaded_file):
    # load image
    file_bytes = np.frombuffer(await uploaded_file.read(), np.uint8)
    img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

    if img is None:
        return None, [{
            "type": "invalid_image",
            "severity": 1.0,
            "description": "Uploaded file is not a valid image"
        }]

    # compute features
    features = extract_image_features(img)

    # anomaly detection
    errors = []
    errors.extend(zscore_anomalies_vector(features))
    errors.extend(isolation_forest_anomaly(features))

    # -------------------------------
    # EDGE DENSITY CHECK (Rendering Failure Detection - NEW)
    # -------------------------------
    edge_density = features[0]  # First feature is edge_density
    EDGE_DENSITY_THRESHOLD = 0.01  # 1% - Below this = likely blank/broken
    if edge_density < EDGE_DENSITY_THRESHOLD:
        errors.append({
            "type": "rendering_failure",
            "severity": 0.95,
            "description": f"Extremely low edge density ({edge_density:.4f}). Map likely blank or failed to render."
        })

    # -------------------------------
    # HEURISTIC: Solid Patch Detection
    # -------------------------------
    patch_errors = detect_solid_patches(img)
    errors.extend(patch_errors)

    # visualize
    vis = img.copy()
    
    # Draw patch errors specifically
    for e in patch_errors:
        if "bbox" in e:
            x, y, w, h = e["bbox"]
            cv2.rectangle(vis, (x, y), (x+w, y+h), (0, 165, 255), 3)  # Orange for patches
            cv2.putText(vis, "Occlusion", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 165, 255), 2)

    if errors:
        h, w, _ = vis.shape
        cv2.rectangle(vis, (0,0), (w-1,h-1), (0,0,255), 4)
        cv2.putText(
            vis,
            "Anomaly Detected",
            (30, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.2,
            (0, 0, 255),
            3
        )

    out_name = f"image_{uuid.uuid4().hex}.png"
    out_path = os.path.join(OUTPUT_DIR, out_name)
    cv2.imwrite(out_path, vis)

    return f"/outputs/{out_name}", errors
