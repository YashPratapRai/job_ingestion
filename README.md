
# Resilient Job Ingestion Service

A resilient, multi-source job ingestion service built with **Python, FastAPI, SQLAlchemy, Pydantic, and SQLite**.

The service fetches jobs from permitted public job feeds, normalizes different source formats into a common schema, validates records, prevents duplicates, handles source failures with retry and fallback mechanisms, protects unhealthy sources using a circuit breaker, and quarantines malformed records without stopping the complete ingestion run.

---

## 🌐 Live Demo

**Live Application:**  
https://job-ingestion.onrender.com/

**Interactive API Documentation:**  
https://job-ingestion.onrender.com/docs

---

## ✨ Features

- Multi-source job ingestion
- Priority-based source fallback
- Retry handling for transient failures
- Rate limiting
- Circuit breaker
- Empty-response handling
- Source-specific normalization
- Pydantic-based validation
- Invalid-record quarantine
- Deterministic SHA-256 deduplication
- Idempotent ingestion
- Ingestion run tracking
- FastAPI REST API
- Lightweight web dashboard
- Automated test suite
- Render deployment

---

# 🏗️ Architecture

```mermaid
flowchart TD

    A[Himalayas Public Feed] --> B[Priority Source Selection]
    R[RemoteOK Public API] --> B

    B --> C[Retry + Rate Limiting]
    C --> D[Circuit Breaker]

    D --> E[Fetch Raw Jobs]

    E --> F[Normalize]
    F --> G[Validate]

    G -->|Valid| H[Generate Deterministic Job Key]
    G -->|Invalid| Q[Quarantine]

    H --> I[Deduplication]

    I -->|New| J[(SQLite Database)]
    I -->|Duplicate| K[Skip]

    J --> L[FastAPI]

    L --> M[Web Dashboard]
    L --> N[Swagger /docs]

    D -. Primary Failure .-> R

                    ┌───────────────────────┐
                    │    Public Job Feeds   │
                    │                       │
                    │ Himalayas   RemoteOK  │
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │  Priority Selection   │
                    │                       │
                    │ Primary → Fallback    │
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │   Retry + Rate Limit  │
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │    Circuit Breaker    │
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │        Fetch          │
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │      Normalize       │
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │       Validate        │
                    └───────────┬───────────┘
                                │
                    ┌───────────┴───────────┐
                    │                       │
                  Valid                  Invalid
                    │                       │
                    ▼                       ▼
             ┌──────────────┐       ┌──────────────┐
             │ Deduplication│       │  Quarantine  │
             └──────┬───────┘       └──────────────┘
                    │
             ┌──────┴───────┐
             │              │
          New Job        Duplicate
             │              │
             ▼              ▼
        ┌─────────┐        Skip
        │  SQLite │
        └────┬────┘
             │
             ▼
        ┌─────────┐
        │ FastAPI │
        └────┬────┘
             │
       ┌─────┴─────┐
       ▼           ▼
   Frontend      /docs

🌐 Source Strategy
The ingestion engine uses a priority-ordered multi-source strategy.

Current sources:

Priority 1 → Himalayas
Priority 2 → RemoteOK
The engine attempts sources in priority order.

Normal Flow
Himalayas
    ↓
Fetch succeeds
    ↓
Use Himalayas
    ↓
Process jobs
Fallback Flow
Himalayas
    ↓
Failure
    ↓
RemoteOK
    ↓
Success
    ↓
Process jobs
This prevents a single external source from becoming a single point of failure.

The source abstraction also makes it possible to add additional permitted feeds without rewriting the ingestion pipeline.

⚠️ Empty Response vs Source Failure
A valid empty response and a request failure represent different situations.

Source Failure
Examples:

Network error

Connection failure

Timeout

HTTP/request exception

Unexpected source exception

A failed source can cause the engine to attempt the next source.

Source Failure
      ↓
Try Fallback
Empty Response
A source may successfully return zero jobs:

[]
This is not automatically treated as a source outage.

Valid Empty Response
        ↓
Do not classify as request failure
This distinction avoids unnecessary fallback requests and misleading failure signals.

🔁 Retry
External services can experience temporary failures.

The retry mechanism allows transient failures to recover before the source is abandoned.

Attempt 1
   ↓
Failure
   ↓
Retry
   ↓
Attempt 2
   ↓
Failure
   ↓
Retry
   ↓
Attempt 3
   ↓
Success
Retry behavior is covered by automated tests.

⏱️ Rate Limiting
The ingestion system enforces a minimum interval between requests.

Request
   ↓
Rate Limit Check
   ↓
Wait if required
   ↓
Next Request
This helps avoid excessive requests to public sources and keeps the ingestion process respectful of source constraints.

🔌 Circuit Breaker
Retries alone are not sufficient if a source remains unavailable.

The circuit breaker tracks failures independently for each source.

             ┌─────────────┐
             │   CLOSED    │
             │   Normal    │
             └──────┬──────┘
                    │
              Failure Threshold
                    │
                    ▼
             ┌─────────────┐
             │    OPEN     │
             │ Skip Source │
             └──────┬──────┘
                    │
                 Cooldown
                    │
                    ▼
             ┌─────────────┐
             │  HALF-OPEN  │
             │ Test Source │
             └──────┬──────┘
                    │
              ┌─────┴─────┐
              │           │
           Success      Failure
              │           │
              ▼           ▼
           CLOSED        OPEN
Benefits:

Prevents repeatedly hitting an unhealthy source

Reduces unnecessary requests

Allows fallback sources to continue operating

Maintains independent state for different sources

🧹 Normalization
Different job sources can return different structures and formats.

The normalization layer converts source-specific records into a common JobSchema.

Canonical Job Schema
external_id
title
company
location
description
url
published_at
source
Conceptually:

Himalayas Data ──┐
                 ├──> Normalizer ──> JobSchema
RemoteOK Data ───┘
This keeps source-specific logic isolated from the rest of the pipeline.

✅ Validation
Every normalized job is validated before persistence.

Validation checks include:

Required fields exist

external_id is a string

title is a string

url is valid

source is a string

Required identifiers are not empty

Pydantic is used for schema-level validation.

Invalid records are not inserted into the main jobs table.

🗃️ Quarantine
Malformed records should not cause the complete ingestion run to fail.

Instead:

Raw Job
   ↓
Normalize
   ↓
Validate
   ↓
Invalid
   ↓
Quarantine
The quarantine mechanism preserves the invalid payload along with the associated validation errors.

This allows valid records from the same ingestion run to continue processing.

♻️ Deduplication
Repeated ingestion runs should not create duplicate jobs.

A deterministic job key is generated using:

source + external_id
The combined value is hashed using SHA-256.

source + external_id
        ↓
      SHA-256
        ↓
     job_key
The job_key is unique in the database.

First ingestion
Job
 ↓
New job_key
 ↓
INSERT
Repeated ingestion
Same Job
 ↓
Same job_key
 ↓
Already exists
 ↓
SKIP
This makes ingestion idempotent.

📊 Ingestion Run Tracking
Every ingestion execution creates an IngestionRun.

A run records:

Run ID

Source

Status

Start time

Completion time

Records fetched

Records inserted

Records skipped

Error information

Example:

INGESTION RESULT
----------------
Run ID: 3
Source: himalayas
Status: SUCCESS
Fetched: 100
Inserted: 21
Skipped: 79
This provides basic operational visibility into ingestion behavior.

🚨 Failure Scenarios
Primary Source Succeeds
Himalayas
    ↓
Success
    ↓
Normalize
    ↓
Validate
    ↓
Deduplicate
    ↓
Store
Status:

SUCCESS
Primary Source Fails
Himalayas
    ↓
Failure
    ↓
RemoteOK
    ↓
Success
    ↓
Process Jobs
Status:

SUCCESS_FALLBACK
The primary failure is retained in the ingestion run information.

Empty Response
Himalayas
    ↓
Valid response
    ↓
0 jobs
This is handled differently from a request failure.

Invalid Job
Source
   ↓
Normalize
   ↓
Validation Failure
   ↓
Quarantine
Other valid jobs continue processing.

Repeated Source Failures
Failure
   ↓
Failure
   ↓
Failure
   ↓
Circuit Opens
   ↓
Source Temporarily Skipped
   ↓
Fallback Source
🌐 API
Health Check
GET /health
Returns the current service health.

List Jobs
GET /jobs?limit=10
Returns recently stored jobs.

Trigger Ingestion
POST /ingest
Triggers a new ingestion run.

Example response:

{
  "status": "SUCCESS",
  "source": "himalayas",
  "fetched": 100,
  "inserted": 21,
  "skipped": 79
}
Ingestion Runs
GET /runs
Returns previous ingestion run information.

Swagger Documentation
FastAPI provides interactive API documentation at:

/docs
Live:

https://job-ingestion.onrender.com/docs

🖥️ Web Interface
The project includes a lightweight frontend served directly by FastAPI.

The dashboard provides:

System status

Stored job count

Run Ingestion button

Latest ingestion result

Recent jobs

Original job listing links

API documentation link

The frontend uses relative API URLs:

fetch("/health");
fetch("/jobs?limit=10");

fetch("/ingest", {
    method: "POST"
});
Therefore frontend and backend are deployed together as a single Render service.

📁 Project Structure
job_ingestion/
│
├── app/
│   ├── api/
│   │   ├── health.py
│   │   ├── jobs.py
│   │   ├── ingestion.py
│   │   └── runs.py
│   │
│   ├── ingestion/
│   │   ├── engine.py
│   │   ├── normalizer.py
│   │   ├── validator.py
│   │   ├── retry.py
│   │   ├── rate_limiter.py
│   │   ├── circuit_breaker.py
│   │   └── quarantine.py
│   │
│   ├── models/
│   │   ├── job.py
│   │   ├── ingestion_run.py
│   │   └── schemas.py
│   │
│   ├── sources/
│   │   ├── base.py
│   │   ├── himalayas_source.py
│   │   └── remoteok_source.py
│   │
│   ├── config.py
│   ├── database.py
│   └── main.py
│
├── static/
│   ├── index.html
│   ├── style.css
│   └── app.js
│
├── tests/
│   ├── test_deduplication.py
│   ├── test_empty_response.py
│   ├── test_fallback.py
│   ├── test_normalizer.py
│   ├── test_rate_limiter.py
│   ├── test_retry.py
│   ├── test_validator.py
│   ├── test_quarantine.py
│   ├── test_circuit_breaker.py
│   └── test_circuit_breaker_integration.py
│
├── run_ingestion.py
├── requirements.txt
├── pytest.ini
├── DECISIONS.md
├── .env.example
└── README.md
🛠️ Tech Stack
Layer	Technology
Language	Python
API	FastAPI
Server	Uvicorn
Validation	Pydantic
ORM	SQLAlchemy
Database	SQLite
Public Sources	Himalayas, RemoteOK
Frontend	HTML, CSS, Vanilla JavaScript
Testing	Pytest
Deployment	Render
🚀 Local Setup
1. Clone the repository
git clone <repository-url>
cd job_ingestion
2. Create a virtual environment
Windows
python -m venv venv
venv\Scripts\activate
Linux / macOS
python3 -m venv venv
source venv/bin/activate
3. Install dependencies
pip install -r requirements.txt
4. Start the application
uvicorn app.main:app --reload
Open:

http://localhost:8000
Swagger:

http://localhost:8000/docs
▶️ Run Ingestion Locally
The ingestion pipeline can also be executed directly:

python run_ingestion.py
Example first run:

INGESTION RESULT
----------------
Run ID: 1
Source: himalayas
Status: SUCCESS
Fetched: 100
Inserted: 100
Skipped: 0
Running it again demonstrates deduplication:

INGESTION RESULT
----------------
Run ID: 2
Source: himalayas
Status: SUCCESS
Fetched: 100
Inserted: 0
Skipped: 100
🧪 Testing
Run the complete test suite:

python -m pytest -v
Current result:

15 passed
The test suite covers:

✓ Retry behavior
✓ Rate limiting
✓ Normalization
✓ Validation
✓ Deduplication
✓ Empty responses
✓ Primary/fallback behavior
✓ Quarantine
✓ Circuit breaker
✓ Circuit breaker integration
The tests verify both individual resilience components and important ingestion-engine behavior.

☁️ Deployment
The application is deployed as a single Render Web Service.

Build Command
pip install -r requirements.txt
Start Command
uvicorn app.main:app --host 0.0.0.0 --port $PORT
The same Render service hosts:

FastAPI Backend
      +
Static Frontend
      +
Ingestion Engine
      +
SQLite Database
Live deployment:

https://job-ingestion.onrender.com/

💾 Database Choice
SQLite was chosen to keep the project lightweight and easy to run and deploy within the scope of the challenge.

For a production-scale deployment, PostgreSQL would be preferable because of:

Better concurrent access

Stronger persistence characteristics

Easier horizontal scaling

Better multi-instance support

Production-grade database operations

🔐 Source and Access Boundaries
The project intentionally uses permitted public job feeds.

It does not attempt to:

Bypass authentication

Circumvent anti-bot protections

Access private job data

Scrape authenticated user accounts

Evade access controls

The source abstraction is designed so that additional permitted public sources can be integrated safely.

📈 Production Improvements
With additional development time, the following improvements would be considered:

PostgreSQL instead of SQLite

Alembic database migrations

Scheduled ingestion

Persistent circuit-breaker state

Structured JSON logging

Metrics and monitoring

Alerts for repeated source failures

Schema-drift detection

More source-specific integration tests

Persistent quarantine storage

Authentication for administrative ingestion endpoints

Distributed locking for concurrent ingestion runs

Observability dashboards

These improvements are intentionally outside the current scope so that the project remains lightweight, testable, and deployable while demonstrating the core resilient ingestion architecture.

🎯 Engineering Principles
Fail Gracefully
A single external source failure should not bring down the entire ingestion pipeline.

Validate Before Persistence
Only normalized and validated records should enter the main jobs table.

Quarantine Bad Data
Malformed records should be preserved separately instead of silently discarded or crashing the pipeline.

Avoid Unnecessary Requests
Rate limiting and circuit breaking prevent repeatedly hitting unhealthy sources.

Make Ingestion Idempotent
Repeated ingestion of the same job should not create duplicate database records.

Separate Source and Processing Logic
Sources are responsible for fetching source-specific data while the ingestion engine handles normalization, validation, deduplication, and persistence.

Keep the System Extensible
Additional permitted sources can be added through the common source interface without rewriting the core pipeline.

🏁 Final Outcome
This project demonstrates a resilient ingestion pipeline rather than a simple fetch-and-store script.

Instead of:

Fetch → Insert
the system follows:

                External Job Source
                        │
                        ▼
                Source Selection
                        │
                        ▼
                Retry + Rate Limit
                        │
                        ▼
                 Circuit Breaker
                        │
                        ▼
                      Fetch
                        │
                        ▼
                    Normalize
                        │
                        ▼
                     Validate
                        │
                  ┌─────┴─────┐
                  │           │
                Valid       Invalid
                  │           │
                  ▼           ▼
             Deduplicate  Quarantine
                  │
                  ▼
                SQLite
                  │
                  ▼
                FastAPI
                  │
             ┌────┴────┐
             ▼         ▼
         Frontend    Swagger


    L --> N[Swagger /docs]

    D -. Primary Failure .-> R
