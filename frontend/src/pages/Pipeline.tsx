import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { CheckCircle2, Circle, Loader2, PlayCircle, BarChart3, ChevronLeft, ShieldCheck, Terminal, AlertTriangle } from 'lucide-react';

const API_BASE = 'http://127.0.0.1:8000';

type Step = 'HITL' | 'GENERATING_SCRIPT' | 'EXECUTING' | 'REPORT';
type ReportArtifact = {
  name?: string;
  content_type?: string;
  path?: string;
  url?: string | null;
};

type ExecutedTestCase = {
  planned_title: string;
  executed_title?: string | null;
  status: string;
  raw_status?: string | null;
  duration_ms?: number | null;
  description?: string | null;
  preconditions?: string | null;
  expected_output?: string | null;
  steps?: Array<{
    step_number: number;
    action: string;
    expected_result: string;
  }>;
  observed_outcome?: string | null;
  failure_reason?: string | null;
  screenshots?: ReportArtifact[];
  artifacts?: ReportArtifact[];
  location?: {
    file?: string;
    line?: number;
  } | null;
};

type DetailedAnalysis = {
  highlights?: string[];
  failures?: string[];
  recommendations?: string[];
  summary?: {
    selected_test_case_count?: number;
    executed_test_case_count?: number;
    passed_test_count?: number;
    failed_test_count?: number;
    skipped_test_count?: number;
    duration_ms?: number | null;
  };
  report_artifacts?: {
    html_report_url?: string | null;
    json_report_url?: string | null;
  };
  executed_test_cases?: ExecutedTestCase[];
};

type ReportResponse = {
  executive_summary: string;
  overall_status: string;
  confidence_score?: number | null;
  detailed_analysis?: DetailedAnalysis;
};

export default function Pipeline() {
  const { sessionId } = useParams();
  const navigate = useNavigate();
  
  const [currentStep, setCurrentStep] = useState<Step>('HITL');
  const [hitlGate, setHitlGate] = useState<'APPROVAL' | 'SELECTION'>('APPROVAL');
  
  const [testCases, setTestCases] = useState<any[]>([]);
  const [isLoadingTests, setIsLoadingTests] = useState(true);
  const [isApproving, setIsApproving] = useState(false);
  
  // Local tracking for approval checkboxes (Gate 1)
  const [localApprovals, setLocalApprovals] = useState<Set<string>>(new Set());
  
  const [executionStats, setExecutionStats] = useState<any>(null);
  const [report, setReport] = useState<ReportResponse | null>(null);
  
  const [error, setError] = useState<string | null>(null);
  const [viewingStepsTc, setViewingStepsTc] = useState<any | null>(null);

  // 1. Fetch Initial Test Cases
  useEffect(() => {
    fetch(`${API_BASE}/sessions/${sessionId}/test-cases/`)
      .then(res => res.json())
      .then(data => {
        setTestCases(data);
        setIsLoadingTests(false);
        // If any test cases are already approved, jump to Gate 2
        const hasApproved = data.some((tc: any) => tc.is_approved);
        if (hasApproved) {
          setHitlGate('SELECTION');
        } else {
          // Pre-select all for approval by default
          setLocalApprovals(new Set(data.map((tc: any) => tc.id)));
        }
      })
      .catch(err => {
        console.error(err);
        setError("Failed to load generated test cases.");
        setIsLoadingTests(false);
      });
  }, [sessionId]);

  // --- Gate 1: Local approval toggle (no backend call, just local state) ---
  const toggleApproval = (testCaseId: string) => {
    setLocalApprovals(prev => {
      const next = new Set(prev);
      if (next.has(testCaseId)) next.delete(testCaseId);
      else next.add(testCaseId);
      return next;
    });
  };

  const toggleApproveAll = () => {
    if (localApprovals.size === testCases.length) {
      setLocalApprovals(new Set());
    } else {
      setLocalApprovals(new Set(testCases.map(tc => tc.id)));
    }
  };

  // Submit bulk approval to backend, then transition to Gate 2
  const handleApprove = async () => {
    setIsApproving(true);
    try {
      const res = await fetch(`${API_BASE}/sessions/${sessionId}/test-cases/approve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ test_case_ids: Array.from(localApprovals) })
      });
      if (res.ok) {
        const updatedCases = await res.json();
        setTestCases(updatedCases);
        setHitlGate('SELECTION');
      } else {
        setError('Failed to approve test cases.');
      }
    } catch (err) {
      console.error(err);
      setError('Failed to approve test cases.');
    } finally {
      setIsApproving(false);
    }
  };

  // --- Gate 2: Selection toggle (backend PATCH, same as before) ---
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
    const approvedCases = testCases.filter(tc => tc.is_approved);
    const allSelected = approvedCases.every(tc => tc.is_selected);
    const newStatus = !allSelected;
    
    try {
      const updatedTcs = testCases.map(tc => tc.is_approved ? { ...tc, is_selected: newStatus } : tc);
      setTestCases(updatedTcs);
      
      await Promise.all(approvedCases.map(tc => 
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

  const artifactUrl = (url?: string | null) => url ? `${API_BASE}${url}` : null;

  const formatDuration = (ms?: number | null) => {
    if (!ms) return '0.0s';
    return `${(ms / 1000).toFixed(1)}s`;
  };

  const getCaseStatusStyle = (status: string) => {
    if (status === 'passed') {
      return {
        borderColor: 'rgba(16, 185, 129, 0.28)',
        badgeBg: 'rgba(16, 185, 129, 0.12)',
        badgeColor: 'var(--success)',
      };
    }

    if (status === 'failed') {
      return {
        borderColor: 'rgba(239, 68, 68, 0.28)',
        badgeBg: 'rgba(239, 68, 68, 0.12)',
        badgeColor: 'var(--error)',
      };
    }

    return {
      borderColor: 'var(--border-color)',
      badgeBg: 'rgba(255,255,255,0.06)',
      badgeColor: 'var(--text-secondary)',
    };
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
          {isLoadingTests ? (
            <div style={{ textAlign: 'center', padding: '4rem', color: 'var(--text-secondary)' }}>
              <Loader2 className="animate-spin" size={32} style={{ margin: '0 auto 1rem' }} />
              Loading AI proposals...
            </div>
          ) : hitlGate === 'APPROVAL' ? (
            /* ===== GATE 1: APPROVAL ===== */
            <div>
              <div style={{ marginBottom: '2.5rem' }}>
                <h2 className="title-glow" style={{ marginBottom: '0.5rem' }}>Review & Approve Generated Test Plan</h2>
                <p className="text-secondary" style={{ marginBottom: '1.5rem', fontSize: '0.95rem' }}>Select the test cases you approve. Only approved cases will be available for execution.</p>
                {testCases.length > 0 && (
                  <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
                    <button 
                      onClick={toggleApproveAll}
                      className="btn-secondary"
                      style={{ padding: '8px 16px', borderRadius: '8px', fontSize: '0.9rem' }}
                    >
                      {localApprovals.size === testCases.length ? 'Deselect All' : 'Select All'}
                    </button>
                    <button 
                      className="btn-primary"
                      onClick={handleApprove}
                      disabled={localApprovals.size === 0 || isApproving}
                    >
                      {isApproving ? (
                        <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <Loader2 className="animate-spin" size={16} /> Approving...
                        </span>
                      ) : `Approve ${localApprovals.size} Test Case${localApprovals.size !== 1 ? 's' : ''}`}
                    </button>
                  </div>
                )}
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                {testCases.map((tc, idx) => {
                  const isChecked = localApprovals.has(tc.id);
                  return (
                    <div 
                      key={tc.id} 
                      className="glass-panel" 
                      style={{ 
                        padding: '1.5rem', 
                        display: 'flex', 
                        gap: '1.5rem',
                        borderColor: isChecked ? 'var(--accent-primary)' : 'var(--border-color)',
                        background: isChecked ? 'rgba(139, 92, 246, 0.05)' : 'var(--bg-surface)'
                      }}
                    >
                      <div style={{ cursor: 'pointer', marginTop: '4px' }} onClick={() => toggleApproval(tc.id)}>
                        {isChecked ? <CheckCircle2 color="var(--accent-primary)" size={24} /> : <Circle color="var(--text-secondary)" size={24} />}
                      </div>
                      <div style={{ flex: 1 }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '1rem', marginBottom: '0.5rem' }}>
                          <h3 className="break-words" style={{ fontSize: '1.1rem', color: isChecked ? 'var(--text-primary)' : 'var(--text-secondary)', margin: 0 }}>
                            {idx + 1}. {tc.title}
                          </h3>
                          <button 
                            onClick={() => setViewingStepsTc(tc)}
                            className="btn-secondary"
                            style={{ padding: '6px 12px', fontSize: '0.8rem', borderRadius: '6px', whiteSpace: 'nowrap' }}
                          >
                            View Steps
                          </button>
                        </div>
                        <p className="break-words" style={{ color: 'var(--text-secondary)', fontSize: '0.95rem', marginBottom: '1rem', lineHeight: 1.5 }}>{tc.description}</p>
                        <div className="break-words" style={{ background: 'rgba(0,0,0,0.3)', padding: '1rem', borderRadius: '8px', fontSize: '0.9rem' }}>
                          <strong style={{ color: 'var(--accent-secondary)' }}>Final Expected Outcome:</strong> {tc.expected_output}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          ) : (
            /* ===== GATE 2: SELECTION ===== */
            <div>
              <div style={{ marginBottom: '2.5rem' }}>
                <h2 className="title-glow" style={{ marginBottom: '0.5rem' }}>Select Approved Tests for Execution</h2>
                <p className="text-secondary" style={{ marginBottom: '1.5rem', fontSize: '0.95rem' }}>Choose which approved test cases to include in this execution run.</p>
                {testCases.filter(tc => tc.is_approved).length > 0 && (
                  <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
                    <button 
                      onClick={toggleSelectAll}
                      className="btn-secondary"
                      style={{ padding: '8px 16px', borderRadius: '8px', fontSize: '0.9rem' }}
                    >
                      {testCases.filter(tc => tc.is_approved).every(tc => tc.is_selected) ? 'Deselect All' : 'Select All'}
                    </button>
                    <button 
                      className="btn-primary"
                      onClick={handleProceed}
                      disabled={testCases.filter(t => t.is_approved && t.is_selected).length === 0}
                    >
                      Synthesize & Run Code
                    </button>
                  </div>
                )}
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                {testCases.filter(tc => tc.is_approved).map((tc, idx) => (
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
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '1rem', marginBottom: '0.5rem' }}>
                        <h3 className="break-words" style={{ fontSize: '1.1rem', color: tc.is_selected ? 'var(--text-primary)' : 'var(--text-secondary)', margin: 0 }}>
                          {idx + 1}. {tc.title}
                        </h3>
                        <button 
                          onClick={() => setViewingStepsTc(tc)}
                          className="btn-secondary"
                          style={{ padding: '6px 12px', fontSize: '0.8rem', borderRadius: '6px', whiteSpace: 'nowrap' }}
                        >
                          View Steps
                        </button>
                      </div>
                      <p className="break-words" style={{ color: 'var(--text-secondary)', fontSize: '0.95rem', marginBottom: '1rem', lineHeight: 1.5 }}>{tc.description}</p>
                      <div className="break-words" style={{ background: 'rgba(0,0,0,0.3)', padding: '1rem', borderRadius: '8px', fontSize: '0.9rem' }}>
                        <strong style={{ color: 'var(--accent-secondary)' }}>Final Expected Outcome:</strong> {tc.expected_output}
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '0.75rem' }}>
                        <span style={{ 
                          display: 'inline-flex', 
                          alignItems: 'center', 
                          gap: '6px',
                          padding: '4px 12px', 
                          borderRadius: '20px', 
                          background: 'rgba(16, 185, 129, 0.1)', 
                          color: 'var(--success)', 
                          fontSize: '0.8rem', 
                          fontWeight: 600,
                          border: '1px solid rgba(16, 185, 129, 0.25)'
                        }}>
                          <CheckCircle2 size={14} /> Approved
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
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
            </div>
            
            <p className="break-words" style={{ fontSize: '1.1rem', lineHeight: 1.7, marginBottom: '2rem' }}>
              {report.executive_summary}
            </p>

            {report.detailed_analysis && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
                <div style={{ background: 'rgba(0,0,0,0.3)', padding: '1.5rem', borderRadius: '12px' }}>
                  <h4 style={{ marginBottom: '1rem', color: 'var(--accent-secondary)' }}>Technical Breakdown</h4>

                  {report.detailed_analysis.highlights && report.detailed_analysis.highlights.length > 0 && (
                    <div style={{ marginBottom: '1.5rem' }}>
                      <div style={{ fontWeight: 700, marginBottom: '0.75rem' }}>Highlights</div>
                      <ul style={{ margin: 0, paddingLeft: '1.25rem', color: 'var(--text-secondary)', lineHeight: 1.7 }}>
                        {report.detailed_analysis.highlights.map((item, idx) => (
                          <li key={`highlight-${idx}`}>{item}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {report.detailed_analysis.failures && report.detailed_analysis.failures.length > 0 && (
                    <div style={{ marginBottom: '1.5rem' }}>
                      <div style={{ fontWeight: 700, marginBottom: '0.75rem' }}>Failures</div>
                      <ul style={{ margin: 0, paddingLeft: '1.25rem', color: 'var(--text-secondary)', lineHeight: 1.7 }}>
                        {report.detailed_analysis.failures.map((item, idx) => (
                          <li key={`failure-${idx}`}>{item}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {report.detailed_analysis.recommendations && report.detailed_analysis.recommendations.length > 0 && (
                    <div>
                      <div style={{ fontWeight: 700, marginBottom: '0.75rem' }}>Recommendations</div>
                      <ul style={{ margin: 0, paddingLeft: '1.25rem', color: 'var(--text-secondary)', lineHeight: 1.7 }}>
                        {report.detailed_analysis.recommendations.map((item, idx) => (
                          <li key={`recommendation-${idx}`}>{item}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>

                {report.detailed_analysis.report_artifacts && (
                  <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
                    {report.detailed_analysis.report_artifacts.html_report_url && (
                      <a
                        href={artifactUrl(report.detailed_analysis.report_artifacts.html_report_url) || '#'}
                        target="_blank"
                        rel="noreferrer"
                        className="btn-secondary"
                        style={{ textDecoration: 'none' }}
                      >
                        Open Playwright HTML Report
                      </a>
                    )}
                    {report.detailed_analysis.report_artifacts.json_report_url && (
                      <a
                        href={artifactUrl(report.detailed_analysis.report_artifacts.json_report_url) || '#'}
                        target="_blank"
                        rel="noreferrer"
                        className="btn-secondary"
                        style={{ textDecoration: 'none' }}
                      >
                        Open Playwright JSON Report
                      </a>
                    )}
                  </div>
                )}

                {report.detailed_analysis.executed_test_cases && report.detailed_analysis.executed_test_cases.length > 0 && (
                  <div>
                    <h4 style={{ marginBottom: '1rem', color: 'var(--accent-secondary)' }}>Executed Test Cases</h4>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                      {report.detailed_analysis.executed_test_cases.map((testCase, idx) => {
                        const statusStyle = getCaseStatusStyle(testCase.status);
                        return (
                          <div
                            key={`${testCase.planned_title}-${idx}`}
                            className="glass-panel"
                            style={{
                              padding: '1.5rem',
                              borderColor: statusStyle.borderColor,
                              background: 'rgba(0,0,0,0.24)',
                            }}
                          >
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '1rem', marginBottom: '1rem' }}>
                              <div>
                                <h5 className="break-words" style={{ fontSize: '1.15rem', marginBottom: '0.4rem' }}>
                                  {idx + 1}. {testCase.planned_title}
                                </h5>
                                {testCase.executed_title && testCase.executed_title !== testCase.planned_title && (
                                  <div className="text-secondary" style={{ fontSize: '0.9rem' }}>
                                    Executed as: {testCase.executed_title}
                                  </div>
                                )}
                              </div>
                              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexShrink: 0 }}>
                                <span className="text-secondary" style={{ fontSize: '0.85rem' }}>
                                  {formatDuration(testCase.duration_ms)}
                                </span>
                                <span style={{ padding: '6px 12px', borderRadius: '20px', background: statusStyle.badgeBg, color: statusStyle.badgeColor, fontWeight: 700, fontSize: '0.85rem', textTransform: 'capitalize' }}>
                                  {testCase.status}
                                </span>
                              </div>
                            </div>

                            {testCase.description && (
                              <p className="break-words" style={{ color: 'var(--text-secondary)', lineHeight: 1.6, marginBottom: '1rem' }}>
                                {testCase.description}
                              </p>
                            )}

                            {testCase.preconditions && (
                              <div style={{ marginBottom: '1rem' }}>
                                <div style={{ fontWeight: 700, marginBottom: '0.35rem' }}>Preconditions</div>
                                <div className="break-words" style={{ color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                                  {testCase.preconditions}
                                </div>
                              </div>
                            )}

                            {testCase.steps && testCase.steps.length > 0 && (
                              <div style={{ marginBottom: '1rem' }}>
                                <div style={{ fontWeight: 700, marginBottom: '0.6rem' }}>Planned Steps</div>
                                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                                  {testCase.steps.map((step) => (
                                    <div key={`${testCase.planned_title}-step-${step.step_number}`} style={{ padding: '0.85rem 1rem', borderRadius: '10px', background: 'rgba(255,255,255,0.04)' }}>
                                      <div style={{ fontWeight: 600, marginBottom: '0.35rem' }}>
                                        Step {step.step_number}: {step.action}
                                      </div>
                                      <div className="text-secondary" style={{ lineHeight: 1.55 }}>
                                        Expected: {step.expected_result}
                                      </div>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}

                            {testCase.expected_output && (
                              <div style={{ marginBottom: '1rem' }}>
                                <div style={{ fontWeight: 700, marginBottom: '0.35rem' }}>Expected Outcome</div>
                                <div className="break-words" style={{ color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                                  {testCase.expected_output}
                                </div>
                              </div>
                            )}

                            <div style={{ marginBottom: testCase.screenshots && testCase.screenshots.length > 0 ? '1rem' : 0 }}>
                              <div style={{ fontWeight: 700, marginBottom: '0.35rem' }}>Observed Outcome</div>
                              <div className="break-words" style={{ color: testCase.status === 'failed' ? 'var(--error)' : 'var(--text-secondary)', lineHeight: 1.6 }}>
                                {testCase.failure_reason || testCase.observed_outcome}
                              </div>
                            </div>

                            {testCase.screenshots && testCase.screenshots.length > 0 && (
                              <div style={{ marginBottom: '1rem' }}>
                                <div style={{ fontWeight: 700, marginBottom: '0.75rem' }}>Screenshot Evidence</div>
                                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1rem' }}>
                                  {testCase.screenshots.map((screenshot, shotIdx) => (
                                    <a
                                      key={`${testCase.planned_title}-shot-${shotIdx}`}
                                      href={artifactUrl(screenshot.url) || '#'}
                                      target="_blank"
                                      rel="noreferrer"
                                      style={{ textDecoration: 'none' }}
                                    >
                                      <div style={{ borderRadius: '12px', overflow: 'hidden', background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border-color)' }}>
                                        <img
                                          src={artifactUrl(screenshot.url) || ''}
                                          alt={`${testCase.planned_title} evidence ${shotIdx + 1}`}
                                          style={{ width: '100%', height: '180px', objectFit: 'cover', display: 'block' }}
                                        />
                                        <div style={{ padding: '0.75rem 0.9rem', color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
                                          {screenshot.name || `Screenshot ${shotIdx + 1}`}
                                        </div>
                                      </div>
                                    </a>
                                  ))}
                                </div>
                              </div>
                            )}

                            {testCase.artifacts && testCase.artifacts.length > 0 && (
                              <div>
                                <div style={{ fontWeight: 700, marginBottom: '0.75rem' }}>Artifacts</div>
                                <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
                                  {testCase.artifacts.map((artifact, artifactIdx) => (
                                    <a
                                      key={`${testCase.planned_title}-artifact-${artifactIdx}`}
                                      href={artifactUrl(artifact.url) || '#'}
                                      target="_blank"
                                      rel="noreferrer"
                                      className="btn-secondary"
                                      style={{ textDecoration: 'none' }}
                                    >
                                      {artifact.name || `Artifact ${artifactIdx + 1}`}
                                    </a>
                                  ))}
                                </div>
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}
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
