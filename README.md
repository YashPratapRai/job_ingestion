# Resilient Job Ingestion Service

A resilient, multi-source job ingestion service built with **Python, FastAPI, SQLAlchemy, and SQLite**.

The system fetches jobs from permitted public job feeds, normalizes heterogeneous source data into a common schema, validates records, prevents duplicates, handles failures through retries and fallback sources, protects unhealthy sources using a circuit breaker, and quarantines malformed records instead of allowing them to break the entire ingestion pipeline.

## Live Demo

🌐 **Live Application:** https://job-ingestion.onrender.com/

📚 **API Documentation:** https://job-ingestion.onrender.com/docs

---

# Architecture

```mermaid
flowchart TD

    A[Himalayas Public Feed] --> B[Source Selection]
    R[RemoteOK Public API] --> B

    B --> C[Retry + Rate Limiting]
    C --> D[Circuit Breaker]

    D --> E[Fetch Raw Jobs]

    E --> F[Normalize]
    F --> G[Validate]

    G -->|Valid| H[Generate Job Key]
    G -->|Invalid| Q[Quarantine]

    H --> I[Deduplication]

    I -->|New Job| J[(SQLite Database)]
    I -->|Duplicate| K[Skip]

    J --> L[FastAPI REST API]

    L --> M[Web Frontend]
    L --> N[Swagger /docs]

    D -. Primary Failure .-> R
End-to-End Flow
                    ┌─────────────────────┐
                    │   Public Job Feeds  │
                    │                     │
                    │  Himalayas          │
                    │  RemoteOK           │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │  Source Selection   │
                    │                     │
                    │ Priority ordered    │
                    │ sources             │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Retry + Rate Limit  │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │  Circuit Breaker    │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │        Fetch        │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │     Normalize       │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │      Validate       │
                    └──────────┬──────────┘
                               │
                    ┌──────────┴──────────┐
                    │                     │
                  Valid                Invalid
                    │                     │
                    ▼                     ▼
             ┌──────────────┐      ┌─────────────┐
             │ Deduplicate  │      │  Quarantine │
             └──────┬───────┘      └─────────────┘
                    │
             ┌──────┴───────┐
             │              │
          New Job        Duplicate
             │              │
             ▼              ▼
        ┌─────────┐       Skip
        │ SQLite  │
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
Key Features
Multi-source job ingestion

Priority-based fallback

Retry handling

Rate limiting

Circuit breaker

Empty-response handling

Source-specific normalization

Pydantic validation

Invalid-record quarantine

Deterministic deduplication

Ingestion run tracking

FastAPI REST API

Lightweight web interface

Automated test suite

Live Render deployment

Source Strategy
The ingestion engine uses a priority-ordered list of sources.

Current source order:

1. Himalayas
2. RemoteOK
The primary source is attempted first.

If it fails, the engine moves to the next available source.

Normal Flow
Himalayas
    │
    ├── Success
    │
    ▼
Process Jobs
Fallback Flow
Himalayas
    │
    ├── Failure
    │
    ▼
RemoteOK
    │
    ├── Success
    │
    ▼
Process Jobs
This prevents a single external source from becoming a single point of failure.

Empty Response vs Failure
An important design decision is to distinguish between:

Source Failure
Examples:

Connection failure

Timeout

HTTP/request exception

Unexpected source exception

A source failure means the source could not successfully provide data.

The next source can therefore be attempted.

Source Failure
      ↓
Try Fallback
Empty Response
A source can successfully respond with zero jobs:

[]
This is not necessarily a failure.

Therefore the system does not automatically treat an empty response as an external request failure.

This distinction avoids unnecessary fallback requests and misleading failure states.

Retry
External sources can experience temporary failures.

The retry mechanism allows transient failures to recover before the system moves on.

Conceptually:

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

Rate Limiting
The service avoids continuously sending requests to public sources.

A rate limiter enforces a minimum interval between requests.

Request
   ↓
Rate Limit Check
   ↓
Wait if necessary
   ↓
Next Request
This reduces unnecessary load on external services and makes the ingestion process more respectful of public feeds.

Circuit Breaker
Retries alone are not sufficient when a source remains unavailable for an extended period.

The circuit breaker tracks source failures independently.

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
The circuit breaker:

Prevents repeatedly hitting an unhealthy source

Reduces unnecessary requests

Allows fallback sources to continue operating

Maintains independent state for different sources

Normalization
Different sources return different data formats.

The normalization layer converts source-specific records into a common JobSchema.

Canonical job structure:

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
This keeps source-specific parsing separate from the database layer.

Validation
Every normalized job is validated before it is stored.

Validation checks include:

Required fields

Field types

Non-empty identifiers

Valid URL

Valid source information

The project uses Pydantic for schema validation.

Invalid records are not inserted into the main jobs table.

Quarantine
A malformed job should not cause the complete ingestion run to fail.

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
The quarantine mechanism records the invalid payload and associated validation errors for later investigation.

This allows valid records from the same ingestion run to continue processing.

Deduplication
Repeated ingestion runs should not create duplicate jobs.

The system creates a deterministic job key from:

source + external_id
The resulting value is hashed using SHA-256.

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
This makes the ingestion process idempotent.

Ingestion Run Tracking
Every ingestion execution creates an IngestionRun.

The run records:

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
This provides basic operational visibility into every ingestion run.

Failure Scenarios
1. Primary Source Succeeds
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
2. Primary Source Fails
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
The original primary-source failure is retained in the ingestion run information.

3. Empty Response
Himalayas
    ↓
Valid response
    ↓
0 jobs
This is treated differently from a request failure.

4. Invalid Job
Source
   ↓
Normalize
   ↓
Validation Failure
   ↓
Quarantine
Other valid jobs continue processing.

5. Repeated Source Failures
Source Failure
      ↓
Source Failure
      ↓
Source Failure
      ↓
Circuit Opens
      ↓
Source Temporarily Skipped
      ↓
Fallback Source
API
Health
GET /health
Returns the current service health.

Jobs
GET /jobs?limit=10
Returns recently stored jobs.

Trigger Ingestion
POST /ingest
Triggers a new ingestion run.

Example:

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
FastAPI automatically exposes interactive API documentation at:

/docs
The live API documentation is available at:

https://job-ingestion.onrender.com/docs

Web Interface
The project includes a lightweight frontend served directly by FastAPI.

The homepage provides:

System status

Stored job count

Run Ingestion button

Latest ingestion result

Recent jobs

Links to original job listings

API documentation

The frontend uses relative API URLs:

fetch("/health")
fetch("/jobs?limit=10")
fetch("/ingest", {
    method: "POST"
})
Therefore frontend and backend are deployed together as a single Render service.

Project Structure
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
Tech Stack
Backend
Python

FastAPI

Uvicorn

Pydantic

SQLAlchemy

Data Sources
Himalayas public job feed

RemoteOK public job API

Database
SQLite

Frontend
HTML

CSS

Vanilla JavaScript

Testing
Pytest

Deployment
Render

Local Setup
1. Clone the repository
git clone <repository-url>
cd job_ingestion
2. Create Virtual Environment
Windows
python -m venv venv
venv\Scripts\activate
Linux / macOS
python3 -m venv venv
source venv/bin/activate
3. Install Dependencies
pip install -r requirements.txt
4. Start the Application
uvicorn app.main:app --reload
Open:

http://localhost:8000
Swagger:

http://localhost:8000/docs
Run Ingestion Locally
The ingestion pipeline can be executed directly using:

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
Running the ingestion again demonstrates deduplication:

INGESTION RESULT
----------------
Run ID: 2
Source: himalayas
Status: SUCCESS
Fetched: 100
Inserted: 0
Skipped: 100
Testing
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

Deployment
The application is deployed as a single Render Web Service.

Build Command
pip install -r requirements.txt
Start Command
uvicorn app.main:app --host 0.0.0.0 --port $PORT
The same service hosts:

FastAPI Backend
      +
Static Frontend
      +
Ingestion Engine
      +
SQLite Database
Live deployment:

https://job-ingestion.onrender.com/

Why SQLite?
SQLite was chosen to keep the project lightweight and easy to run and deploy within the scope of the challenge.

For a production-scale deployment, PostgreSQL would be preferable because it provides:

Better concurrent access

Stronger operational characteristics

Easier scaling

Better support for multiple application instances

Production-grade persistence

Security and Source Boundaries
This project intentionally uses permitted public job feeds rather than attempting to bypass authentication, anti-bot mechanisms, or access controls.

The system does not attempt to scrape private or authenticated job-platform data.

The ingestion design is source-oriented so additional permitted feeds can be added without changing the core processing pipeline.

Production Improvements
Given additional development time, the following improvements would be considered:

PostgreSQL instead of SQLite

Alembic database migrations

Scheduled ingestion

Persistent circuit-breaker state

Structured JSON logging

Metrics and monitoring

Alerting for repeated source failures

Schema-drift detection

More source-specific integration tests

Persistent quarantine storage

Authentication for administrative ingestion endpoints

Distributed locking for concurrent ingestion runs

Better observability dashboards

These are intentionally outside the current scope so that the project remains small, testable, and easy to deploy while demonstrating the core resilient ingestion pattern.

Engineering Principles
The implementation follows these principles:

1. Fail gracefully
A single external source failure should not bring down the complete ingestion pipeline.

2. Validate before persistence
Only normalized and validated records should enter the main jobs table.

3. Quarantine bad data
Malformed records should be preserved separately rather than silently discarded.

4. Avoid unnecessary requests
Rate limiting and circuit breaking prevent repeatedly hitting unhealthy sources.

5. Make ingestion idempotent
Repeated ingestion of the same job should not create duplicate database records.

6. Separate source logic from processing logic
Each source is responsible for fetching its own data while the shared ingestion engine handles normalization, validation, deduplication, and persistence.

7. Keep the system extensible
Additional permitted sources can be added through the common source interface without rewriting the entire ingestion pipeline.

Engineering Outcome
The project demonstrates a resilient ingestion pipeline rather than a simple fetch-and-store script.

Instead of:

Fetch → Insert
the system follows:

                 External Source
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
              ┌────────┴────────┐
              │                 │
            Valid             Invalid
              │                 │
              ▼                 ▼
        Deduplication       Quarantine
              │
              ▼
            SQLite
              │
              ▼
           FastAPI
              │
       ┌──────┴──────┐
       ▼             ▼
   Frontend        API Docs
The result is a small, extensible, and testable foundation for a more production-grade job ingestion platform.
