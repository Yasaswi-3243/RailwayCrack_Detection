import { Link } from 'react-router-dom';

export default function HomePage() {
  return (
    <div className="mx-auto max-w-7xl px-4 py-10">
      <div className="mx-auto mb-4 grid max-w-4xl grid-cols-1">
        <div className="card-custom card-hover mb-4 p-8 text-center shadow-lg">
          <h1 className="card-title-custom mb-3 text-5xl">Welcome to Rail Defect Detection</h1>
          <p className="text-lg text-slate-700">
            Empowering railway safety with AI-powered defect detection. Upload rail images and let our advanced YOLO model identify potential defects instantly.
          </p>
          <Link to="/predict" className="btn-primary-custom mt-4 inline-block rounded-md px-6 py-3 text-white">
            Try Prediction
          </Link>
        </div>
      </div>

      <div className="mt-4 grid grid-cols-1 gap-6 md:grid-cols-3">
        <div className="card-custom card-hover p-6 shadow">
          <h5 className="card-title-custom mb-2 text-xl">Fast & Accurate</h5>
          <p className="text-slate-700">
            Our model leverages state-of-the-art YOLO technology for real-time, precise defect detection on rail tracks.
          </p>
        </div>
        <div className="card-custom card-hover p-6 shadow">
          <h5 className="card-title-custom mb-2 text-xl">Easy to Use</h5>
          <p className="text-slate-700">
            Simply upload an image of a rail track and get instant results with highlighted defects and confidence scores.
          </p>
        </div>
        <div className="card-custom card-hover p-6 shadow">
          <h5 className="card-title-custom mb-2 text-xl">Enhancing Safety</h5>
          <p className="text-slate-700">
            Automated defect detection helps prevent accidents, reduces manual inspection time, and ensures safer railways.
          </p>
        </div>
      </div>
    </div>
  );
}
