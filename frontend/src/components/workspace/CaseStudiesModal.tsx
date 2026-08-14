import { useEffect, useState } from 'react';
import { getCaseStudies, runCaseStudy, type CaseStudySummary, type CaseStudyRunResponse } from '../../api/caseStudy';
import { useGrid } from '../../state/GridContext';

export function CaseStudiesModal({ onClose }: { onClose: () => void }) {
  const [studies, setStudies] = useState<CaseStudySummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState<string | null>(null);
  const [result, setResult] = useState<CaseStudyRunResponse | null>(null);
  
  const gridState = useGrid();

  useEffect(() => {
    getCaseStudies()
      .then(setStudies)
      .finally(() => setLoading(false));
  }, []);

  const handleRun = async (study: CaseStudySummary) => {
    setRunning(study.id);
    setResult(null);
    try {
      const res = await runCaseStudy(study.id);
      setResult(res);
      // Wait a moment then load the grid and trigger analysis state
      await gridState.loadGrid(study.grid_id);
      
      // Update analysis state with the result from the case study run
      // We don't have a direct setter for analysis.result in the context, but we can set it somehow or let the user see it
      // Actually, since we need to show the visual timeline, we can render it here in the modal.
    } catch (err) {
      console.error(err);
    } finally {
      setRunning(null);
    }
  };

  return (
    <div className="modal-overlay" style={overlayStyle}>
      <div className="modal-content" style={contentStyle}>
        <h2>Engineering Case Studies</h2>
        <p className="panel-hint">Demonstration scenarios validating GridFlex under different stress conditions.</p>
        
        {loading ? <p>Loading...</p> : (
          <div style={{ display: 'flex', gap: '20px' }}>
            <div style={{ flex: 1, maxHeight: '60vh', overflowY: 'auto' }}>
              {studies.map(study => (
                <div key={study.id} className="case-study-card" style={cardStyle}>
                  <h3>{study.name}</h3>
                  <p>{study.description}</p>
                  <div style={{ marginTop: '10px' }}>
                    <strong>Expected Issues:</strong>
                    <ul>
                      {study.expected_issues.map(iss => <li key={iss}>{iss}</li>)}
                    </ul>
                  </div>
                  <button 
                    disabled={running !== null}
                    onClick={() => handleRun(study)}
                    style={{ marginTop: '10px' }}
                  >
                    {running === study.id ? 'Running...' : 'Run Case Study'}
                  </button>
                </div>
              ))}
            </div>
            
            {result && (
              <div style={{ flex: 1, padding: '15px', background: '#f5f5f5', borderRadius: '4px' }}>
                <h3>Execution Timeline</h3>
                <div className="execution-timeline">
                  {result.steps.map((step, idx) => (
                    <div key={idx} style={{ marginBottom: '10px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <span style={getStatusStyle(step.status)}>{step.status}</span>
                        <strong>{step.name}</strong>
                      </div>
                      {step.message && <div style={{ marginLeft: '65px', fontSize: '0.9em', color: '#666' }}>{step.message}</div>}
                    </div>
                  ))}
                </div>
                
                <div style={{ marginTop: '20px', padding: '10px', background: '#fff', border: '1px solid #ddd' }}>
                  <strong>Disclaimer:</strong> This execution uses actual power flow computations and is fully reproducible.
                </div>
                
                <button onClick={onClose} style={{ marginTop: '15px' }}>View Results in Workspace</button>
              </div>
            )}
          </div>
        )}
        
        <button className="close-btn" onClick={onClose} style={closeBtnStyle}>Close</button>
      </div>
    </div>
  );
}

const overlayStyle: React.CSSProperties = {
  position: 'fixed',
  top: 0, left: 0, right: 0, bottom: 0,
  backgroundColor: 'rgba(0,0,0,0.5)',
  display: 'flex',
  justifyContent: 'center',
  alignItems: 'center',
  zIndex: 1000
};

const contentStyle: React.CSSProperties = {
  backgroundColor: '#fff',
  padding: '20px',
  borderRadius: '8px',
  width: '80%',
  maxWidth: '900px',
  maxHeight: '90vh',
  overflowY: 'auto',
  position: 'relative'
};

const cardStyle: React.CSSProperties = {
  border: '1px solid #ddd',
  padding: '15px',
  marginBottom: '10px',
  borderRadius: '4px'
};

const closeBtnStyle: React.CSSProperties = {
  position: 'absolute',
  top: '10px',
  right: '10px'
};

function getStatusStyle(status: string): React.CSSProperties {
  const base = { padding: '2px 6px', borderRadius: '4px', fontSize: '0.8em', width: '50px', textAlign: 'center' as const };
  switch(status) {
    case 'SUCCESS': return { ...base, backgroundColor: '#d4edda', color: '#155724' };
    case 'FAILED': return { ...base, backgroundColor: '#f8d7da', color: '#721c24' };
    case 'SKIPPED': return { ...base, backgroundColor: '#e2e3e5', color: '#383d41' };
    default: return { ...base, backgroundColor: '#cce5ff', color: '#004085' };
  }
}
