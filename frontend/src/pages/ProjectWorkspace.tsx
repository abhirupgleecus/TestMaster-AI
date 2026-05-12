import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Play, Activity, Settings, ChevronLeft } from 'lucide-react';

// const API_BASE = 'http://127.0.0.1:8000';
const API_BASE = 'http://136.110.2.248:5173';

export default function ProjectWorkspace() {
  const { projectId } = useParams();
  const navigate = useNavigate();
  const [project, setProject] = useState<any>(null);
  const [contextInput, setContextInput] = useState('');
  const [isStarting, setIsStarting] = useState(false);

  useEffect(() => {
    fetch(`${API_BASE}/projects/${projectId}`)
      .then(res => res.json())
      .then(data => setProject(data))
      .catch(err => console.error(err));
  }, [projectId]);

  const handleStartSession = async () => {
    if (!contextInput) return;
    setIsStarting(true);
    try {
      const res = await fetch(`${API_BASE}/projects/${projectId}/sessions/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ context_input: contextInput })
      });
      if (res.ok) {
        const data = await res.json();
        navigate(`/sessions/${data.id}`);
      }
    } catch (err) {
      console.error(err);
      setIsStarting(false);
    }
  };

  if (!project) {
    return <div className="container" style={{ textAlign: 'center', padding: '5rem', color: 'var(--text-secondary)' }}>Loading Workspace...</div>;
  }

  return (
    <div className="container">
      <button 
        onClick={() => navigate('/')} 
        style={{ background: 'transparent', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '4px', marginBottom: '2rem' }}
      >
        <ChevronLeft size={16} /> Back to Dashboard
      </button>

      <div className="glass-panel" style={{ padding: '3rem', marginBottom: '3rem', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h1 style={{ fontSize: '3rem', marginBottom: '1rem' }} className="title-glow">{project.name}</h1>
          <a href={project.target_url} target="_blank" rel="noreferrer" className="break-all" style={{ color: 'var(--text-secondary)', display: 'inline-flex', alignItems: 'center', gap: '8px', padding: '8px 16px', background: 'rgba(255,255,255,0.05)', borderRadius: '20px' }}>
            <Activity size={16} color="var(--success)" style={{ flexShrink: 0 }} />
            {project.target_url}
          </a>
          <p className="break-words" style={{ marginTop: '1.5rem', color: 'var(--text-secondary)', fontSize: '1.1rem', maxWidth: '600px', lineHeight: 1.6 }}>
            {project.description}
          </p>
        </div>
        <div style={{ padding: '16px', background: 'rgba(255,255,255,0.03)', borderRadius: '50%' }}>
          <Settings size={32} color="var(--accent-secondary)" />
        </div>
      </div>

      <h2 style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '12px' }}>
        <Play color="var(--accent-primary)" /> Generate New Test-Cases
      </h2>
      <div className="glass-panel" style={{ padding: '2rem' }}>
        <p style={{ marginBottom: '1rem', color: 'var(--text-secondary)' }}>
          Describe the user journey or specific functionalities you want the AI to generate tests for. The more specific, the better the coverage.
        </p>
        <textarea 
          className="input-base" 
          rows={5}
          placeholder="e.g. Users should be able to navigate to the catalog, search for 'wireless headphones', filter by rating, and add the top result to their cart."
          value={contextInput}
          onChange={e => setContextInput(e.target.value)}
          style={{ fontSize: '1.1rem', padding: '1.5rem', marginBottom: '1.5rem' }}
        />
        <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
          <button 
            className="btn-primary" 
            style={{ padding: '12px 24px', fontSize: '1.1rem' }}
            disabled={isStarting || !contextInput}
            onClick={handleStartSession}
          >
            {isStarting ? (
              <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <div style={{ width: '16px', height: '16px', border: '2px solid rgba(255,255,255,0.3)', borderTopColor: '#fff', borderRadius: '50%' }} className="animate-spin" />
                Synthesizing Plan...
              </span>
            ) : 'Generate Test Plan'}
          </button>
        </div>
      </div>
    </div>
  );
}
