"""
Fix Engine: Manages geometry state and applies robust fixes.
Handles in-memory modification of geometries and export.
"""
import shapely.wkt
from shapely.geometry import LineString, Point, MultiLineString
from shapely.ops import snap, linemerge
import copy
from typing import List, Dict, Any, Optional

class GeometryFixEngine:
    def __init__(self):
        self.original_geometries = []  # List of Shapely geometries
        self.current_geometries = []   # Modified list
        self.applied_fixes = []        # Log of fixes applied
        self.spatial_index = None      # For faster lookups (optional)

    def load_wkt_content(self, wkt_content: str):
        """Load WKT content into memory (matching geometry_qa.py parsing exactly)."""
        try:
            self.original_geometries = []
            self.current_geometries = []
            self.applied_fixes = []
            
            # EXACT COPY of geometry_qa.py parsing logic
            buf = ""
            raw_lines = wkt_content.splitlines()
            
            for i, line_str in enumerate(raw_lines):
                stripped = line_str.strip()
                if not stripped: 
                    continue
                
                buf += stripped + " "
                
                if stripped.endswith(")"):
                    try:
                        clean_wkt = buf.split(";")[-1]
                        geom = shapely.wkt.loads(clean_wkt)
                        if geom and not geom.is_empty:
                            self.original_geometries.append(geom)
                    except Exception:
                        # Append None to maintain index alignment
                        self.original_geometries.append(None)
                    buf = ""
            
            # Deep copy for modification
            self.current_geometries = copy.deepcopy(self.original_geometries)
            
            print(f"[FixEngine] Loaded {len(self.current_geometries)} geometries")
            return len(self.current_geometries)
        except Exception as e:
            print(f"Error loading WKT: {e}")
            return 0

    def get_geometry(self, index: int) -> Optional[Any]:
        if 0 <= index < len(self.current_geometries):
            return self.current_geometries[index]
        return None

    def apply_fix(self, error_id: str, fix_type: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Apply a robust fix based on the strategy type.
        """
        try:
            # Extract index from error_id (e.g., "dangle-5" -> 5)
            # Assuming error_id format is "type-index" or just "index"
            parts = error_id.split('-')
            
            # Find the integer part which is the index
            idx = -1
            for p in parts:
                if p.isdigit():
                    idx = int(p)
                    break
            
            if idx == -1 or idx >= len(self.current_geometries):
                return {"success": False, "message": f"Invalid geometry index: {idx}"}

            geom = self.current_geometries[idx]
            original_wkt = geom.wkt
            
            fix_result = None
            
            # --------------------------------------------------
            # STRATEGY: SNAP (Dangle Fix)
            # --------------------------------------------------
            if fix_type.upper() == "SNAP":
                tolerance = params.get("tolerance", 0.5) if params else 0.5
                # Find nearest geometry to snap to
                best_snap = None
                min_dist = float('inf')
                
                # Check all other geometries
                for i, other in enumerate(self.current_geometries):
                    if i == idx: continue
                    dist = geom.distance(other)
                    if dist < min_dist and dist < tolerance:
                        min_dist = dist
                        best_snap = other
                
                if best_snap:
                    # Apply Snap
                    snapped_geom = snap(geom, best_snap, tolerance)
                    self.current_geometries[idx] = snapped_geom
                    fix_result = f"Snapped to nearest geometry (dist: {min_dist:.4f})"
                else:
                    return {"success": False, "message": "No geometry found within snap tolerance"}

            # --------------------------------------------------
            # STRATEGY: DELETE (Short Line Fix)
            # --------------------------------------------------
            elif fix_type.upper() == "DELETE":
                # Mark as None/Deleted
                self.current_geometries[idx] = None 
                fix_result = "Deleted geometry"

            # --------------------------------------------------
            # STRATEGY: SIMPLIFY (Curvature/Anomaly Fix)
            # --------------------------------------------------
            elif fix_type.upper() == "SIMPLIFY":
                tolerance = params.get("tolerance", 0.5) if params else 0.5
                simplified = geom.simplify(tolerance, preserve_topology=True)
                self.current_geometries[idx] = simplified
                fix_result = f"Simplified geometry (tolerance: {tolerance})"

            # --------------------------------------------------
            # STRATEGY: BUFFER (Self-intersection Fix)
            # --------------------------------------------------
            elif fix_type.upper() == "BUFFER":
                # buffer(0) is a classic trick to fix self-intersections
                buffered = geom.buffer(0)
                self.current_geometries[idx] = buffered
                fix_result = "Applied buffer(0) to fix self-intersection"

            # --------------------------------------------------
            # STRATEGY: MAKE_VALID (Universal Invalid Geometry Fix)
            # --------------------------------------------------
            elif fix_type.upper() == "MAKE_VALID":
                from shapely.validation import make_valid
                valid_geom = make_valid(geom)
                self.current_geometries[idx] = valid_geom
                fix_result = "Applied make_valid() to repair geometry"

            # --------------------------------------------------
            # STRATEGY: CLOSE (Unclosed Ring Fix for Polygons)
            # --------------------------------------------------
            elif fix_type.upper() == "CLOSE":
                if geom.geom_type in ['Polygon', 'LinearRing']:
                    # Already closed by definition in Shapely
                    fix_result = "Ring already closed"
                elif geom.geom_type == 'LineString':
                    coords = list(geom.coords)
                    if coords[0] != coords[-1]:
                        coords.append(coords[0])
                        closed_ring = LineString(coords)
                        self.current_geometries[idx] = closed_ring
                        fix_result = "Closed the ring by connecting end to start"
                    else:
                        fix_result = "Ring already closed"
                else:
                    fix_result = "Close not applicable to this geometry type"

            # --------------------------------------------------
            # STRATEGY: REVERSE (Winding Order Fix)
            # --------------------------------------------------
            elif fix_type.upper() == "REVERSE":
                from shapely.geometry import LinearRing, Polygon as ShapelyPolygon
                if geom.geom_type == 'Polygon':
                    # Reverse exterior ring
                    ext = LinearRing(list(geom.exterior.coords)[::-1])
                    ints = [LinearRing(list(r.coords)[::-1]) for r in geom.interiors]
                    reversed_poly = ShapelyPolygon(ext, ints)
                    self.current_geometries[idx] = reversed_poly
                    fix_result = "Reversed winding order"
                elif geom.geom_type == 'LineString':
                    reversed_line = LineString(list(geom.coords)[::-1])
                    self.current_geometries[idx] = reversed_line
                    fix_result = "Reversed coordinate order"
                else:
                    fix_result = "Reverse not applicable"

            # --------------------------------------------------
            # STRATEGY: DENSIFY (Add Points to Sparse Geometry)
            # --------------------------------------------------
            elif fix_type.upper() == "DENSIFY":
                from shapely.ops import substring
                if geom.geom_type == 'LineString':
                    # Add points every 1 unit
                    interval = params.get("interval", 1.0) if params else 1.0
                    length = geom.length
                    num_points = max(int(length / interval), 2)
                    points = [geom.interpolate(i * interval) for i in range(num_points + 1)]
                    densified = LineString([(p.x, p.y) for p in points])
                    self.current_geometries[idx] = densified
                    fix_result = f"Densified with {num_points} points"
                else:
                    fix_result = "Densify not applicable to this geometry type"

            # --------------------------------------------------
            # STRATEGY: OTHER (Mark as Reviewed)
            # --------------------------------------------------
            elif fix_type.upper() == "OTHER":
                # Don't modify geometry, just log as reviewed
                fix_result = "Marked as reviewed (no auto-fix available)"

            else:
                return {"success": False, "message": f"Unknown fix type: {fix_type}"}

            # Log the fix
            if fix_result:
                self.applied_fixes.append({
                    "error_id": error_id,
                    "fix_type": fix_type,
                    "original": original_wkt,
                    "result": fix_result,
                    "timestamp": "now"
                })
                return {"success": True, "message": fix_result}
            
        except Exception as e:
            return {"success": False, "message": str(e)}

    def export_fixed_wkt(self) -> str:
        """Export current valid geometries as WKT."""
        valid_geoms = [g for g in self.current_geometries if g is not None and not g.is_empty]
        if not valid_geoms:
            return ""
        
        if len(valid_geoms) == 1:
            return valid_geoms[0].wkt
        
        collection = MultiLineString(valid_geoms)
        return collection.wkt

    def export_report(self) -> str:
        """Generate a text report of applied fixes."""
        report = "AXES SYSTEMS - AI FIX REPORT\n"
        report += "============================\n\n"
        report += f"Total Objects processed: {len(self.original_geometries)}\n"
        report += f"Total Fixes Applied: {len(self.applied_fixes)}\n\n"
        
        for i, fix in enumerate(self.applied_fixes, 1):
            report += f"FIX #{i}\n"
            report += f"Error ID: {fix['error_id']}\n"
            report += f"Type: {fix['fix_type']}\n"
            report += f"Action: {fix['result']}\n"
            report += "-" * 30 + "\n"
            
        return report

# Singleton
_engine = GeometryFixEngine()
def get_fix_engine():
    return _engine
