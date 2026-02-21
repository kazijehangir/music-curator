# Agent Rules for Future Development

To ensure long-term maintainability, all future AI agents (and human contributors) interacting with this repository MUST adhere to the following rules:

1. **Test-Driven Modifications**: Any new feature, bug fix, or modification must be accompanied by relevant unit tests in the `tests/` directory.
2. **Mandatory Verification**: All changes must be verified (e.g., via `pytest` and manual testing) before being considered complete.
3. **Documentation Sync**: `README.md`, `ROADMAP.md`, `AGENT_RULES.md` and any other relevant documentation (like API specs or architecture notes) must be updated as the final step of *every individual change or PR*. Do not leave documentation updates until the end of a multi-step feature.
4. **Schema Verification First**: Never assume the external database schema (e.g., PocketBase) perfectly matches the internal code models (e.g., Pydantic). If an attribute or column is missing or throwing an error, DO NOT attempt to hack the python code to bypass it. Stop and ask the human to verify the database collection schema.
