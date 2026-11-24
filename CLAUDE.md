# Flight agent: notes for Claude Code

Course capstone (AgentOps). The owner is a beginner: keep code short, commented and easy to explain.

- Python package in `flight_agent/`; run with `python -m flight_agent "<trip>"`.
- Workflow steps live in `flight_agent/agent.py` (`STEPS` list); all model calls go through `flight_agent/llm.py`.
- Settings in `config.yaml`; prompts in `flight_agent/prompts.py` (bump `prompt_version` when prompts change).
- Never hardcode or commit the API key; it comes from `FLIGHT_AGENT_API_KEY`.
- Run `python -m pytest -q` before every commit (free, uses a fake LLM).
- Eval runs cost real money: ask the owner before running `python -m evals.run_evals`.
- Every change goes on a branch with a pull request.
