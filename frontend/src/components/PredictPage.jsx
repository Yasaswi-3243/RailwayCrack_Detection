import { useEffect, useMemo, useRef, useState } from 'react';

const ALLOWED_FORMATS = ['jpg', 'jpeg', 'png', 'webp'];

function severityClass(severity) {
  if (severity === 'Critical') return 'bg-red-100';
  if (severity === 'Moderate') return 'bg-yellow-100';
  return 'bg-sky-100';
}

export default function PredictPage() {
  const [file, setFile] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [selectedBox, setSelectedBox] = useState(null);

  const outputImgRef = useRef(null);
  const canvasRef = useRef(null);

  const detections = useMemo(() => (result?.detections ? result.detections : []), [result]);

  const drawDetections = (filterBoxNumber = null) => {
    const img = outputImgRef.current;
    const canvas = canvasRef.current;
    if (!img || !canvas || !img.naturalWidth) return;

    canvas.width = img.clientWidth;
    canvas.height = img.clientHeight;

    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    const scaleX = canvas.width / img.naturalWidth;
    const scaleY = canvas.height / img.naturalHeight;

    detections.forEach((d) => {
      if (filterBoxNumber && d.box_number !== filterBoxNumber) return;
      const [x1, y1, x2, y2] = d.box;
      const sx1 = x1 * scaleX;
      const sy1 = y1 * scaleY;
      const sx2 = x2 * scaleX;
      const sy2 = y2 * scaleY;
      const w = sx2 - sx1;
      const h = sy2 - sy1;

      ctx.lineWidth = Math.max(2, canvas.width / 400);
      ctx.strokeStyle = d.color || '#ffff00';
      ctx.strokeRect(sx1, sy1, w, h);

      const label = `Box ${d.box_number}: ${d.crack_type} (${(d.confidence * 100).toFixed(1)}%)`;
      ctx.font = `${Math.max(12, canvas.width / 60)}px Arial`;
      const textW = ctx.measureText(label).width + 8;
      const textH = Math.max(18, canvas.width / 60 + 6);
      const ty = Math.max(0, sy1 - textH - 2);
      ctx.fillStyle = d.color || '#ffff00';
      ctx.fillRect(sx1, ty, textW, textH);
      ctx.fillStyle = '#000';
      ctx.fillText(label, sx1 + 4, ty + textH - 6);
    });
  };

  useEffect(() => {
    drawDetections(selectedBox);
    const onResize = () => drawDetections(selectedBox);
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, [detections, selectedBox]);

  const onFileChange = (e) => {
    const picked = e.target.files?.[0];
    if (!picked) return;

    const ext = picked.name.split('.').pop().toLowerCase();
    if (!ALLOWED_FORMATS.includes(ext)) {
      setError('The uploaded image format is not supported. Please upload a JPG, PNG, or WebP file.');
      setFile(null);
      return;
    }

    setError('');
    setFile(picked);
  };

  const onSubmit = async (e) => {
    e.preventDefault();
    if (!file) {
      setError('Please select an image file to upload.');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const formData = new FormData();
      formData.append('image', file);
      const res = await fetch('/api/predict', { method: 'POST', body: formData });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.error || 'Prediction failed.');
      }
      setResult(data);
      setSelectedBox(null);
    } catch (err) {
      setError(err.message || 'Prediction failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto max-w-7xl px-4 py-10">
      {error ? (
        <div className="mx-auto mb-4 max-w-4xl rounded border border-red-400 bg-red-100 px-4 py-3 text-red-700">{error}</div>
      ) : null}

      <div className="mx-auto max-w-4xl">
        <div className="card-custom card-hover mb-4 p-6 shadow-lg">
          <h2 className="card-title-custom mb-3 text-3xl">Rail Defect Prediction</h2>
          <form onSubmit={onSubmit}>
            <div className="mb-3">
              <label htmlFor="image" className="mb-2 block text-slate-800">
                Upload Rail Track Image
              </label>
              <input
                className="block w-full rounded border border-slate-300 bg-white px-3 py-2"
                type="file"
                id="image"
                name="image"
                accept="image/*"
                onChange={onFileChange}
                required
              />
              <div className="mt-1 text-sm text-slate-500">Accepted formats: JPG, PNG, WebP</div>
            </div>
            <button type="submit" className="btn-primary-custom rounded px-4 py-2 text-white" disabled={loading}>
              {loading ? 'Predicting...' : 'Predict'}
            </button>
          </form>
        </div>
      </div>

      {result ? (
        <>
          <div className="mt-4 grid grid-cols-1 justify-center gap-6 md:grid-cols-2">
            <div className="card-custom p-4 text-center shadow">
              <h5 className="card-title-custom mb-3 text-xl">Original Image</h5>
              <div className="predict-img-wrap">
                <img
                  src={`${result.original_url}?t=${result.timestamp}`}
                  className="predict-img"
                  alt="Original Rail Image"
                />
              </div>
            </div>
            <div className="card-custom p-4 text-center shadow">
              <h5 className="card-title-custom mb-3 text-xl">Prediction Output</h5>
              <div className="predict-img-wrap" onClick={() => setSelectedBox(null)}>
                <img
                  ref={outputImgRef}
                  src={`${result.original_url}?t=${result.timestamp}`}
                  className="predict-img"
                  alt="Prediction Output"
                  onLoad={() => drawDetections(selectedBox)}
                />
                <canvas ref={canvasRef} className="overlay-canvas" />
              </div>
            </div>
          </div>

          {detections.length ? (
            <div className="mt-4">
              <div className="card-custom card-hover p-4 shadow">
                <h5 className="card-title-custom mb-3 text-xl">Detections</h5>
                <div className="overflow-x-auto">
                  <table className="min-w-full border border-slate-300 text-left text-sm">
                    <thead className="bg-slate-100">
                      <tr>
                        <th className="px-3 py-2">Box #</th>
                        <th className="px-3 py-2">Crack Type</th>
                        <th className="px-3 py-2">Severity</th>
                        <th className="px-3 py-2">Danger Level</th>
                        <th className="px-3 py-2">Confidence</th>
                        <th className="px-3 py-2">Size (L×W px)</th>
                        <th className="px-3 py-2">% of Image</th>
                      </tr>
                    </thead>
                    <tbody>
                      {detections.map((d) => (
                        <tr
                          key={d.box_number}
                          className={`${severityClass(d.severity)} cursor-pointer ${selectedBox === d.box_number ? 'ring-1 ring-slate-700' : ''}`}
                          onClick={() => setSelectedBox(d.box_number)}
                        >
                          <td className="px-3 py-2 font-semibold">{d.box_number}</td>
                          <td className="px-3 py-2 font-semibold">{d.crack_type}</td>
                          <td className="px-3 py-2">{d.severity}</td>
                          <td className="px-3 py-2">{d.danger_level}</td>
                          <td className="px-3 py-2">{(d.confidence * 100).toFixed(1)}%</td>
                          <td className="px-3 py-2">{d.length_px} × {d.width_px}</td>
                          <td className="px-3 py-2">{Number(d.relative_size).toFixed(2)}%</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          ) : (
            <div className="mt-4 rounded bg-green-100 p-4 text-green-900 shadow-sm">
              <strong>✓ No Cracks Detected</strong>
              <br />
              The rail section appears to be in good condition. No visible cracks or defects were found above the detection threshold.
            </div>
          )}
        </>
      ) : null}
    </div>
  );
}
