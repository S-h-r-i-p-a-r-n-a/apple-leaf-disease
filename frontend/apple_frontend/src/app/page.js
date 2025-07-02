'use client'
import { useState, useEffect } from 'react'

export default function Home() {
  const [image, setImage] = useState(null)
  const [preview, setPreview] = useState(null)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [darkMode, setDarkMode] = useState(false)

const BASE_URL = 'https://apple-leaf-disease.onrender.com'
 // Change this to your backend URL in production

  useEffect(() => {
    const root = document.documentElement
    root.style.setProperty('--background', darkMode ? '#0a0a0a' : '#ffffff')
    root.style.setProperty('--foreground', darkMode ? '#ededed' : '#171717')
  }, [darkMode])

  const handleImageChange = (e) => {
    const file = e.target.files[0]
    if (file) {
      setImage(file)
      setPreview(URL.createObjectURL(file))
      setResult(null)
    }
  }

  const handleRemoveImage = () => {
    setImage(null)
    setPreview(null)
    setResult(null)
    document.querySelector('input[type="file"]').value = ''
  }

  const handleUpload = async () => {
    if (!image) return
    setLoading(true)
    const formData = new FormData()
    formData.append('file', image)

    try {
      const res = await fetch(`${BASE_URL}/report`, {
        method: 'POST',
        body: formData,
      })

      if (!res.ok) throw new Error('Upload failed')
      const data = await res.json()
      setResult(data)
    } catch {
      alert('Upload failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main
      className="min-h-screen px-4 py-10 transition duration-300"
      style={{ backgroundColor: 'var(--background)', color: 'var(--foreground)' }}
    >
      <div
        className="max-w-3xl mx-auto rounded-2xl p-8 space-y-6 shadow-lg border border-gray-300"
        style={{ backgroundColor: 'rgba(255,255,255,0.1)', backdropFilter: 'blur(10px)' }}
      >
        {/* Header */}
        <div className="flex justify-between items-center">
          <h1 className="text-3xl font-bold">🍏 Apple Leaf Disease Detector</h1>
          <button
            onClick={() => setDarkMode(!darkMode)}
            className="px-4 py-1 rounded-md text-sm border"
            style={{
              backgroundColor: darkMode ? '#333' : '#eee',
              color: darkMode ? '#fff' : '#000',
              borderColor: darkMode ? '#555' : '#ccc',
            }}
          >
            {darkMode ? '☀️ Light Mode' : '🌙 Dark Mode'}
          </button>
        </div>

        {/* File Upload */}
        <input
          type="file"
          accept="image/*"
          onChange={handleImageChange}
          className="file:py-2 file:px-4 file:rounded file:border-0 file:bg-green-600 file:text-white hover:file:bg-green-700"
        />

        {/* Image Preview */}
        {preview && (
          <div className="relative w-fit mx-auto mt-4">
            <img src={preview} alt="Preview" className="max-w-sm rounded-lg shadow-md" />
            <button
              onClick={handleRemoveImage}
              className="absolute top-1 right-1 bg-white text-red-600 rounded-full w-6 h-6 flex items-center justify-center shadow hover:scale-110"
              title="Remove image"
            >
              ❌
            </button>
          </div>
        )}

        {/* Upload Button */}
        <div className="text-center">
          <button
            onClick={handleUpload}
            disabled={loading}
            className={`mt-4 px-6 py-2 rounded text-white font-medium transition ${
              loading ? 'bg-gray-400 cursor-not-allowed' : 'bg-green-600 hover:bg-green-700'
            }`}
          >
            {loading ? 'Processing...' : 'Upload & Predict'}
          </button>
        </div>

        {/* Results */}
        {result && (
          <div className="pt-6 border-t border-gray-300">
            {/* Detected Disease */}
            <h2 className="text-xl font-semibold mb-2">🧠 Detected Disease</h2>
            <ul className="space-y-1 mb-4">
              {result.detected_diseases?.map((d, i) => (
                <li key={i}>
                  ✅ <strong>{d.name}</strong> — Confidence: {d.confidence}
                </li>
              ))}
            </ul>

            {/* Treatment Report */}
            <h2 className="text-xl font-semibold mb-2">💊 Treatment Suggestion</h2>
            <ul className="space-y-1 mb-4">
              {Object.entries(result.treatment_report || {}).map(([k, v]) => (
                <li key={k}>
                  🔍 <strong>{k}:</strong> {v}
                </li>
              ))}
            </ul>

            {/* Annotated Image + Downloads */}
            <div className="mt-6 space-y-6">
              {/* Annotated Image */}
              <img
                src={`${BASE_URL}${result.annotated_image.replace(/\\/g, '/').replace(/^\/+/, '/')}`}
                alt="Prediction"
                className="w-full max-w-lg mx-auto rounded-lg shadow-xl border-4 border-green-600"
              />

              <div className="flex flex-col md:flex-row items-center justify-center gap-4 text-center">
                {/* Download PDF */}
                <a
                  href={`${BASE_URL}/download/${result.pdf_report?.split('/').pop()}`}
                  download
                  className="group relative px-6 py-3 bg-blue-600 text-white font-semibold rounded-lg shadow-md transition duration-300 hover:bg-blue-700 hover:scale-105"
                >
                  📄 Download Report (PDF)
                  <span className="block h-0.5 bg-white scale-x-0 group-hover:scale-x-100 transition-transform origin-left mt-1"></span>
                </a>

                {/* Download Annotated Image */}
                <a
                  href={`${BASE_URL}/download/${result.annotated_image?.split('/').pop()}`}
                  download
                  className="group relative px-6 py-3 bg-green-600 text-white font-semibold rounded-lg shadow-md transition duration-300 hover:bg-green-700 hover:scale-105"
                >
                  🖼️ Download Image
                  <span className="block h-0.5 bg-white scale-x-0 group-hover:scale-x-100 transition-transform origin-left mt-1"></span>
                </a>

                {/* Audio Voice Report */}
                <div className="bg-gray-100 p-3 rounded-lg shadow-md w-full md:w-auto">
                  <audio controls className="w-full md:w-64">
                    <source
                      src={`${BASE_URL}${result.voice_report?.replace(/\\/g, '/').replace(/^\/+/, '/')}`}
                      type="audio/mpeg"
                    />
                    Your browser does not support audio playback.
                  </audio>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </main>
  )
}
