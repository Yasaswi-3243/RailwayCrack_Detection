import { NavLink, Route, Routes } from 'react-router-dom';
import HomePage from './components/HomePage';
import AboutPage from './components/AboutPage';
import PredictPage from './components/PredictPage';

function Navbar() {
  const linkClass = ({ isActive }) =>
    `px-3 py-2 text-white/90 hover:text-white ${isActive ? 'font-semibold underline underline-offset-4' : ''}`;

  return (
    <nav className="navbar-custom shadow-md">
      <div className="mx-auto flex w-full max-w-7xl items-center justify-between px-4 py-4">
        <NavLink to="/" className="text-xl font-semibold text-white">
          Rail Defect Detection
        </NavLink>
        <div className="flex items-center gap-1">
          <NavLink to="/" className={linkClass}>
            Home
          </NavLink>
          <NavLink to="/about" className={linkClass}>
            About
          </NavLink>
          <NavLink to="/predict" className={linkClass}>
            Prediction
          </NavLink>
        </div>
      </div>
    </nav>
  );
}

export default function App() {
  return (
    <div className="bg-rail min-h-screen">
      <Navbar />
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/about" element={<AboutPage />} />
        <Route path="/predict" element={<PredictPage />} />
      </Routes>
    </div>
  );
}
