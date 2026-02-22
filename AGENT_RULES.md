# Agent Rules for Future Development

To ensure long-term maintainability, all future AI agents (and human contributors) interacting with this repository MUST adhere to the following rules:

1. **Test-Driven Modifications**: Any new feature, bug fix, or modification must be accompanied by relevant unit tests in the `tests/` directory.
2. **Mandatory Verification**: All changes must be verified (e.g., via `pytest` and manual testing) before being considered complete.
3. **Documentation Sync**: `README.md`, `ROADMAP.md`, `AGENT_RULES.md` and any other relevant documentation (like API specs or architecture notes) must be updated as the final step of *every individual change or PR*. Do not leave documentation updates until the end of a multi-step feature.
4. **Schema Verification First**: Never assume the external database schema (e.g., PocketBase) perfectly matches the internal code models (e.g., Pydantic). If an attribute or column is missing or throwing an error, DO NOT attempt to hack the python code to bypass it. Stop and ask the human to verify the database collection schema.
5. **Iteration Cap**: Do not get stuck in infinite debugging loops. If an error persists or you cannot cleanly resolve a bug within 5 consecutive attempts/modifications, STOP execution and explicitly ask the user for guidance or a review of your approach.
6. **Unified Debugging**: When debugging pipeline or schema issues, ALWAYS update the `tests/integration/test_pipeline_e2e.py` test with the scenarios or diagnostics you want to test instead of creating custom one-off validation scripts.
7. **No Dependency Downgrades**: When evaluating syntax or API problems (especially with newer versions of libraries like PocketBase), NEVER downgrade to an older version of some library or dependency as an attempt to fix the issue. Find the correct syntax for the current version.
8. **Hermetic E2E Tests**: E2E tests MUST run against actual external services (e.g., LM Studio/Ollama) to ensure realism. Do NOT mock external dependencies in `tests/integration/test_pipeline_e2e.py`. State should be hermetic (using temporary directories and isolated database instances), but functional logic must be real.
9. **Local Python Environment**: ALWAYS use the local python environment (`.venv`) within the project directory when running any python commands or scripts.
10. **No Large Binaries**: Never commit real music files (>1MB) to Git. Use small generated silence files for CI specimens.
