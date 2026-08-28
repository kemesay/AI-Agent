# Contributing

Thanks for your interest in improving Trade Service Agents.

## Development setup

```bash
python3 -m venv .venv
source .venv/bin/activate
make install
cp .env.example .env   # set GENAI_API_KEY
```

## Workflow

1. Create a feature branch off `main`.
2. Make your change, keeping scoring logic (`src/trade_service_agents/scoring/`) pure and
   deterministic — no network or LLM calls in that layer.
3. Add or update tests under `tests/`.
4. Run `make lint` and `make test` before opening a pull request.
5. Follow [Conventional Commits](https://www.conventionalcommits.org/) for commit messages
   (`feat:`, `fix:`, `docs:`, `test:`, `chore:`, `ci:`, `refactor:`).

## Adding a new risk-assessment agent

1. Add a pure scoring function under `src/trade_service_agents/scoring/`.
2. Wrap it as a `@tool` in `src/trade_service_agents/agents/tools.py`.
3. Define the agent's role/goal/backstory in `agents/config/agents.yaml` and its task in
   `agents/config/tasks.yaml`.
4. Wire the agent and task into `agents/crew.py`, including it in the aggregation task's
   `context` list.
5. Add unit tests for the scoring function and update `docs/ARCHITECTURE.md`.

## Reporting issues

Use the issue templates under `.github/ISSUE_TEMPLATE/` for bug reports and feature requests.
