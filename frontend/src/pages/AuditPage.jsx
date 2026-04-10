import { useEffect, useRef, useState } from 'react';
import Papa from 'papaparse';
import { AlertTriangle, CheckCircle, FileText, Flag, TrendingUp, Upload, X } from 'lucide-react';
import { auditOrganization } from '../services/api';

function readField(row, aliases) {
  for (const alias of aliases) {
    if (row[alias] !== undefined && row[alias] !== null && String(row[alias]).trim() !== '') {
      return String(row[alias]).trim();
    }
  }
  return '';
}

function parseOutcome(value) {
  const normalized = String(value ?? '')
    .trim()
    .toLowerCase();

  if (['1', 'true', 'yes', 'approved', 'approve', 'accept'].includes(normalized)) {
    return 1;
  }
  if (['0', 'false', 'no', 'denied', 'deny', 'reject', 'rejected'].includes(normalized)) {
    return 0;
  }

  const numeric = Number.parseInt(normalized, 10);
  return Number.isNaN(numeric) ? 0 : numeric > 0 ? 1 : 0;
}

function getPriorityClass(priority) {
  const value = (priority || '').toLowerCase();
  if (value === 'high') return 'high';
  if (value === 'medium') return 'medium';
  return 'low';
}

function AnimatedBar({ pct, color, delay = 0 }) {
  const [width, setWidth] = useState(0);

  useEffect(() => {
    const timeoutId = setTimeout(() => setWidth(Math.min(pct, 100)), 120 + delay);
    return () => clearTimeout(timeoutId);
  }, [delay, pct]);

  return (
    <div className="bar-track">
      <div className="bar-fill" style={{ width: `${width}%`, background: color }} />
    </div>
  );
}

function Metric({ label, value, sub, color }) {
  return (
    <div className="metric">
      <p className="metric-label">{label}</p>
      <p className="metric-value" style={{ color }}>
        {value}
      </p>
      <p className="metric-sub">{sub}</p>
    </div>
  );
}

export default function AuditPage() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [file, setFile] = useState(null);
  const [domain, setDomain] = useState('hiring');
  const [dragging, setDragging] = useState(false);

  const fileInputRef = useRef(null);

  const handleFile = (selectedFile) => {
    if (selectedFile && selectedFile.name.toLowerCase().endsWith('.csv')) {
      setFile(selectedFile);
    }
  };

  const handleDrop = (event) => {
    event.preventDefault();
    setDragging(false);
    handleFile(event.dataTransfer.files[0]);
  };

  const handleUpload = () => {
    if (!file) return;

    setLoading(true);
    setResult(null);

    Papa.parse(file, {
      header: true,
      skipEmptyLines: true,
      complete: async ({ data }) => {
        try {
          const decisions = data.map((row) => {
            if (domain === 'lending') {
              return {
                gender: readField(row, ['gender', 'Gender']),
                education: readField(row, ['education', 'Education']),
                income_group: readField(row, ['income_group', 'IncomeGroup', 'incomeGroup']),
                outcome: parseOutcome(readField(row, ['outcome', 'Outcome', 'decision', 'Decision', 'loan_status', 'Loan_Status'])),
              };
            }

            return {
              sex: readField(row, ['sex', 'Sex']),
              race: readField(row, ['race', 'Race']),
              age_group: readField(row, ['age_group', 'AgeGroup', 'ageGroup']),
              outcome: parseOutcome(readField(row, ['outcome', 'Outcome', 'decision', 'Decision'])),
            };
          });

          const hasInvalidRows = decisions.some((decision) => {
            if (domain === 'lending') {
              return !decision.gender || !decision.education || !decision.income_group;
            }
            return !decision.sex || !decision.race || !decision.age_group;
          });

          if (!decisions.length) {
            setResult({ error: true, message: 'CSV file contains no valid rows.' });
            setLoading(false);
            return;
          }

          if (hasInvalidRows) {
            setResult({
              error: true,
              message:
                domain === 'lending'
                  ? 'CSV is missing required lending columns/values: gender, education, income_group.'
                  : 'CSV is missing required hiring columns/values: sex, race, age_group.',
            });
            setLoading(false);
            return;
          }

          const response = await auditOrganization({ domain, decisions });
          setResult(response);
        } catch {
          setResult({ error: true, message: 'Audit failed. Please verify the CSV and try again.' });
        } finally {
          setLoading(false);
        }
      },
      error: () => {
        setLoading(false);
        setResult({ error: true, message: 'Invalid CSV format. Please upload a valid file.' });
      },
    });
  };

  const flaggedCount = result?.bias_summary?.flagged_count ?? 0;
  const totalRecords = result?.bias_summary?.total_records ?? 0;
  const highestDisparity = result?.flagged_slices?.length
    ? Math.max(...result.flagged_slices.map((slice) => slice.disparity_ratio || 0)).toFixed(1)
    : '0.0';
  const riskLevel = flaggedCount === 0 ? 'Low' : flaggedCount <= 2 ? 'Moderate' : 'High';
  const riskColor = flaggedCount === 0 ? 'var(--success)' : flaggedCount <= 2 ? 'var(--warning)' : 'var(--danger)';

  return (
    <section className="page-wrap">
      <header className="page-hero">
        <p className="hero-kicker">Enterprise Oversight</p>
        <h2 className="hero-title">Organization Bias Audit</h2>
        <p className="hero-subtitle">
          Run batch-level statistical diagnostics on decision data, prioritize high-risk segments, and track compliance-ready evidence.
        </p>
      </header>

      <div className="split-layout">
        <article className="panel">
          <p className="panel-title">Dataset Intake</p>

          <div className="field">
            <span className="field-label">Domain</span>
            <div className="pill-row">
              {['hiring', 'lending'].map((option) => (
                <button
                  key={option}
                  type="button"
                  className={`pill-btn${domain === option ? ' active' : ''}`}
                  onClick={() => setDomain(option)}
                >
                  {option.charAt(0).toUpperCase() + option.slice(1)}
                </button>
              ))}
            </div>
          </div>

          {!file ? (
            <div
              className={`upload-zone${dragging ? ' over' : ''}`}
              onDragOver={(event) => {
                event.preventDefault();
                setDragging(true);
              }}
              onDragLeave={() => setDragging(false)}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
            >
              <input ref={fileInputRef} type="file" accept=".csv" onChange={(event) => handleFile(event.target.files?.[0])} />
              <Upload size={28} style={{ marginBottom: '0.55rem', color: 'var(--primary)' }} />
              <p style={{ fontWeight: 700, marginBottom: '0.25rem' }}>Drop CSV file or click to browse</p>
              <p className="muted-text">
                {domain === 'lending'
                  ? 'Expected columns: gender, education, income_group, outcome'
                  : 'Expected columns: sex, race, age_group, outcome'}
              </p>
            </div>
          ) : (
            <div className="file-chip-wrap">
              <span className="file-chip">
                <FileText size={14} />
                {file.name}
              </span>
              <button type="button" className="icon-btn" onClick={() => setFile(null)}>
                <X size={14} />
              </button>
            </div>
          )}

          <button type="button" className="btn-primary" style={{ marginTop: '0.85rem' }} disabled={!file || loading} onClick={handleUpload}>
            {loading ? (
              <>
                <span className="spinner" />
                Running Audit
              </>
            ) : (
              <>Generate Audit Report</>
            )}
          </button>
        </article>

        <article className="panel">
          <p className="panel-title">Format Requirements</p>

          <div className="meta-line">
            <span className="muted-text">{domain === 'lending' ? 'gender' : 'sex'}</span>
            <strong>{domain === 'lending' ? 'Male / Female' : 'Male / Female / Other'}</strong>
          </div>
          <div className="meta-line">
            <span className="muted-text">{domain === 'lending' ? 'education' : 'race'}</span>
            <strong>{domain === 'lending' ? 'Graduate / Not Graduate' : 'Black, White, Hispanic, Asian, ...'}</strong>
          </div>
          <div className="meta-line">
            <span className="muted-text">{domain === 'lending' ? 'income_group' : 'age_group'}</span>
            <strong>{domain === 'lending' ? 'low, mid, high, very_high' : '25-34, 35-44, 45-54, ...'}</strong>
          </div>
          <div className="meta-line">
            <span className="muted-text">outcome</span>
            <strong>1 = approved, 0 = denied</strong>
          </div>

          <section className="info-box" style={{ marginTop: '0.9rem' }}>
            <p className="info-label">Audit Notes</p>
            <p className="muted-text">Slices with small samples are flagged as low-confidence. Findings are statistical indicators and not legal determinations.</p>
          </section>
        </article>
      </div>

      {result?.error && (
        <div className="alert error" style={{ marginTop: '0.9rem' }}>
          <AlertTriangle size={16} />
          <span>{result.message}</span>
        </div>
      )}

      {result && !result.error && (
        <>
          <section className="metric-grid">
            <Metric label="Total Records" value={totalRecords.toLocaleString()} sub="decisions analyzed" color="var(--primary)" />
            <Metric label="Flagged Slices" value={flaggedCount} sub="demographic groups" color={flaggedCount > 0 ? 'var(--danger)' : 'var(--success)'} />
            <Metric label="Highest Disparity" value={`${highestDisparity}x`} sub="vs reference" color={parseFloat(highestDisparity) >= 3 ? 'var(--danger)' : 'var(--warning)'} />
            <Metric label="Risk Level" value={riskLevel} sub="overall signal" color={riskColor} />
          </section>

          {result.gemini_report && (
            <section className="panel" style={{ marginBottom: '0.9rem' }}>
              <p className="info-label" style={{ marginBottom: '0.5rem' }}>
                <TrendingUp size={12} />
                AI Summary
              </p>
              <p className="muted-text">{result.gemini_report}</p>
            </section>
          )}

          <section className="panel">
            <p className="panel-title" style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
              <Flag size={12} />
              Flagged Groups by Priority
            </p>

            {result.flagged_slices?.length > 0 ? (
              <div className="slice-list">
                {[...result.flagged_slices]
                  .sort((a, b) => (b.disparity_ratio || 0) - (a.disparity_ratio || 0))
                  .map((slice, index) => {
                    const priority = getPriorityClass(slice.priority || slice.remediation_priority);
                    const approvalPct = Math.round((slice.approval_rate || 0) * 100);
                    const refPct = Math.round((slice.reference_approval_rate || 0) * 100);
                    const barColor = priority === 'high' ? 'var(--danger)' : priority === 'medium' ? 'var(--warning)' : 'var(--success)';
                    const sliceName = domain === 'lending' ? `${slice.gender} ${slice.education}` : `${slice.race} ${slice.sex}`;
                    const sliceDetail =
                      domain === 'lending'
                        ? `Income: ${slice.income_group} • n = ${slice.sample_size?.toLocaleString() || 'n/a'}`
                        : `Age: ${slice.age_group} • n = ${slice.sample_size?.toLocaleString() || 'n/a'}`;
                    const keyId = domain === 'lending'
                      ? `${slice.gender}-${slice.education}-${slice.income_group}-${index}`
                      : `${slice.race}-${slice.sex}-${slice.age_group}-${index}`;

                    return (
                      <article key={keyId} className={`slice-card ${priority}`}>
                        <div className="slice-head">
                          <div>
                            <p className="slice-name">{sliceName}</p>
                            <p className="slice-detail">{sliceDetail}</p>
                          </div>
                          <div style={{ textAlign: 'right' }}>
                            <p className="slice-ratio" style={{ color: barColor }}>{slice.disparity_ratio?.toFixed(1)}x</p>
                            <span className={`badge ${priority === 'high' ? 'error' : 'success'}`}>
                              {priority.toUpperCase()}
                            </span>
                          </div>
                        </div>

                        <div className="bar-row">
                          <div className="bar-meta">
                            <span className="muted-text">Group approval</span>
                            <strong>{approvalPct}%</strong>
                          </div>
                          <AnimatedBar pct={approvalPct} color={barColor} delay={index * 70} />
                        </div>

                        <div className="bar-row">
                          <div className="bar-meta">
                            <span className="muted-text">Reference approval</span>
                            <strong>{refPct}%</strong>
                          </div>
                          <AnimatedBar pct={refPct} color="var(--text-subtle)" delay={index * 70 + 80} />
                        </div>

                        {(slice.remediation_note || slice.note) && (
                          <section className="info-box" style={{ marginTop: '0.6rem' }}>
                            <p className="info-label">Suggested Action</p>
                            <p className="muted-text">{slice.remediation_note || slice.note}</p>
                          </section>
                        )}
                      </article>
                    );
                  })}
              </div>
            ) : (
              <div className="empty-state">
                <CheckCircle size={36} style={{ marginBottom: '0.5rem', color: 'var(--success)' }} />
                <p>No statistically significant disparities detected in the uploaded dataset.</p>
              </div>
            )}
          </section>
        </>
      )}

      <p className="footer-note">
        Results are generated for operational risk review. Validate findings with governance, legal, and model risk stakeholders before remediation decisions.
      </p>
    </section>
  );
}
