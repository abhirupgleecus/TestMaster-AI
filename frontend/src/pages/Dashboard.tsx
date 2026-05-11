import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { FolderPlus, Globe, ArrowRight, Brain } from 'lucide-react';

const API_BASE = 'http://127.0.0.1:8000';

export default function Dashboard() {
  const [projects, setProjects] = useState<any[]>([]);
  const [isCreating, setIsCreating] = useState(false);
  const navigate = useNavigate();
  
  const [name, setName] = useState('');
  const [targetUrl, setTargetUrl] = useState('');
  const [description, setDescription] = useState('');

  useEffect(() => {
    fetch(`${API_BASE}/projects/`)
      .then(res => res.json())
      .then(data => setProjects(data))
      .catch(err => console.error(err));
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsCreating(true);
    try {
      const res = await fetch(`${API_BASE}/projects/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, target_url: targetUrl, description })
      });
      if (res.ok) {
        const data = await res.json();
        navigate(`/projects/${data.id}`);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setIsCreating(false);
    }
  };

  return (
    <div className="container">
      {/* Central Hero Section for New Project */}
      <section style={{ 
        padding: '6rem 0 4rem', 
        marginBottom: '4rem', 
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        textAlign: 'center'
      }}>
        <div style={{ maxWidth: '700px', width: '100%' }}>
          {/* Brand Heading Lockup */}
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.75rem', marginBottom: '4rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '24px' }}>
              <div style={{ 
                background: 'linear-gradient(135deg, #8B5CF6 0%, #3B82F6 100%)', 
                padding: '16px', 
                borderRadius: '24px', 
                display: 'flex', 
                alignItems: 'center', 
                justifyContent: 'center',
                boxShadow: '0 0 40px rgba(139, 92, 246, 0.4)'
              }}>
                <Brain size={48} color="white" />
              </div>
              <h1 style={{ fontSize: '4.5rem', fontWeight: 800, margin: 0, letterSpacing: '-2px', lineHeight: 1 }}>
                TestMaster <span style={{ 
                  background: 'linear-gradient(to right, #A78BFA, #60A5FA)', 
                  WebkitBackgroundClip: 'text', 
                  WebkitTextFillColor: 'transparent' 
                }}>AI</span>
              </h1>
            </div>

            <h2 style={{ 
              fontSize: '2.25rem', 
              fontWeight: 700, 
              color: '#9333EA', 
              textShadow: '0 0 30px rgba(147, 51, 234, 0.6), 0 0 10px rgba(147, 51, 234, 0.4)',
              margin: 0,
              letterSpacing: '0.5px',
              lineHeight: 1.2
            }}>
              Generate Quality Testscripts
            </h2>
            
            <p className="text-secondary" style={{ 
              fontSize: '1.25rem', 
              margin: 0, 
              fontWeight: 500, 
              letterSpacing: '0.5px', 
              opacity: 0.7 
            }}>
              AI-Powered Test Automation for Validation Excellence
            </p>
          </div>

          <div className="glass-panel" style={{ padding: '2.5rem', textAlign: 'left', width: '100%' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '2rem' }}>
              <div style={{ padding: '12px', background: 'rgba(139, 92, 246, 0.1)', borderRadius: '12px', color: 'var(--accent-primary)' }}>
                <FolderPlus size={24} />
              </div>
              <h3 style={{ fontSize: '1.5rem' }}>Create New Testscript</h3>
            </div>
            
            <form onSubmit={handleCreate} style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
              <div className="flex flex-col gap-2">
                <label style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', fontWeight: 500 }}>PROJECT NAME</label>
                <input 
                  required
                  className="input-base" 
                  placeholder="e.g. Acme E-Commerce" 
                  value={name}
                  onChange={e => setName(e.target.value)}
                />
              </div>
              <div className="flex flex-col gap-2">
                <label style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', fontWeight: 500 }}>TARGET APPLICATION URL</label>
                <input 
                  required
                  type="url"
                  className="input-base" 
                  placeholder="https://app.acme.com" 
                  value={targetUrl}
                  onChange={e => setTargetUrl(e.target.value)}
                />
              </div>
              <div className="flex flex-col gap-2" style={{ gridColumn: 'span 2' }}>
                <label style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', fontWeight: 500 }}>DESCRIPTION</label>
                <textarea 
                  className="input-base" 
                  placeholder="What are we testing? (optional)" 
                  rows={2}
                  value={description}
                  onChange={e => setDescription(e.target.value)}
                />
              </div>
              <div style={{ gridColumn: 'span 2', marginTop: '1rem' }}>
                <button 
                  type="submit" 
                  className="btn-primary w-full" 
                  disabled={isCreating || !name || !targetUrl}
                  style={{ padding: '14px', fontSize: '1.1rem' }}
                >
                  {isCreating ? 'Provisioning Environment...' : 'Initialize Pipeline'} <ArrowRight size={20} />
                </button>
              </div>
            </form>
          </div>
        </div>
      </section>

      {/* Active Workspaces List */}
      <section>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '2rem' }}>
          <h2 style={{ fontSize: '1.75rem' }}>Your Workspaces</h2>
          <div style={{ flex: 1, height: '1px', background: 'var(--border-color)' }}></div>
          <span className="text-secondary" style={{ fontSize: '0.9rem' }}>{projects.length} ACTIVE</span>
        </div>

        {projects.length === 0 ? (
          <div className="glass-panel" style={{ padding: '4rem', textAlign: 'center', borderStyle: 'dashed' }}>
            <p className="text-secondary">No workspaces found. Initialize your first pipeline above.</p>
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(350px, 1fr))', gap: '2rem' }}>
            {projects.map(p => (
              <div 
                key={p.id} 
                className="glass-panel" 
                style={{ padding: '2rem', display: 'flex', flexDirection: 'column', justifyContent: 'space-between', cursor: 'pointer' }}
                onClick={() => navigate(`/projects/${p.id}`)}
              >
                <div>
                  <h3 style={{ marginBottom: '0.5rem', fontSize: '1.25rem' }}>{p.name}</h3>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '1rem' }}>
                    <Globe size={14} />
                    <span>{p.target_url}</span>
                  </div>
                  <p className="text-secondary" style={{ fontSize: '0.95rem', lineHeight: 1.5 }}>
                    {p.description || 'No description provided.'}
                  </p>
                </div>
                <div style={{ marginTop: '2rem', display: 'flex', justifyContent: 'flex-end' }}>
                  <span style={{ color: 'var(--accent-secondary)', fontSize: '0.9rem', fontWeight: 500, display: 'flex', alignItems: 'center', gap: '4px' }}>
                    Open Workspace <ArrowRight size={14} />
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
