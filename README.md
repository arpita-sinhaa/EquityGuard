# EquityGuard

A Fairness Intelligence Platform for Algorithmic Decision Systems

---

## Overview

EquityGuard is a full-stack fairness analytics platform designed to detect and explain statistical indications of bias in real-world decision systems.

It provides:

* Citizen-level checks for individual transparency
* Organization-level audits for systemic bias detection
* Cloud-backed analytics using Google BigQuery
* Explainability layer powered by LLMs (OpenRouter)

---

## Problem Statement

Modern algorithmic systems influence hiring, lending, and other high-stakes decisions. However, these systems often operate as black boxes, making it difficult to detect:

* Disparities across demographic groups
* Violations of fairness standards (e.g., four-fifths rule)
* Systemic bias in historical decisions

EquityGuard addresses this by combining statistical fairness metrics with clear, interpretable explanations.

---

## Core Features

### Citizen Bias Check

* Accepts user demographic inputs
* Retrieves historical decision statistics
* Returns:

  * Approval rate
  * Disparity ratio
  * Four-fifths rule evaluation
  * Plain-language explanation

---

### Organization Audit

* Accepts bulk decision records (CSV / JSON)
* Aggregates decisions into intersectional slices
* Detects statistically significant bias
* Outputs:

  * Flagged demographic groups
  * Priority levels (low / medium / high)
  * Remediation guidance

---

## System Architecture

```plaintext
User Input → React Frontend → FastAPI Backend → BigQuery → Fairness Engine → LLM Explanation
```

### Key Layers:

* Frontend: React + Vite
* Backend: FastAPI (Python)
* Data Layer: Google BigQuery
* Explainability: OpenRouter (LLM abstraction)

---

## Data Pipelines

### Hiring Domain

* Dataset: UCI Adult Census Income
* Script: `preprocess_hiring.py`
* Output: `hiring_bias_data.csv`
* Features:

  * sex, race, age_group

---

### Lending Domain

* Dataset: Loan Prediction Dataset (Kaggle)
* Source: https://www.kaggle.com/datasets/altruistdelhite04/loan-prediction-problem-dataset/data
* Script: `preprocess_lending.py`
* Output: `lending_bias_data.csv`
* Features:

  * gender, education, income_group

---

## Lending Income Normalization

To ensure comparability, raw income values are grouped into normalized buckets:

| Income Group | Range (INR)    |
| ------------ | -------------- |
| low          | 0 – 3,000      |
| mid          | 3,001 – 6,000  |
| high         | 6,001 – 10,000 |
| very_high    | 10,000+        |

---

## BigQuery Data Model

Dataset: `bias_stats`

### Hiring Table

```
intersectional_slices
```

Columns:

* sex, race, age_group
* approval_rate, disparity_ratio, sample_size

---

### Lending Table

```
lending_bias_data
```

Columns:

* Gender, Education, income_group
* approval_rate, disparity_ratio, sample_size

---

## Backend Setup

### 1. Create environment

```bash
cd backend
python -m venv venv
.\venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install fastapi uvicorn python-dotenv google-cloud-bigquery pandas
```

### 3. Configure environment

Create `backend/.env`:

```env
USE_MOCK_DATA=false
GOOGLE_APPLICATION_CREDENTIALS_JSON={...service account json...}

OPENROUTER_API_KEY=your_key
OPENROUTER_API_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL=openrouter/auto
```

### 4. Run backend

```bash
uvicorn app.main:app --reload
```

---

## Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Open:

```
http://localhost:5173
```

---

## API Endpoints

### Citizen Bias Check

```
POST /check-bias
```

#### Hiring Example:

```json
{
  "domain": "hiring",
  "sex": "Female",
  "race": "Black",
  "age_group": "45-54"
}
```

#### Lending Example:

```json
{
  "domain": "lending",
  "gender": "Female",
  "education": "Graduate",
  "income_group": "mid"
}
```

---

### Organization Audit

```
POST /audit
```

```json
{
  "domain": "lending",
  "decisions": [
    {
      "gender": "Female",
      "education": "Graduate",
      "income_group": "mid",
      "outcome": 0
    }
  ]
}
```

---

## Fairness Methodology

* Disparity Ratio: compares group approval rates against a reference group
* Four-Fifths Rule: detects under-selection (< 80%)
* Sample Size Filtering: avoids unreliable statistical conclusions

Priority classification:

* High: disparity > 3
* Medium: disparity > 1.5
* Low: otherwise

---

## Runtime Behavior

* `USE_MOCK_DATA=true` → uses mock data
* `USE_MOCK_DATA=false` → queries BigQuery
* LLM fallback triggers if API key is not configured

---

## Troubleshooting

### BigQuery errors

* Verify credentials path
* Ensure correct IAM permissions

### No results returned

* Check if slice exists in dataset
* Verify correct casing of fields

### LLM errors

* Validate API key
* Use fallback model if needed

---

## Current Status

* Dual-domain support (Hiring + Lending)
* Real-world datasets integrated
* BigQuery production pipeline
* Organization audit functionality implemented

---

## Future Enhancements

* Interactive bias visualization dashboards
* Additional domains (insurance, education, healthcare)
* Time-based drift analysis
* Role-based access for organizations

---

## Author

Krishita Garg

---

## Summary

EquityGuard enables transparent, explainable, and auditable decision systems by combining statistical fairness analysis with accessible insights for both individuals and organizations.
