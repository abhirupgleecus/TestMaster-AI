import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import ProjectWorkspace from './pages/ProjectWorkspace';
import Pipeline from './pages/Pipeline';

function App() {
  return (
    <BrowserRouter>
      <div className="app-layout">
        <main>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/projects/:projectId" element={<ProjectWorkspace />} />
            <Route path="/sessions/:sessionId" element={<Pipeline />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;
