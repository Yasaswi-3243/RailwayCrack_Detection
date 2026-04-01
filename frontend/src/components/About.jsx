import { Link } from 'react-router-dom';

export default function About() {
  return (
    <div className="container mx-auto px-4 py-12">
      <div className="max-w-4xl mx-auto">
        <div className="bg-white rounded-lg shadow-2xl p-12 mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-6 text-center">
            About Rail Defect Detection
          </h1>

          <div className="prose prose-lg max-w-none space-y-6">
            <section>
              <h2 className="text-2xl font-bold text-gray-900 mb-4">Our Mission</h2>
              <p className="text-gray-700">
                We are committed to improving railway safety through advanced artificial intelligence. 
                Our Rail Defect Detection system leverages cutting-edge computer vision technology to 
                identify potential defects on railway tracks with unprecedented accuracy and speed.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-gray-900 mb-4">How It Works</h2>
              <p className="text-gray-700 mb-4">
                Our system uses the YOLO (You Only Look Once) neural network architecture, one of the 
                most advanced object detection models available:
              </p>
              <ul className="list-disc list-inside space-y-2 text-gray-700">
                <li>Upload a high-quality image of railway tracks</li>
                <li>Our AI model analyzes the image in real-time</li>
                <li>Detects and localizes cracks and other defects</li>
                <li>Provides confidence scores for each detection</li>
                <li>Generates detailed visual annotations</li>
              </ul>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-gray-900 mb-4">Key Features</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-4">
                <div className="bg-blue-50 p-4 rounded-lg">
                  <h3 className="font-semibold text-blue-900 mb-2">🎯 High Accuracy</h3>
                  <p className="text-blue-800 text-sm">
                    Advanced neural networks trained on thousands of railway images ensure reliable detection.
                  </p>
                </div>
                
                <div className="bg-green-50 p-4 rounded-lg">
                  <h3 className="font-semibold text-green-900 mb-2">⚡ Real-Time Processing</h3>
                  <p className="text-green-800 text-sm">
                    Instant analysis with processing times under 5 seconds per image.
                  </p>
                </div>
                
                <div className="bg-orange-50 p-4 rounded-lg">
                  <h3 className="font-semibold text-orange-900 mb-2">📊 Detailed Analytics</h3>
                  <p className="text-orange-800 text-sm">
                    Get comprehensive reports with precise coordinates and confidence metrics.
                  </p>
                </div>
                
                <div className="bg-purple-50 p-4 rounded-lg">
                  <h3 className="font-semibold text-purple-900 mb-2">🔄 Continuous Improvement</h3>
                  <p className="text-purple-800 text-sm">
                    Our model is regularly updated with new training data for better accuracy.
                  </p>
                </div>
              </div>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-gray-900 mb-4">Technical Specifications</h2>
              <div className="bg-gray-50 p-6 rounded-lg">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <h3 className="font-semibold text-gray-900 mb-2">Model Architecture</h3>
                    <p className="text-gray-700">YOLO v8 (You Only Look Once v8)</p>
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900 mb-2">Input Formats</h3>
                    <p className="text-gray-700">JPG, PNG, BMP, WEBP</p>
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900 mb-2">Detection Classes</h3>
                    <p className="text-gray-700">Railway Cracks, Surface Defects</p>
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900 mb-2">Processing Speed</h3>
                    <p className="text-gray-700">~2-5 seconds per image</p>
                  </div>
                </div>
              </div>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-gray-900 mb-4">Why Choose Us</h2>
              <ul className="space-y-3 text-gray-700">
                <li className="flex items-start">
                  <span className="text-blue-600 mr-3 text-xl">✓</span>
                  <span>Industry-leading accuracy and reliability</span>
                </li>
                <li className="flex items-start">
                  <span className="text-blue-600 mr-3 text-xl">✓</span>
                  <span>User-friendly interface requires no technical expertise</span>
                </li>
                <li className="flex items-start">
                  <span className="text-blue-600 mr-3 text-xl">✓</span>
                  <span>Reduces manual inspection time and costs</span>
                </li>
                <li className="flex items-start">
                  <span className="text-blue-600 mr-3 text-xl">✓</span>
                  <span>Improves safety by early defect detection</span>
                </li>
                <li className="flex items-start">
                  <span className="text-blue-600 mr-3 text-xl">✓</span>
                  <span>Continuous model improvements and updates</span>
                </li>
              </ul>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-gray-900 mb-4">Get Started</h2>
              <p className="text-gray-700 mb-4">
                Ready to improve your railway maintenance program? Start analyzing images today.
              </p>
              <Link to="/predict" className="btn-primary inline-block">
                Upload Your First Image
              </Link>
            </section>
          </div>
        </div>

        {/* Contact Section */}
        <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg shadow-2xl p-12 text-white text-center">
          <h2 className="text-3xl font-bold mb-4">Have Questions?</h2>
          <p className="text-lg mb-6">
            Contact our support team for more information or custom deployment options.
          </p>
          <button className="bg-white text-blue-600 px-8 py-3 rounded-lg font-semibold hover:bg-gray-100 transition">
            Get in Touch
          </button>
        </div>
      </div>
    </div>
  );
}
