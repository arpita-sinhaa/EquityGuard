import { useEffect, useState } from 'react';
import { AlertTriangle, CheckCircle, ChevronDown, Info, Search } from 'lucide-react';
import { checkBias } from '../services/api';

const DOMAIN_OPTIONS = [
  { value: 'hiring', label: 'Hiring' },
  { value: 'lending', label: 'Lending' },
];

const SEX_OPTIONS = ['Female', 'Male'];
const RACE_OPTIONS = ['Black', 'White', 'Hispanic', 'Asian', 'American Indian or Alaska Native', 'Other'];
const AGE_OPTIONS = ['18-24', '25-34', '35-44', '45-54', '55+'];
const GENDER_OPTIONS = ['Female', 'Male'];
const EDUCATION_OPTIONS = ['Graduate', 'Not Graduate'];
const INCOME_GROUP_OPTIONS = [
  { value: 'low', label: 'Low (<= INR 3,000)' },
  { value: 'mid', label: 'Mid (INR 3,001 - 6,000)' },
  { value: 'high', label: 'High (INR 6,001 - 10,000)' },
  { value: 'very_high', label: 'Very High (> INR 10,000)' },
];

function getSeverityClass(ratio) {
  if (!ratio) return 'low';
  if (ratio >= 3) return 'high';
  if (ratio >= 1.5) return 'medium';
  return 'low';
}

function StyledSelect({ name, value, onChange, options }) {
  return (
    <div className="select-wrap">
      <select className="select" name={name} value={value} onChange={onChange}>
        {options.map((option) => (
          <option key={typeof option === 'string' ? option : option.value} value={typeof option === 'string' ? option : option.value}>
            {typeof option === 'string' ? option : option.label}
          </option>
        ))}
      </select>
      <span className="select-icon">
        <ChevronDown size={15} />
      </span>
    </div>
  );
}

function AnimatedBar({ pct, color, delay = 0 }) {
  const [width, setWidth] = useState(0);

  useEffect(() => {
    const timeoutId = setTimeout(() => {
      setWidth(Math.min(pct, 100));
    }, 120 + delay);

    return () => clearTimeout(timeoutId);
  }, [delay, pct]);

  return (
    <div className="bar-track">
      <div className="bar-fill" style={{ width: `${width}%`, background: color }} />
    </div>
  );
}

export default function CitizenPage() {
  const [formData, setFormData] = useState({
    domain: 'hiring',
    sex: 'Female',
    race: 'Black',
    age_group: '45-54',
    gender: 'Female',
    education: 'Graduate',
    income_group: 'mid',
  });
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const handleChange = (event) => {
    setFormData((current) => ({ ...current, [event.target.name]: event.target.value }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setLoading(true);
    setResult(null);

    try {
      const payload =
        formData.domain === 'lending'
          ? {
              domain: formData.domain,
              gender: formData.gender,
              education: formData.education,
              income_group: formData.income_group,
            }
          : {
              domain: formData.domain,
              sex: formData.sex,
              race: formData.race,
              age_group: formData.age_group,
            };

      const response = await checkBias(payload);
      setResult({
        status: response.status || 'OK',
        data: response.data || response,
        explanation: response.explanation || 'No explanation available.',
        counterfactuals: response.counterfactuals || null,
      });
    } catch {
      setResult({ status: 'ERROR', explanation: 'Something went wrong. Please try again.' });
    } finally {
      setLoading(false);
    }
  };

  const data = result?.data;
  const counterfactuals = result?.counterfactuals;
  const severity = getSeverityClass(data?.disparity_ratio);
  const approvalPct = data ? Math.round((data.approval_rate || 0) * 100) : 0;
  const referencePct = data ? Math.round((data.reference_approval_rate || 0) * 100) : 0;
  const profileLabel =
    formData.domain === 'lending'
      ? `${formData.gender}, ${formData.education}, ${formData.income_group}`
      : `${formData.race} ${formData.sex}, ${formData.age_group}`;

  return (
    <section className="page-wrap">
      <header className="page-hero">
        <p className="hero-kicker">Citizen Oversight</p>
        <h2 className="hero-title">Personalized Bias Screening</h2>
        <p className="hero-subtitle">
          Submit a demographic profile and receive a transparent, model-backed disparity report across hiring and lending outcomes.
        </p>
      </header>

      <div className="split-layout">
        <article className="panel">
          <p className="panel-title">Profile Input</p>

          <form onSubmit={handleSubmit}>
            <div className="field">
              <span className="field-label">Domain</span>
              <div className="pill-row">
                {DOMAIN_OPTIONS.map((option) => (
                  <button
                    key={option.value}
                    type="button"
                    className={`pill-btn${formData.domain === option.value ? ' active' : ''}`}
                    onClick={() => setFormData((current) => ({ ...current, domain: option.value }))}
                  >
                    {option.label}
                  </button>
                ))}
              </div>
            </div>

            {formData.domain === 'lending' ? (
              <>
                <div className="field">
                  <label className="field-label">Gender</label>
                  <StyledSelect name="gender" value={formData.gender} onChange={handleChange} options={GENDER_OPTIONS} />
                </div>

                <div className="field">
                  <label className="field-label">Education</label>
                  <StyledSelect
                    name="education"
                    value={formData.education}
                    onChange={handleChange}
                    options={EDUCATION_OPTIONS}
                  />
                </div>

                <div className="field">
                  <label className="field-label">Income Group</label>
                  <StyledSelect
                    name="income_group"
                    value={formData.income_group}
                    onChange={handleChange}
                    options={INCOME_GROUP_OPTIONS}
                  />
                </div>
              </>
            ) : (
              <>
                <div className="field">
                  <label className="field-label">Sex</label>
                  <StyledSelect name="sex" value={formData.sex} onChange={handleChange} options={SEX_OPTIONS} />
                </div>

                <div className="field">
                  <label className="field-label">Race / Ethnicity</label>
                  <StyledSelect name="race" value={formData.race} onChange={handleChange} options={RACE_OPTIONS} />
                </div>

                <div className="field">
                  <label className="field-label">Age Group</label>
                  <StyledSelect name="age_group" value={formData.age_group} onChange={handleChange} options={AGE_OPTIONS} />
                </div>
              </>
            )}

            <button type="submit" className="btn-primary" disabled={loading}>
              {loading ? (
                <>
                  <span className="spinner" />
                  Analyzing Pattern
                </>
              ) : (
                <>
                  <Search size={16} />
                  Run Check
                </>
              )}
            </button>
          </form>
        </article>

        <article className="panel">
          <p className="panel-title">Decision Analytics</p>

          {!result && !loading && (
            <div className="empty-state">
              <Search size={34} style={{ marginBottom: '0.6rem' }} />
              <p>Run the check to generate disparity and compliance indicators for your selected profile.</p>
            </div>
          )}

          {result?.status === 'ERROR' && (
            <div className="alert error">
              <AlertTriangle size={16} />
              <span>{result.explanation}</span>
            </div>
          )}

          {result && result.status !== 'ERROR' && data && (
            <div>
              <div className="ratio-view">
                <p className="ratio-label">Disparity Ratio vs Reference Group</p>
                <p className={`ratio-value ${severity}`}>
                  {data.disparity_ratio?.toFixed(1)}x
                </p>
                <p className="muted-text">
                  {formData.domain === 'lending'
                    ? 'Reference baseline: Male Graduate (1.0x)'
                    : 'Reference baseline: White Male, 25-34 (1.0x)'}
                </p>
              </div>

              <div className="bar-row">
                <div className="bar-meta">
                  <span className="muted-text">Your group approval rate</span>
                  <strong>{approvalPct}%</strong>
                </div>
                <AnimatedBar
                  pct={approvalPct}
                  color={severity === 'high' ? 'var(--danger)' : severity === 'medium' ? 'var(--warning)' : 'var(--success)'}
                />
              </div>

              <div className="bar-row">
                <div className="bar-meta">
                  <span className="muted-text">Reference approval rate</span>
                  <strong>{referencePct}%</strong>
                </div>
                <AnimatedBar pct={referencePct} color="var(--text-subtle)" delay={110} />
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', margin: '0.9rem 0' }}>
                <span className={`badge ${data.fourfifths_breach ? 'error' : 'success'}`}>
                  {data.fourfifths_breach ? <AlertTriangle size={12} /> : <CheckCircle size={12} />}
                  {data.fourfifths_breach ? '4/5ths Breach' : 'Within 4/5ths Rule'}
                </span>
                <strong>n = {data.sample_size?.toLocaleString()}</strong>
              </div>

              <div className="meta-line">
                <span className="muted-text">Domain</span>
                <strong style={{ textTransform: 'capitalize' }}>{formData.domain}</strong>
              </div>
              <div className="meta-line">
                <span className="muted-text">Profile</span>
                <strong>{profileLabel}</strong>
              </div>

              {result.explanation && (
                <section className="info-box">
                  <p className="info-label">
                    <Info size={12} />
                    AI Insight
                  </p>
                  <p className="muted-text">{result.explanation}</p>
                </section>
              )}

              <section className="info-box" style={{ marginTop: '1rem' }}>
                <p className="info-label">
                  <Info size={12} />
                  Counterfactual Scenarios
                </p>
                {counterfactuals && counterfactuals.length > 0 ? (
                  <div className="counterfactual-list">
                    {counterfactuals.map((item, index) => (
                      <div key={`${item.changed_attribute}-${index}`} className="counterfactual-card">
                        <p className="muted-text">
                          <strong>{item.changed_attribute.replace(/_/g, ' ')}</strong>
                        </p>
                        <p>{`Changed to: ${item.new_value}`}</p>
                        <p>{`Approval rate: ${Math.round((item.approval_rate || 0) * 100)}%`}</p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="muted-text">No significant counterfactual changes found.</p>
                )}
              </section>
            </div>
          )}
        </article>
      </div>

      <p className="footer-note">
        EquityGuard identifies statistical signals, not legal determinations. Use these outputs as a triage layer before formal policy or legal review.
      </p>
    </section>
  );
}
