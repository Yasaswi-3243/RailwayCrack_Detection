import { Link } from 'react-router-dom';

export default function Home() {
  return (
    <div className="container mx-auto px-4 py-12">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 items-center mb-16">
        <div className="bg-white rounded-lg shadow-2xl p-8">
          <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-6">
            Welcome to Rail Defect Detection
          </h1>
          <p className="text-xl text-gray-700 mb-8">
            Empowering railway safety with AI-powered defect detection. Upload rail images and let our advanced YOLO model identify potential defects instantly.
          </p>
          <Link
            to="/predict"
            className="btn-primary btn-lg inline-block"
          >
            Try Prediction
          </Link>
        </div>
        <div className="hidden md:block">
          <div className="w-full h-96 bg-gradient-to-br from-blue-400 to-purple-600 rounded-lg shadow-lg flex items-center justify-center">
            <div className="text-center text-white">
              <div className="text-6xl mb-4">🚂</div>
              <p className="text-2xl font-bold">Railway Safety</p>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        <div className="bg-white rounded-lg shadow-lg p-8 card-hover">
          <h5 className="text-xl font-bold text-gray-900 mb-4">Fast & Accurate</h5>
          <p className="text-gray-700">
            Our model leverages state-of-the-art YOLO technology for real-time, precise defect detection on rail tracks.
          </p>
        </div>
        
        <div className="bg-white rounded-lg shadow-lg p-8 card-hover">
          <h5 className="text-xl font-bold text-gray-900 mb-4">Easy to Use</h5>
          <p className="text-gray-700">
            Simply upload an image of your railway track. Our system instantly analyzes and highlights potential defects.
          </p>
        </div>
        
        <div className="bg-white rounded-lg shadow-lg p-8 card-hover">
          <h5 className="text-xl font-bold text-gray-900 mb-4">Detailed Results</h5>
          <p className="text-gray-700">
            Get comprehensive analysis with confidence scores, exact locations, and detailed annotations of detected defects.
          </p>
        </div>
      </div>

      <div className="mt-16 bg-white rounded-lg shadow-lg p-12 text-center">
        <h2 className="text-3xl font-bold text-gray-900 mb-6">Get Started Today</h2>
        <p className="text-lg text-gray-700 mb-8">
          Improve railway maintenance efficiency with our intelligent defect detection system.
        </p>
        <Link
          to="/predict"
          className="btn-primary inline-block"
        >
          Upload Your First Image
        </Link>
      </div>
    </div>
  );
}
