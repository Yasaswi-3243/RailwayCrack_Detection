export default function AboutPage() {
  return (
    <div className="mx-auto max-w-7xl px-4 py-10">
      <div className="mb-4 flex justify-center">
        <div className="w-full max-w-5xl about-section">
          <h2 className="card-title-custom mb-3 text-3xl">
            <i className="fa-solid fa-train-subway mr-2"></i>About Rail Defect Detection
          </h2>
          <p className="text-lg text-slate-700">
            Rail Defect Detection is an AI-powered web application designed to enhance railway safety by automating the detection of defects in rail tracks. Using advanced computer vision and deep learning techniques, our system helps railway operators identify potential hazards quickly and accurately, reducing the risk of accidents and improving maintenance efficiency.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
        <div className="about-card h-full p-6">
          <h5 className="card-title-custom mb-3 text-xl">
            <i className="fa-solid fa-bullseye mr-2"></i>Purpose
          </h5>
          <p className="text-slate-700">
            To provide a fast, reliable, and user-friendly tool for detecting rail defects, supporting proactive maintenance and accident prevention.
          </p>
        </div>
        <div className="about-card h-full p-6">
          <h5 className="card-title-custom mb-3 text-xl">
            <i className="fa-solid fa-microchip mr-2"></i>Technology Stack
          </h5>
          <ul className="list-disc pl-5 text-slate-700">
            <li>Flask (Python Web Framework)</li>
            <li>YOLO (You Only Look Once) Deep Learning Model</li>
            <li>Pillow (Image Processing)</li>
            <li>Tailwind CSS (Frontend Styling)</li>
          </ul>
        </div>
        <div className="about-card h-full p-6">
          <h5 className="card-title-custom mb-3 text-xl">
            <i className="fa-solid fa-users mr-2"></i>Our Team
          </h5>
          <p className="text-slate-700">
            A passionate group of AI enthusiasts and engineers dedicated to making railways safer through technology and innovation.
          </p>
        </div>
      </div>
    </div>
  );
}
