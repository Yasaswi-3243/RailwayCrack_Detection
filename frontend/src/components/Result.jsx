import { useLocation, Link } from 'react-router-dom';

export default function Result() {
  const location = useLocation();
  const result = location.state?.result;

  if (!result) {
    return (
      <div className="container mx-auto px-4 py-12">
        <div className="bg-white rounded-lg shadow-lg p-8 text-center">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">No Results</h1>
          <p className="text-gray-700 mb-6">Please upload an image to see results.</p>
          <Link to="/predict" className="btn-primary inline-block">
            Go Back to Upload
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-12">
      <div className="max-w-4xl mx-auto">
        {/* Results Header */}
        <div className="mb-8 text-center">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">Analysis Results</h1>
          <p className="text-gray-600">
            {result.detections?.length || 0} defect(s) detected
          </p>
        </div>

        {/* Result Image */}
        {result.image && (
          <div className="mb-8 rounded-lg overflow-hidden shadow-2xl">
            <img
              src={`data:image/jpeg;base64,${result.image}`}
              alt="Result with annotations"
              className="w-full h-auto"
            />
          </div>
        )}

        {/* Detections Table */}
        {result.detections && result.detections.length > 0 ? (
          <div className="mb-8 bg-white rounded-lg shadow-lg overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-100 border-b-2 border-gray-300">
                  <tr>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Detection</th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Confidence</th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Location</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {result.detections.map((det, idx) => (
                    <tr key={idx} className="hover:bg-gray-50">
                      <td className="px-6 py-4 text-sm text-gray-900">
                        {det.class || 'Crack'}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-900">
                        <div className="flex items-center">
                          <div className="w-24 bg-gray-200 rounded-full h-2 mr-3">
                            <div
                              className="bg-blue-600 h-2 rounded-full"
                              style={{ width: `${(det.confidence || 0) * 100}%` }}
                            ></div>
                          </div>
                          <span className="font-semibold">
                            {((det.confidence || 0) * 100).toFixed(1)}%
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-600">
                        ({Math.round(det.x)}, {Math.round(det.y)})
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ) : (
          <div className="mb-8 bg-green-50 border border-green-200 rounded-lg p-8 text-center">
            <div className="text-5xl mb-4">✓</div>
            <h2 className="text-2xl font-bold text-green-900 mb-2">No Defects Detected</h2>
            <p className="text-green-700">The analyzed rail appears to be in good condition.</p>
          </div>
        )}

        {/* Summary Statistics */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow-lg p-6 text-center">
            <div className="text-3xl font-bold text-blue-600 mb-2">
              {result.detections?.length || 0}
            </div>
            <p className="text-gray-600">Defects Found</p>
          </div>
          
          <div className="bg-white rounded-lg shadow-lg p-6 text-center">
            <div className="text-3xl font-bold text-green-600 mb-2">
              {result.detections?.length === 0 ? '100' : '0'}%
            </div>
            <p className="text-gray-600">Good Condition</p>
          </div>
          
          <div className="bg-white rounded-lg shadow-lg p-6 text-center">
            <div className="text-3xl font-bold text-orange-600 mb-2">
              {result.analysis_time || 'N/A'}
            </div>
            <p className="text-gray-600">Processing Time</p>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex gap-4 justify-center">
          <Link to="/predict" className="btn-primary">
            Analyze Another Image
          </Link>
          <Link to="/" className="px-6 py-3 border-2 border-blue-600 text-blue-600 rounded-lg hover:bg-blue-50 font-semibold">
            Back to Home
          </Link>
        </div>
      </div>
    </div>
  );
}
