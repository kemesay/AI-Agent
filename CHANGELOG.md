# Changelog

All notable changes to this project are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- Under/over-invoicing price checker for the Product & HS Code Compliance category
  (`reference_data/customs_prices.py`, `scoring/price_deviation.py`): compares an invoice's
  declared unit price against a bundled customs indicative-price reference workbook
  (overridable via `CUSTOMS_PRICE_LIST_PATH`), matched by HS code and description similarity,
  flagging prices suspiciously below (duty evasion) or above (trade-based money-laundering)
  the reference. Works with zero deployment setup — the workbook ships with the package — and
  silently no-ops if no confident match is found, so it never reads as a false finding.
- Docker Compose deployment (`docker-compose.yml`): `docker compose up -d --build` builds and
  runs the service, exposing it on a configurable `HOST_PORT` (default 8050).

### Changed

- Agents 4-9 (the six risk-dimension analysts) now run as direct Python calls instead of
  CrewAI/LLM agents, cutting a full `/analyze_proforma` analysis from ~15-17 Gemini API calls
  to ~3 — the deterministic scoring logic was unchanged, only the orchestration layer.
- Default Gemini model updated after `gemini-2.5-flash` was retired by Google.

### Fixed

- `RiskAssessmentCrew.crew().kickoff()` is now called via `kickoff_async()` from the async
  FastAPI route, avoiding a crash when CrewAI detects it's already inside a running event loop.
- A task guardrail's success value must be a raw string, not a `TaskOutput`, for CrewAI to
  re-run `output_pydantic` conversion — returning the object directly silently skipped
  conversion, so a correctly tool-called aggregation could still report as unvalidated.

## [0.1.0] - 2026-08-28

### Added

- Initial release: 11-agent multi-agent architecture for proforma invoice risk assessment.
- Multimodal document ingestion, normalization, and extraction (Agents 1-3) via Google Gemini.
- Deterministic risk-scoring engine covering invoice integrity, supplier legitimacy, payment and
  currency risk, product and HS code compliance, logistics and incoterms, and purpose validation
  (Agents 4-9).
- CrewAI-orchestrated risk aggregation and executive summary agents (Agents 10-11).
- FastAPI service exposing `/extract`, `/extract_proforma`, and `/analyze_proforma`.
- Test suite covering the scoring engine and API layer.
- Docker image, GitHub Actions CI workflow, and project documentation.
