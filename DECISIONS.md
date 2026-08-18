## 1. Why this ingestion strategy?

I chose a priority-ordered, multi-source ingestion strategy using permitted public job feeds, with Himalayas as the primary source and RemoteOK as a fallback.

The obvious alternative was relying on a single source or directly scraping large job platforms. I rejected this because a single source creates a single point of failure, while direct scraping can be brittle and may cross site-specific access or terms-of-use boundaries.

The ingestion pipeline is therefore designed as:

**Fetch → Normalize → Validate → Deduplicate → Store**

with **retry, rate limiting, circuit breaking, fallback, and quarantine** around the ingestion process.

A source failure is treated differently from a valid empty response. A failed source can trigger the next source in priority order, while an empty response does not automatically imply that the source is unavailable.

Malformed records are validated and quarantined instead of being allowed to fail the complete ingestion run.

## 2. Trade-off under the time limit

I chose SQLite for persistence because it kept the implementation lightweight and allowed the complete ingestion service to be developed and deployed quickly without introducing database infrastructure.

With a full week, I would move persistence to PostgreSQL, add database migrations, scheduled ingestion, persistent circuit-breaker state, structured logging and metrics, and expand integration testing around source failures and schema changes.

I also kept the frontend intentionally lightweight because the primary engineering goal of the task was demonstrating a reliable ingestion pipeline rather than building a complex UI.

## 3. Where did I use AI tools?

I used AI tools as a development assistant for architecture brainstorming, debugging, identifying edge cases, and improving test coverage.

I personally verified the generated suggestions by implementing and running the code locally, testing the pipeline against real permitted public feeds, and validating the behavior through automated tests.

During implementation, I changed and verified the design based on actual runtime behavior. This included separating source failures from empty responses, adding validation and quarantine handling, implementing ordered fallback behavior, and integrating circuit-breaker logic.

The final implementation has **15 automated tests passing**, covering retry, rate limiting, normalization, validation, deduplication, empty responses, fallback behavior, quarantine, and circuit-breaker behavior.

The service was also deployed and manually verified through its live FastAPI UI and API documentation.