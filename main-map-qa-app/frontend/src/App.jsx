import { useState, useRef } from 'react';
import axios from 'axios';
import { Upload, FileText, AlertTriangle, Layers, Download, CheckCircle, Activity, Map as MapIcon, Image as ImageIcon } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from './components/ui/card';
import { Button } from './components/ui/button';
import MapViewer from './components/MapViewer';

function App() {
  const [file, setFile] = useState(null);
  const [mode, setMode] = useState('geometry');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [selectedErrorId, setSelectedErrorId] = useState(null);
  const [showBaseMap, setShowBaseMap] = useState(true);

  const handleUpload = async () => {
    if (!file) return;
    setLoading(true);
    setResult(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const endpoint = mode === 'image'
        ? 'http://localhost:8000/qa/image'
        : 'http://localhost:8000/qa/geometry';

      const res = await axios.post(endpoint, formData);
      setResult(res.data);
    } catch (err) {
      console.error(err);
      alert('Error running QA: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  const handleExport = () => {
    if (!result?.errors) return;
    const jsonString = `data:text/json;chatset=utf-8,${encodeURIComponent(
      JSON.stringify(result.errors, null, 2)
    )}`;
    const link = document.createElement("a");
    link.href = jsonString;
    link.download = "qa_report_errors.json";
    link.click();
  };

  const handleExportTxt = () => {
    if (!result?.errors) return;

    let textContent = `AXES SYSTEMS QA REPORT\n`;
    textContent += `======================\n`;
    textContent += `Date: ${new Date().toLocaleString()}\n`;
    textContent += `Mode: ${mode.toUpperCase()}\n`;
    textContent += `Total Issues: ${result.errors.length}\n\n`;

    result.errors.forEach((err, i) => {
      // ID & Type
      const id = err.id || `issue-${i + 1}`;
      const type = err.type || "Anomaly";

      textContent += `#${i + 1} [${id}]\n`;
      if (err.line_number) {
        textContent += `Line #: ${err.line_number}\n`;
      }
      textContent += `Type: ${type}\n`;

      // Location
      if (err.location) {
        textContent += `Location: ${err.location}\n`;
      }

    });

    const blob = new Blob([textContent], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "qa_report_errors.txt";
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="h-screen w-full flex flex-col bg-slate-50 text-slate-900">
      {/* Header */}
      <header className="h-14 border-b bg-white px-6 flex items-center justify-between shrink-0 z-10 shadow-sm">
        <div className="flex items-center gap-2 font-bold text-xl text-blue-600">
          <Activity className="h-6 w-6" />
          <span>Axes Systems QA</span>
        </div>
        <div className="text-sm text-slate-500">
          Masai Hackathon v1.0
        </div>
      </header>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">

        {/* Sidebar */}
        <aside className="w-80 bg-white border-r flex flex-col overflow-hidden shrink-0">
          <div className="p-4 border-b space-y-4">

            {/* Controls */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <label className="text-xs font-semibold uppercase tracking-wider text-slate-400">QA Mode</label>
                {/* Toggle Base Map */}
                {mode === 'geometry' && (
                  <button
                    onClick={() => setShowBaseMap(!showBaseMap)}
                    className={`text-xs px-2 py-0.5 rounded border transition-colors ${showBaseMap ? 'bg-blue-50 border-blue-200 text-blue-600' : 'bg-slate-50 border-slate-200 text-slate-400'}`}
                  >
                    {showBaseMap ? 'Hide Network' : 'Show Network'}
                  </button>
                )}
              </div>

              <div className="grid grid-cols-2 gap-2 bg-slate-100 p-1 rounded-lg">
                <button
                  onClick={() => setMode('geometry')}
                  className={`flex items-center justify-center gap-2 text-sm font-medium py-1.5 rounded-md transition-all ${mode === 'geometry' ? 'bg-white shadow text-blue-600' : 'text-slate-500 hover:bg-slate-200'}`}
                >
                  <MapIcon className="h-4 w-4" /> Geometry
                </button>
                <button
                  onClick={() => setMode('image')}
                  className={`flex items-center justify-center gap-2 text-sm font-medium py-1.5 rounded-md transition-all ${mode === 'image' ? 'bg-white shadow text-blue-600' : 'text-slate-500 hover:bg-slate-200'}`}
                >
                  <ImageIcon className="h-4 w-4" /> Image
                </button>
              </div>
            </div>

            {/* File Upload */}
            <div
              onClick={() => document.getElementById('file-upload').click()}
              className={`border-2 border-dashed rounded-xl p-6 flex flex-col items-center justify-center gap-2 transition-colors cursor-pointer ${file ? 'border-blue-200 bg-blue-50/50' : 'border-slate-200 hover:border-slate-300'}`}
            >
              <Upload className={`h-8 w-8 ${file ? 'text-blue-500' : 'text-slate-300'}`} />
              <input
                type="file"
                id="file-upload"
                className="hidden"
                onChange={(e) => setFile(e.target.files[0])}
              />
              <div className="text-sm font-medium text-center">
                {file ? <span className="text-blue-600">{file.name}</span> : <span className="text-slate-500">Click to upload file</span>}
              </div>
            </div>

            <Button onClick={handleUpload} disabled={!file || loading} className="w-full">
              {loading ? "Analyzing..." : "Run Analysis"}
            </Button>
          </div>

          {/* Results List */}
          <div className="flex-1 overflow-y-auto p-2">
            {!result && (
              <div className="text-center p-8 text-slate-400 text-sm">
                No results yet.<br />Upload a file to start.
              </div>
            )}

            {result && (
              <div className="space-y-2">
                <div className="flex items-center justify-between px-2 pb-2">
                  <span className="text-xs font-bold text-slate-400 uppercase">Issues Found ({result.errors.length})</span>
                  <div className="flex gap-1">
                    <Button variant="ghost" size="sm" onClick={handleExportTxt} className="h-6 text-xs gap-1">
                      <FileText className="h-3 w-3" /> TXT
                    </Button>
                    <Button variant="ghost" size="sm" onClick={handleExport} className="h-6 text-xs gap-1">
                      <Download className="h-3 w-3" /> JSON
                    </Button>
                  </div>
                </div>
                {result.errors.map((err, i) => (
                  <div
                    key={i}
                    onClick={() => setSelectedErrorId(err.geometry_index)}
                    className={`p-3 rounded-lg border text-sm cursor-pointer transition-colors ${selectedErrorId === err.geometry_index ? 'bg-blue-50 border-blue-200 shadow-sm' : 'bg-white border-transparent hover:bg-slate-50 hover:border-slate-200 change-this-border'}`}
                  >
                    <div className="flex items-start gap-2">
                      <AlertTriangle className="h-4 w-4 text-amber-500 mt-0.5 shrink-0" />
                      <div>
                        <div className="font-semibold text-slate-700">{err.type.replace(/_/g, ' ')}</div>
                        <div className="text-slate-500 text-xs mt-1">{err.description}</div>
                        {err.line_number && <div className="text-xs font-mono text-blue-600 font-bold mt-1">Line #{err.line_number}</div>}
                        {err.severity && <div className="mt-2 text-xs font-mono bg-slate-100 inline-block px-1.5 py-0.5 rounded text-slate-500">sev: {err.severity}</div>}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </aside>

        {/* Main View Area */}
        <main className="flex-1 bg-slate-100 flex flex-col min-w-0">
          {result && (
            <>
              {mode === 'geometry' ? (
                <div className="flex-1 relative">
                  {/* Map */}
                  <div className="absolute inset-0">
                    <MapViewer
                      errors={result.errors}
                      highlightedErrorId={selectedErrorId}
                      collectionWkt={result.collection_wkt}
                      showBaseMap={showBaseMap}
                    />
                  </div>
                </div>
              ) : (
                <div className="flex-1 flex items-center justify-center p-8 overflow-auto">
                  {/* Image View */}
                  <div className="bg-white p-2 shadow-lg rounded-lg border">
                    <img
                      src={`http://localhost:8000${result.output_url}`}
                      alt="Analysis Output"
                      className="max-w-full h-auto rounded"
                    />
                  </div>
                </div>
              )}

              {/* Static Report Toggle / View (Overlay or Bottom) */}
              {mode === 'geometry' && (
                <div className="absolute bottom-6 right-6 z-[400]">
                  <Card className="w-64 shadow-xl">
                    <CardHeader className="p-3 pb-0">
                      <CardTitle className="text-sm">Static Report</CardTitle>
                    </CardHeader>
                    <CardContent className="p-3">
                      <div className="relative group cursor-pointer aspect-square bg-slate-100 rounded overflow-hidden border">
                        <img
                          src={`http://localhost:8000${result.output_url}`}
                          alt="Report Thumbnail"
                          className="w-full h-full object-cover"
                        />
                        <div className="absolute inset-0 bg-black/50 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                          <a href={`http://localhost:8000${result.output_url}`} target="_blank" className="text-white text-xs font-bold underline">Open Full</a>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </div>
              )}
            </>
          )}

          {!result && (
            <div className="flex-1 flex flex-col items-center justify-center text-slate-300">
              <Layers className="h-16 w-16 mb-4" />
              <div className="text-xl font-light">Ready for Analysis</div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}

export default App;
