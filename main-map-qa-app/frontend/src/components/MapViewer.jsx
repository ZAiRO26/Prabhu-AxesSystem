import { MapContainer, TileLayer, Polyline, Tooltip, useMap, CircleMarker } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { useMemo, useEffect } from 'react';
import { parse } from 'wkt';

// Fix Leaflet icons
import icon from 'leaflet/dist/images/marker-icon.png';
import iconShadow from 'leaflet/dist/images/marker-shadow.png';

let DefaultIcon = L.icon({
    iconUrl: icon,
    shadowUrl: iconShadow,
    iconSize: [25, 41],
    iconAnchor: [12, 41]
});
L.Marker.prototype.options.icon = DefaultIcon;

// Component to fit bounds to the data
const BoundsFitter = ({ lines }) => {
    const map = useMap();
    useEffect(() => {
        if (lines.length > 0) {
            try {
                // Flatten to points
                const points = lines.flat();
                if (points.length > 0) {
                    const bounds = L.latLngBounds(points);
                    map.fitBounds(bounds, { padding: [50, 50], maxZoom: 18 });
                }
            } catch (e) {
                console.error("Bounds error", e);
            }
        }
    }, [lines, map]);
    return null;
};

export default function MapViewer({ errors, highlightedErrorId, collectionWkt, showBaseMap = true }) {

    // 1. Process Base Map (Clean Geometries)
    const baseLines = useMemo(() => {
        if (!collectionWkt || !showBaseMap) return [];
        return collectionWkt.map(wktStr => {
            try {
                const geojson = parse(wktStr);
                if (geojson && (geojson.type === 'LineString' || geojson.type === 'MultiLineString')) {
                    const coords = geojson.type === 'LineString' ? [geojson.coordinates] : geojson.coordinates;
                    // Y -> Lat, X -> Lng for Simple CRS
                    return coords.map(line => line.map(([x, y]) => [y, x]));
                }
            } catch (e) { }
            return null;
        }).filter(Boolean).flat();
    }, [collectionWkt, showBaseMap]);

    // 2. Process Errors (Lines and Points)
    const { errorLines, errorPoints } = useMemo(() => {
        const eLines = [];
        const ePoints = [];

        errors.forEach((err) => {
            if (!err.wkt) return;
            try {
                const geojson = parse(err.wkt);
                if (!geojson) return;

                const isHighlighted = err.geometry_index === highlightedErrorId;
                const color = '#ef4444'; // Red
                const opacity = isHighlighted ? 1 : 0.8;

                if (geojson.type === 'LineString' || geojson.type === 'MultiLineString') {
                    const coords = geojson.type === 'LineString'
                        ? [geojson.coordinates]
                        : geojson.coordinates;

                    const paths = coords.map(line => line.map(([x, y]) => [y, x]));
                    eLines.push({
                        paths, color,
                        weight: isHighlighted ? 6 : 4, opacity,
                        desc: err.description, id: err.id || err.geometry_index
                    });
                } else if (geojson.type === 'Point') {
                    // GeoJSON Point is [x, y] -> Leaflet [y, x]
                    const pos = [geojson.coordinates[1], geojson.coordinates[0]];
                    ePoints.push({
                        pos, color,
                        radius: isHighlighted ? 8 : 5,
                        weight: isHighlighted ? 3 : 2,
                        desc: err.description, id: err.id || err.geometry_index
                    });
                }
            } catch (e) { console.error(e); }
        });
        return { errorLines: eLines, errorPoints: ePoints };
    }, [errors, highlightedErrorId]);

    // Bounds Logic
    const allPathsFlattened = useMemo(() => {
        const linePts = [...baseLines.flat(), ...errorLines.flatMap(e => e.paths).flat()];
        const ptPts = errorPoints.map(e => e.pos);
        return [...linePts, ...ptPts];
    }, [baseLines, errorLines, errorPoints]);

    // Calculate Data Bounds for Scale Info
    const dataBounds = useMemo(() => {
        if (allPathsFlattened.length === 0) return null;
        let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;

        allPathsFlattened.forEach(([lat, lng]) => {
            if (lng < minX) minX = lng;
            if (lng > maxX) maxX = lng;
            if (lat < minY) minY = lat;
            if (lat > maxY) maxY = lat;
        });

        return {
            width: maxX - minX,
            height: maxY - minY,
        };
    }, [allPathsFlattened]);

    return (
        <MapContainer
            center={[0, 0]}
            zoom={2}
            style={{ height: '100%', width: '100%', background: '#f8fafc' }}
            crs={L.CRS.Simple}
            minZoom={-5}
        >
            {/* Bounds Fitter handles simple arrays of [lat, lng] */}
            {allPathsFlattened.length > 0 && <BoundsFitter lines={[allPathsFlattened]} />}

            {/* Base Map Layer */}
            {baseLines.map((paths, i) => (
                <Polyline
                    key={`base-${i}`}
                    positions={paths}
                    pathOptions={{ color: "#334155", weight: 2, opacity: 0.3 }}
                />
            ))}

            {/* Error Lines */}
            {errorLines.map((line, i) => (
                <Polyline
                    key={`err-line-${i}`}
                    positions={line.paths}
                    pathOptions={{ color: line.color, opacity: line.opacity, weight: line.weight }}
                >
                    <Tooltip sticky>
                        <div className="font-bold text-sm">{line.desc}</div>
                        <div className="text-xs text-muted-foreground">ID: {line.id}</div>
                    </Tooltip>
                </Polyline>
            ))}

            {/* Error Points (Dangles) */}
            {errorPoints.map((pt, i) => (
                <CircleMarker
                    key={`err-pt-${i}`}
                    center={pt.pos}
                    pathOptions={{ color: 'white', fillColor: pt.color, fillOpacity: 1, weight: pt.weight }}
                    radius={pt.radius}
                >
                    <Tooltip sticky>
                        <div className="font-bold text-sm">{pt.desc}</div>
                        <div className="text-xs text-muted-foreground">ID: {pt.id}</div>
                    </Tooltip>
                </CircleMarker>
            ))}

            {/* Scale / Info Overlay */}
            {dataBounds && (
                <div className="leaflet-bottom leaflet-left" style={{ pointerEvents: 'none', margin: '20px', zIndex: 1000 }}>
                    <div className="leaflet-control bg-white/95 p-3 rounded shadow-lg border border-slate-300 text-xs font-mono text-slate-700">
                        <div className="font-bold border-b border-slate-200 pb-1 mb-1 text-slate-900">Map Scale & Info</div>
                        <div className="grid grid-cols-2 gap-x-4 gap-y-1">
                            <span>Width:</span> <span className="font-bold">{dataBounds.width.toFixed(1)} units</span>
                            <span>Height:</span> <span className="font-bold">{dataBounds.height.toFixed(1)} units</span>
                        </div>
                        <div className="text-[10px] text-slate-500 mt-1 italic leading-tight">
                            *Units likely meters (based on CRS)
                        </div>
                    </div>
                </div>
            )}
        </MapContainer>
    );
}
