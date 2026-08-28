# Changelog

All notable changes to this project are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
adheres to [Semantic Versioning](https://semver.org/).

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
