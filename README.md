# EquityGuard

EquityGuard is a full-stack fairness analytics application for:

1. Citizen-level bias checks (single profile lookup)
2. Organization-level audits (batch decision analysis)

It supports both hiring and lending domains, uses BigQuery for production data lookup, and can generate plain-language insight text through OpenRouter.

## What the app does

1. Citizen Check
- Accepts demographic/profile inputs
- Finds matching historical slice stats
- Returns approval rate, disparity ratio, 4/5ths rule status, and explanation

2. Organization Audit
- Accepts bulk decision records
- Detects flagged slices
- Returns prioritized remediation guidance and summary

## Project structure

EquityGuard/
- backend/
	- app/
		- main.py
		- routes/
		- services/
		- models/
- frontend/
	- src/
		- pages/
		- services/
- preprocess_hiring.py
- preprocess_lending.py
- hiring_bias_data.csv
- lending_bias_data.csv

## Tech stack

- Backend: FastAPI
- Frontend: React + Vite
- Data: Google BigQuery
- LLM insight layer: OpenRouter Chat Completions API

## Data pipeline inputs

1. Hiring pipeline source
- Adult income-style dataset
- Script: preprocess_hiring.py
- Output: hiring_bias_data.csv

2. Lending pipeline source
- Kaggle Loan Prediction dataset
- Source reference: https://www.kaggle.com/datasets/altruistdelhite04/loan-prediction-problem-dataset/data
- Script: preprocess_lending.py
- Output: lending_bias_data.csv

## Lending input mapping

The lending citizen flow uses these fields:

- gender
- education
- income_group

Income group ranges used in UI and request docs:

- low: INR 0 to 3,000
- mid: INR 3,001 to 6,000
- high: INR 6,001 to 10,000
- very_high: above INR 10,000

## BigQuery tables expected

Dataset: bias_stats

1. Hiring table
- intersectional_slices
- key fields: sex, race, age_group

2. Lending table
- lending_bias_data
- key fields: Gender, Education, income_group

## Backend setup

From project root:

1. Create and activate environment

	 Windows PowerShell:
	 cd backend
	 python -m venv venv
	 .\venv\Scripts\Activate

2. Install dependencies

	 pip install fastapi uvicorn python-dotenv google-cloud-bigquery pandas

3. Configure backend environment

	 Create backend/.env with values like:

	 USE_MOCK_DATA=false  
     GOOGLE_APPLICATION_CREDENTIALS=/path/to/your/credentials.json

	 OPENROUTER_API_KEY=your_openrouter_key  
	 OPENROUTER_API_URL=https://openrouter.ai/api/v1  
	 OPENROUTER_MODEL=openrouter/auto  

4. Run backend

	 .\venv\Scripts\python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

Backend docs:

- Swagger UI: http://localhost:8000/docs

## Frontend setup

From project root:

1. Install and run frontend

	 cd frontend
	 npm install
	 npm run dev

2. Open app

	 http://localhost:5173

## API examples

1. Citizen check (hiring)

POST /check-bias

{
	"domain": "hiring",
	"sex": "Female",
	"race": "Black",
	"age_group": "45-54"
}

2. Citizen check (lending)

POST /check-bias

{
	"domain": "lending",
	"gender": "Female",
	"education": "Graduate",
	"income_group": "mid"
}

3. Organization audit

POST /audit

{
	"domain": "hiring",
	"decisions": [
		{
			"sex": "Female",
			"race": "Black",
			"age_group": "45-54",
			"outcome": 0
		}
	]
}

## Runtime behavior notes

1. Mock vs BigQuery
- USE_MOCK_DATA=true forces mock responses
- USE_MOCK_DATA=false uses BigQuery lookups

2. Minimum sample-size checks in citizen route
- Hiring requires sample_size >= 100
- Lending requires sample_size >= 50

3. OpenRouter fallback behavior
- If OPENROUTER_API_KEY is missing, explanation methods return fallback text
- If OpenRouter rejects request, backend logs OpenRouter error details

## Troubleshooting

1. CREDENTIAL PATH is None
- Ensure backend/.env exists
- Ensure GOOGLE_APPLICATION_CREDENTIALS points to a real JSON file
- Restart backend process fully

2. Still seeing mock data
- Confirm USE_MOCK_DATA=false in backend/.env
- Restart backend after env change

3. OpenRouter returns provider error
- Verify OPENROUTER_API_KEY
- Verify OPENROUTER_API_URL is https://openrouter.ai/api/v1
- Try OPENROUTER_MODEL=openrouter/auto

4. Frontend cannot start
- Run npm install in frontend
- Ensure backend is up on port 8000

## Current status

The backend and frontend are wired for dual-domain citizen checks and organization audits, with lending-specific inputs aligned to the lending CSV pipeline fields.