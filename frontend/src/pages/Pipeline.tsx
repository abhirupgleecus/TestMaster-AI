import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { CheckCircle2, Circle, Loader2, PlayCircle, BarChart3, ChevronLeft, ShieldCheck, Terminal, AlertTriangle } from 'lucide-react';

const API_BASE = 'http://127.0.0.1:8000';

type Step = 'HITL' | 'GENERATING_SCRIPT' | 'EXECUTING' | 'REPORT';

export default function Pipeline() {
  const { sessionId } = useParams();
  const navigate = useNavigate();
  
  const [currentStep, setCurrentStep] = useState<Step>('HITL');
  
  const [testCases, setTestCases] = useState<any[]>([]);
  const [isLoadingTests, setIsLoadingTests] = useState(true);
  
  const [executionStats, setExecutionStats] = useState<any>(null);
  const [report, setReport] = useState<any>(null);
  
  const [error, setError] = useState<string | null>(null);
  const [viewingStepsTc, setViewingStepsTc] = useState<any | null>(null);

  // 1. Fetch Initial Test Cases
  useEffect(() => {
    fetch(`${API_BASE}/sessions/${sessionId}/test-cases/`)
      .then(res => res.json())
      .then(data => {
        setTestCases(data);
        setIsLoadingTests(false);
      })
      .catch(err => {
        console.error(err);
        setError("Failed to load generated test cases.");
        setIsLoadingTests(false);
      });
  }, [sessionId]);

  // Toggle Test Case Selection
  const toggleTestCase = async (testCaseId: string, currentStatus: boolean) => {
    try {
      const res = await fetch(`${API_BASE}/sessions/${sessionId}/test-cases/${testCaseId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ is_selected: !currentStatus })
      });
      if (res.ok) {
        setTestCases(prev => prev.map(tc => tc.id === testCaseId ? { ...tc, is_selected: !currentStatus } : tc));
      }
    } catch (err) {
      console.error(err);
    }
  };

  const toggleSelectAll = async () => {
    const allSelected = testCases.every(tc => tc.is_selected);
    const newStatus = !allSelected;
    
    // In a real app we'd have a bulk API, but here we can iterate or just update UI and then bulk patch
    // To keep it simple and reactive:
    try {
      // Mocking bulk behavior for UI responsiveness
      const updatedTcs = testCases.map(tc => ({ ...tc, is_selected: newStatus }));
      setTestCases(updatedTcs);
      
      // Parallel patch calls (not ideal for perf but works for small sets)
      await Promise.all(testCases.map(tc => 
        fetch(`${API_BASE}/sessions/${sessionId}/test-cases/${tc.id}`, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ is_selected: newStatus })
        })
      ));
    } catch (err) {
      console.error(err);
    }
  };

  // Removed toggleExpand as we now use a modal

  // Run the full pipeline sequentially
  const handleProceed = async () => {
    setCurrentStep('GENERATING_SCRIPT');
    try {
      // Generate Script
      const scriptRes = await fetch(`${API_BASE}/sessions/${sessionId}/generate-script`, { method: 'POST' });
      if (!scriptRes.ok) throw new Error("Script generation failed");
      const scriptData = await scriptRes.json();
      
      setCurrentStep('EXECUTING');
      // Execute Script
      const execRes = await fetch(`${API_BASE}/scripts/${scriptData.id}/execute`, { method: 'POST' });
      if (!execRes.ok) throw new Error("Execution failed to start");
      const execData = await execRes.json();
      
      // Start Polling (in a real app we'd poll, but execute blocks until done currently based on API design)
      // Actually, execute_script runs Playwright and returns the completed execution.
      setExecutionStats(execData);
      
      setCurrentStep('REPORT');
      // Fetch Report
      const reportRes = await fetch(`${API_BASE}/executions/${execData.id}/report`);
      if (reportRes.ok) {
        setReport(await reportRes.json());
      }
      
    } catch (err: any) {
      setError(err.message || "An error occurred during orchestration");
    }
  };

  const getStepStatus = (step: Step) => {
    const steps: Step[] = ['HITL', 'GENERATING_SCRIPT', 'EXECUTING', 'REPORT'];
    const currentIndex = steps.indexOf(currentStep);
    const stepIndex = steps.indexOf(step);
    if (stepIndex < currentIndex) return 'completed';
    if (stepIndex === currentIndex) return 'active';
    return 'pending';
  };

  const StepIndicator = ({ step, label, icon: Icon }: any) => {
    const status = getStepStatus(step);
    return (
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px', opacity: status === 'pending' ? 0.4 : 1 }}>
        <div style={{ 
          width: '40px', height: '40px', borderRadius: '50%', 
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          background: status === 'active' ? 'var(--glow-primary)' : status === 'completed' ? 'rgba(16, 185, 129, 0.2)' : 'rgba(255,255,255,0.05)',
          color: status === 'active' ? 'var(--accent-primary)' : status === 'completed' ? 'var(--success)' : 'var(--text-secondary)',
          border: `1px solid ${status === 'active' ? 'var(--accent-primary)' : status === 'completed' ? 'var(--success)' : 'var(--border-color)'}`
        }}>
          {status === 'active' && step !== 'HITL' && step !== 'REPORT' ? <Loader2 className="animate-spin" size={20} /> : <Icon size={20} />}
        </div>
        <span style={{ fontSize: '0.85rem', fontWeight: status === 'active' ? 600 : 400 }}>{label}</span>
      </div>
    );
  };

  return (
    <div className="container">
      <button 
        onClick={() => navigate(-1)} 
        style={{ background: 'transparent', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '4px', marginBottom: '2rem' }}
      >
        <ChevronLeft size={16} /> Exit Pipeline
      </button>

      {/* Stepper Header */}
      <div className="glass-panel" style={{ padding: '2rem', marginBottom: '2rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <StepIndicator step="HITL" label="Human Review" icon={ShieldCheck} />
        <div style={{ flex: 1, height: '1px', background: 'var(--border-color)', margin: '0 2rem' }} />
        <StepIndicator step="GENERATING_SCRIPT" label="Code Synthesis" icon={Terminal} />
        <div style={{ flex: 1, height: '1px', background: 'var(--border-color)', margin: '0 2rem' }} />
        <StepIndicator step="EXECUTING" label="Playwright Run" icon={PlayCircle} />
        <div style={{ flex: 1, height: '1px', background: 'var(--border-color)', margin: '0 2rem' }} />
        <StepIndicator step="REPORT" label="Analysis Report" icon={BarChart3} />
      </div>

      {error && (
        <div style={{ padding: '1rem', background: 'rgba(239, 68, 68, 0.1)', border: '1px solid var(--error)', color: 'var(--error)', borderRadius: '8px', marginBottom: '2rem', display: 'flex', alignItems: 'center', gap: '12px' }}>
          <AlertTriangle size={20} /> {error}
        </div>
      )}

      {/* Main Content Area */}
      {currentStep === 'HITL' && (
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
              <h2 className="title-glow">Review Generated Test Plan</h2>
              {!isLoadingTests && testCases.length > 0 && (
                <button 
                  onClick={toggleSelectAll}
                  style={{ 
                    background: 'rgba(255,255,255,0.05)', 
                    border: '1px solid var(--border-color)', 
                    padding: '4px 12px', 
                    borderRadius: '20px',
                    fontSize: '0.8rem',
                    color: 'var(--text-secondary)',
                    cursor: 'pointer'
                  }}
                >
                  {testCases.every(tc => tc.is_selected) ? 'Deselect All' : 'Select All'}
                </button>
              )}
            </div>
            <button 
              className="btn-primary"
              onClick={handleProceed}
              disabled={testCases.filter(t => t.is_selected).length === 0}
            >
              Approve & Synthesize Code
            </button>
          </div>

          {isLoadingTests ? (
            <div style={{ textAlign: 'center', padding: '4rem', color: 'var(--text-secondary)' }}>
              <Loader2 className="animate-spin" size={32} style={{ margin: '0 auto 1rem' }} />
              Loading AI proposals...
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              {testCases.map((tc, idx) => (
                <div 
                  key={tc.id} 
                  className="glass-panel" 
                  style={{ 
                    padding: '1.5rem', 
                    display: 'flex', 
                    gap: '1.5rem',
                    borderColor: tc.is_selected ? 'var(--accent-primary)' : 'var(--border-color)',
                    background: tc.is_selected ? 'rgba(139, 92, 246, 0.05)' : 'var(--bg-surface)'
                  }}
                >
                  <div style={{ cursor: 'pointer', marginTop: '4px' }} onClick={() => toggleTestCase(tc.id, tc.is_selected)}>
                    {tc.is_selected ? <CheckCircle2 color="var(--accent-primary)" size={24} /> : <Circle color="var(--text-secondary)" size={24} />}
                  </div>
                  <div style={{ flex: 1 }}>
                    <h3 className="break-words" style={{ fontSize: '1.1rem', marginBottom: '0.5rem', color: tc.is_selected ? 'var(--text-primary)' : 'var(--text-secondary)' }}>
                      {idx + 1}. {tc.title}
                    </h3>
                    <p className="break-words" style={{ color: 'var(--text-secondary)', fontSize: '0.95rem', marginBottom: '1rem', lineHeight: 1.5 }}>{tc.description}</p>
                    
                    <div style={{ display: 'flex', gap: '1rem', marginBottom: '1rem' }}>
                      <button 
                        onClick={() => setViewingStepsTc(tc)}
                        style={{ background: 'transparent', color: 'var(--accent-secondary)', fontSize: '0.85rem', fontWeight: 600, padding: 0 }}
                      >
                        View Steps
                      </button>
                    </div>

                    {/* Inline steps removed in favor of modal */}
                    
                    <div className="break-words" style={{ background: 'rgba(0,0,0,0.3)', padding: '1rem', borderRadius: '8px', fontSize: '0.9rem' }}>
                      <strong style={{ color: 'var(--accent-secondary)' }}>Final Expected Outcome:</strong> {tc.expected_output}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {(currentStep === 'GENERATING_SCRIPT' || currentStep === 'EXECUTING') && (
        <div className="glass-panel" style={{ padding: '5rem 2rem', textAlign: 'center', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
          <div style={{ position: 'relative', width: '80px', height: '80px', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '2rem' }}>
            <div style={{ position: 'absolute', inset: 0, borderRadius: '50%', border: '2px solid var(--accent-primary)', opacity: 0.2 }}></div>
            <div style={{ position: 'absolute', inset: 0, borderRadius: '50%', border: '2px solid transparent', borderTopColor: 'var(--accent-primary)', animation: 'spin 1s linear infinite' }}></div>
            <Terminal size={32} color="var(--accent-primary)" />
          </div>
          <h2 style={{ marginBottom: '1rem' }}>
            {currentStep === 'GENERATING_SCRIPT' ? 'Synthesizing Playwright Code...' : 'Executing Test Suite...'}
          </h2>
          <p className="text-secondary" style={{ maxWidth: '400px', lineHeight: 1.6 }}>
            {currentStep === 'GENERATING_SCRIPT' 
              ? 'The AI is mapping your selected test cases to executable Playwright TypeScript code.' 
              : 'Spinning up headless browser environment and executing the generated assertions.'}
          </p>
        </div>
      )}

      {currentStep === 'REPORT' && executionStats && report && (
        <div>
          <h2 className="title-glow" style={{ marginBottom: '1.5rem', textAlign: 'center', fontSize: '2.5rem' }}>Executive Summary</h2>
          
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1rem', marginBottom: '2rem' }}>
            <div className="glass-panel" style={{ padding: '1.5rem', textAlign: 'center' }}>
              <div style={{ fontSize: '2.5rem', fontWeight: 700, marginBottom: '0.5rem' }}>{executionStats.total_tests}</div>
              <div className="text-secondary" style={{ fontSize: '0.9rem', textTransform: 'uppercase', letterSpacing: '1px' }}>Total Tests</div>
            </div>
            <div className="glass-panel" style={{ padding: '1.5rem', textAlign: 'center', borderColor: executionStats.passed_tests > 0 ? 'rgba(16, 185, 129, 0.3)' : '' }}>
              <div style={{ fontSize: '2.5rem', fontWeight: 700, marginBottom: '0.5rem', color: 'var(--success)' }}>{executionStats.passed_tests}</div>
              <div className="text-secondary" style={{ fontSize: '0.9rem', textTransform: 'uppercase', letterSpacing: '1px' }}>Passed</div>
            </div>
            <div className="glass-panel" style={{ padding: '1.5rem', textAlign: 'center', borderColor: executionStats.failed_tests > 0 ? 'rgba(239, 68, 68, 0.3)' : '' }}>
              <div style={{ fontSize: '2.5rem', fontWeight: 700, marginBottom: '0.5rem', color: executionStats.failed_tests > 0 ? 'var(--error)' : 'inherit' }}>{executionStats.failed_tests}</div>
              <div className="text-secondary" style={{ fontSize: '0.9rem', textTransform: 'uppercase', letterSpacing: '1px' }}>Failed</div>
            </div>
            <div className="glass-panel" style={{ padding: '1.5rem', textAlign: 'center' }}>
              <div style={{ fontSize: '2.5rem', fontWeight: 700, marginBottom: '0.5rem', color: 'var(--accent-secondary)' }}>{executionStats.duration_ms ? (executionStats.duration_ms / 1000).toFixed(1) : 0}s</div>
              <div className="text-secondary" style={{ fontSize: '0.9rem', textTransform: 'uppercase', letterSpacing: '1px' }}>Duration</div>
            </div>
          </div>

          <div className="glass-panel" style={{ padding: '2.5rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
              <h3 style={{ fontSize: '1.5rem' }}>AI Deep Analysis</h3>
              <div style={{ padding: '6px 12px', background: report.overall_status === 'PASSED' ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)', color: report.overall_status === 'PASSED' ? 'var(--success)' : 'var(--error)', borderRadius: '20px', fontWeight: 600, fontSize: '0.9rem' }}>
                {report.overall_status}
              </div>
            </div>
            
            <p className="break-words" style={{ fontSize: '1.1rem', lineHeight: 1.7, marginBottom: '2rem' }}>
              {report.executive_summary}
            </p>

            {report.detailed_analysis && (
              <div style={{ background: 'rgba(0,0,0,0.3)', padding: '1.5rem', borderRadius: '12px' }}>
                <h4 style={{ marginBottom: '1rem', color: 'var(--accent-secondary)' }}>Technical Breakdown</h4>
                <pre className="break-all" style={{ whiteSpace: 'pre-wrap', fontFamily: 'inherit', color: 'var(--text-secondary)', lineHeight: 1.6, fontSize: '0.95rem' }}>
                  {JSON.stringify(report.detailed_analysis, null, 2)}
                </pre>
              </div>
            )}
            
            <div style={{ marginTop: '3rem', display: 'flex', justifyContent: 'center' }}>
              <button className="btn-primary" onClick={() => navigate('/')}>Return to Workspaces</button>
            </div>
          </div>
        </div>
      )}

      {/* Steps Modal */}
      {viewingStepsTc && (
        <div style={{ 
          position: 'fixed', 
          inset: 0, 
          background: 'rgba(0,0,0,0.8)', 
          backdropFilter: 'blur(8px)',
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center', 
          zIndex: 1000,
          padding: '2rem'
        }} onClick={() => setViewingStepsTc(null)}>
          <div 
            className="glass-panel" 
            style={{ 
              maxWidth: '600px', 
              width: '100%', 
              maxHeight: '80vh', 
              overflowY: 'auto', 
              overflowX: 'hidden', 
              padding: '2.5rem',
              position: 'relative'
            }} 
            onClick={e => e.stopPropagation()}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '2rem' }}>
              <div>
                <h2 style={{ fontSize: '1.5rem', marginBottom: '0.5rem' }} className="title-glow">{viewingStepsTc.title}</h2>
                <p className="text-secondary" style={{ fontSize: '0.9rem' }}>Detailed execution steps generated by AI</p>
              </div>
              <button 
                onClick={() => setViewingStepsTc(null)}
                style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid var(--border-color)', borderRadius: '50%', width: '32px', height: '32px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-secondary)' }}
              >
                ✕
              </button>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
              {viewingStepsTc.steps?.map((step: any) => (
                <div key={step.step_number} style={{ display: 'flex', gap: '1rem' }}>
                  <div style={{ 
                    width: '28px', 
                    height: '28px', 
                    borderRadius: '50%', 
                    background: 'rgba(139, 92, 246, 0.1)', 
                    color: 'var(--accent-primary)', 
                    display: 'flex', 
                    alignItems: 'center', 
                    justifyContent: 'center',
                    fontSize: '0.8rem',
                    fontWeight: 700,
                    flexShrink: 0
                  }}>
                    {step.step_number}
                  </div>
                  <div style={{ flex: 1 }}>
                    <div className="break-all" style={{ fontSize: '1rem', marginBottom: '0.4rem', color: 'var(--text-primary)' }}>{step.action}</div>
                    <div className="break-words" style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', padding: '0.75rem', background: 'rgba(0,0,0,0.2)', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.05)' }}>
                      <span style={{ color: 'var(--success)', fontWeight: 600, marginRight: '8px' }}>EXPECTED:</span>
                      {step.expected_result}
                    </div>
                  </div>
                </div>
              ))}
            </div>

            <div style={{ marginTop: '2.5rem', paddingTop: '2rem', borderTop: '1px solid var(--border-color)', display: 'flex', justifyContent: 'flex-end' }}>
              <button className="btn-secondary" onClick={() => setViewingStepsTc(null)}>Close</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
