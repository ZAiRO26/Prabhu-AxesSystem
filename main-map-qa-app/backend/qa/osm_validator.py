"""
OSM Validator: Query OpenStreetMap to validate local geometry errors against real-world data.
Uses Overpass API to check if roads exist in the error locations.
"""
import os
from typing import Dict, Any, Optional, Tuple
from shapely.geometry import Point

# Try to import overpy, fail gracefully if not available
try:
    import overpy
    OVERPY_AVAILABLE = True
except ImportError:
    OVERPY_AVAILABLE = False
    overpy = None

# --------------------------------------------------
# OSM Validator Class
# --------------------------------------------------
class OSMValidator:
    """
    Validates geometry errors against OpenStreetMap data.
    Helps distinguish true errors from false positives.
    """
    
    def __init__(self):
        self.api = overpy.Overpass() if OVERPY_AVAILABLE else None
    
    def query_roads_near_point(
        self, 
        x: float, 
        y: float, 
        radius_meters: float = 50.0,
        is_cartesian: bool = True
    ) -> Dict[str, Any]:
        """
        Query OSM for roads near a given point.
        
        Args:
            x, y: Coordinates (can be Cartesian or Lat/Lng)
            radius_meters: Search radius
            is_cartesian: If True, coordinates are local Cartesian (non-geographic).
                         In this case, we cannot query OSM directly.
        
        Returns:
            Dict with 'roads_found', 'road_count', and 'confidence' keys.
        """
        if not OVERPY_AVAILABLE or self.api is None:
            return {
                "status": "unavailable",
                "message": "OSM validation unavailable (overpy not installed)",
                "confidence": "UNKNOWN"
            }
        
        if is_cartesian:
            # For Cartesian coordinates, we can't directly query OSM
            # This would require a coordinate transformation (e.g., EPSG:4326)
            return {
                "status": "skip",
                "message": "Cartesian coordinates detected. OSM validation requires Lat/Lng.",
                "confidence": "UNKNOWN",
                "suggestion": "Transform to WGS84 for OSM validation"
            }
        
        # Assume y = lat, x = lng for geographic coordinates
        lat, lng = y, x
        
        try:
            # Build Overpass query for highways within radius
            query = f"""
            [out:json];
            way["highway"](around:{radius_meters},{lat},{lng});
            out geom;
            """
            
            result = self.api.query(query)
            road_count = len(result.ways)
            
            if road_count > 0:
                # Roads exist in OSM near this point
                road_names = [way.tags.get("name", "Unnamed") for way in result.ways[:3]]
                return {
                    "status": "found",
                    "road_count": road_count,
                    "road_names": road_names,
                    "confidence": "HIGH",
                    "message": f"OSM shows {road_count} road(s) near this point. Error likely VALID."
                }
            else:
                # No roads in OSM - might be a false positive (dead end)
                return {
                    "status": "not_found",
                    "road_count": 0,
                    "confidence": "LOW",
                    "message": "OSM shows no roads here. Error might be a FALSE POSITIVE (valid dead-end)."
                }
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"OSM query failed: {str(e)}",
                "confidence": "UNKNOWN"
            }
    
    def validate_dangle_error(
        self, 
        error: Dict[str, Any],
        is_cartesian: bool = True
    ) -> Dict[str, Any]:
        """
        Validate a dangle error against OSM.
        
        Args:
            error: The error dict from geometry_qa
            is_cartesian: Whether coordinates are Cartesian (local) or geographic
        
        Returns:
            Validation result with confidence assessment
        """
        # Extract coordinates from error
        location = error.get("location", "")
        if not location:
            return {"status": "skip", "message": "No location data in error"}
        
        try:
            parts = location.split(",")
            x = float(parts[0].strip())
            y = float(parts[1].strip())
        except:
            return {"status": "skip", "message": "Could not parse location"}
        
        osm_result = self.query_roads_near_point(x, y, is_cartesian=is_cartesian)
        
        # Enhance error with OSM validation
        return {
            "error_id": error.get("id"),
            "error_type": error.get("type"),
            "osm_validation": osm_result,
            "final_confidence": osm_result.get("confidence", "UNKNOWN")
        }


# --------------------------------------------------
# Coordinate Detection (Heuristic)
# --------------------------------------------------
def detect_coordinate_system(lines_data: list) -> str:
    """
    Heuristic to detect if coordinates are geographic (Lat/Lng) or Cartesian.
    
    Geographic: lat in [-90, 90], lng in [-180, 180]
    Cartesian: Usually larger values like meters (e.g., 7000, 8000)
    """
    if not lines_data:
        return "unknown"
    
    sample_coords = []
    for item in lines_data[:5]:  # Check first 5 geometries
        geom = item.get("geom")
        if geom and hasattr(geom, 'coords'):
            try:
                coords = list(geom.coords)
                if coords:
                    sample_coords.extend(coords[:2])
            except:
                pass
    
    if not sample_coords:
        return "unknown"
    
    xs = [c[0] for c in sample_coords]
    ys = [c[1] for c in sample_coords]
    
    # Check if values are within geographic ranges
    x_in_range = all(-180 <= x <= 180 for x in xs)
    y_in_range = all(-90 <= y <= 90 for y in ys)
    
    if x_in_range and y_in_range:
        return "geographic"
    else:
        return "cartesian"


# --------------------------------------------------
# Singleton Instance
# --------------------------------------------------
_validator_instance = None

def get_osm_validator() -> OSMValidator:
    """Get or create the OSM validator singleton."""
    global _validator_instance
    if _validator_instance is None:
        _validator_instance = OSMValidator()
    return _validator_instance
