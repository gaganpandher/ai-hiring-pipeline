import React from 'react'
import ReactDOM from 'react-dom/client'

function App() {
  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      height: '100vh',
      fontFamily: 'sans-serif',
      background: '#0f1117',
      color: '#ffffff',
      gap: '12px'
    }}>
      <div style={{ fontSize: '48px' }}>🧠</div>
      <h1 style={{ fontSize: '28px', fontWeight: 600, margin: 0 }}>
        AI Hiring Pipeline
      </h1>
      <p style={{ color: '#888', margin: 0 }}>
        Frontend connected ✅ — ready to build
      </p>
      <a
        href="http://localhost:8000/api/docs"
        target="_blank"
        rel="noreferrer"
        style={{
          marginTop: '8px',
          padding: '10px 24px',
          background: '#7f77dd',
          color: '#fff',
          borderRadius: '8px',
          textDecoration: 'none',
          fontSize: '14px'
        }}
      >
        Open API Docs →
      </a>
    </div>
  )
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
)
