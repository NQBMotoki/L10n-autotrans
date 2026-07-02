# Repository Guidelines

## Project Structure & Module Organization

This repository is for the `L10n-autotrans` Streamlit demo. Keep the UI orchestration in `app.py` and put reusable logic under `src/`.

Expected layout:

```text
app.py
requirements.txt
.env.example
README.md
sample_data/
  sample_input.csv
  sample_terms.csv
src/
  llm_client.py
  prompts.py
  qa_rules.py
  terminology.py
  exporters.py
  schemas.py
  utils.py
```

Use `sample_data/` only for small demo assets. Add tests under `tests/` when behavior becomes stable, mirroring `src/` module names.

## Build, Test, and Development Commands

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the app locally:

```bash
streamlit run app.py
```

Run tests when available:

```bash
pytest
```

Use mock mode in the Streamlit sidebar for demos without a DeepSeek API key.

## Coding Style & Naming Conventions

Use Python 3 with 4-space indentation, type hints for public helpers, and small functions with clear responsibilities. Prefer `snake_case` for functions, variables, and module names; use `UPPER_SNAKE_CASE` for constants in `src/schemas.py`.

Keep `app.py` focused on Streamlit state, inputs, and rendering. Place API calls in `src/llm_client.py`, prompt assembly in `src/prompts.py`, QA logic in `src/qa_rules.py`, and export logic in `src/exporters.py`.

## Testing Guidelines

Prefer `pytest` for unit tests. Name files `test_<module>.py` and functions `test_<behavior>()`. Prioritize tests for JSON parsing failures, length risk levels, terminology checks, and export generation. Avoid tests that require real API keys; use mock responses or monkeypatch the client.

## Commit & Pull Request Guidelines

No existing Git history is present yet. Use concise Conventional Commit-style messages, for example `feat: add terminology checker` or `fix: handle invalid model JSON`.

Pull requests should include a short summary, manual test steps, screenshots for UI changes, and notes about any `.env` or sample data changes. Never include real API keys or private customer copy in commits.

## Security & Configuration Tips

Store local secrets in `.env`, following `.env.example`. Do not write sidebar-entered API keys to disk. Keep mock mode functional so reviewers can run the full demo without credentials.
