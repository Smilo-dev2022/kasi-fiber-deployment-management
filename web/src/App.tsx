import { BrowserRouter, Routes, Route, Navigate } from react-router-dom

function Dashboard() {
  return <div className="p-4">Dashboard</div>
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<Dashboard />} />
      </Routes>
    </BrowserRouter>
  )
}
