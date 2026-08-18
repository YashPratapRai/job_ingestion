# ⚡ Resilient Job Ingestion Service

A robust, fault-tolerant, multi-source job ingestion service built with **Python**, **FastAPI**, **SQLAlchemy**, and **SQLite**.

The system fetches jobs from permitted public job feeds, normalizes heterogeneous source data into a common schema, validates records, prevents duplicates, handles failures through retries and fallback sources, protects unhealthy sources using a circuit breaker pattern, and quarantines malformed records instead of allowing them to break the entire ingestion pipeline.

---

## 🌐 Live Links

- **Live Application:** [https://job-ingestion.onrender.com/](https://job-ingestion.onrender.com/)
- **Interactive API Docs (Swagger):** [https://job-ingestion.onrender.com/docs](https://job-ingestion.onrender.com/docs)

---

## ✨ Key Features

- **Multi-Source Ingestion:** Ingests raw data from multiple public job feeds (e.g., Himalayas, RemoteOK).
- **Resilience & Fault Tolerance:**
  - Automated retries with rate-limiting.
  - Circuit Breaker pattern to protect unhealthy APIs and trigger source fallbacks.
- **Data Normalization & Validation:** Transforms heterogeneous formats into a unified internal schema.
- **Error Quarantine:** Malformed records are quarantined without blocking the ingestion pipeline.
- **Smart Deduplication:** Unique job key generation to discard duplicate listings before DB writes.
- **FastAPI Backend:** High-performance RESTful endpoints with built-in Swagger/OpenAPI docs.

---

## 🏗️ Architecture

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
