import { Link } from 'react-router-dom';

export default function Navbar() {
  return (
    <nav className="bg-gray-900 shadow-lg">
      <div className="container mx-auto px-4 py-4">
        <div className="flex justify-between items-center">
          <Link to="/" className="text-white text-xl font-bold">
            Rail Defect Detection
          </Link>
          <div className="hidden md:flex space-x-6">
            <Link to="/" className="text-gray-300 hover:text-white transition">
              Home
            </Link>
            <Link to="/about" className="text-gray-300 hover:text-white transition">
              About
            </Link>
            <Link to="/predict" className="text-gray-300 hover:text-white transition">
              Prediction
            </Link>
          </div>
        </div>
      </div>
    </nav>
  );
}
