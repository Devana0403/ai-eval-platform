# AI Software Engineering Evaluation Platform

An evaluation platform that takes a coding task, generates a candidate solution with an LLM (Google Gemini), runs that solution inside an isolated sandbox, grades it against tests, classifies *why* it failed if it failed, and can benchmark the same process across many tasks at once.

Built to explore automated evaluation, sandboxed execution, failure analysis, and reproducible benchmarking of LLM-generated software.
**Live demo:** https://victorious-glacier-079dc1610.3.azurestaticapps.net
**API:** https://ai-eval-platform-api.azurewebsites.net

> **Note on the live deployment:** This is deployed on Azure's free-tier trial. Azure's $200 credit and trial subscription are disabled 30 days after account creation (or when the credit runs out, whichever comes first), so the hosted version may stop working after that window unless the Azure subscription is upgraded. The Static Web App (frontend) runs on Azure's permanent free tier and should keep working regardless. To verify full functionality at any time, clone this repo and run it locally — see **Running Locally** below.

---

## What it does

1. A user submits a coding task (a description + a function name).
2. The task's correctness criteria can be defined three ways:
   - Write raw Python test/assert code yourself.
   - Give plain-English input → output examples (e.g. `2, 3 -> 5`), which get compiled into test code automatically.
   - Let the LLM generate its own test suite from the description.
3. The platform sends the task to Gemini, which generates a candidate solution.
4. The candidate solution is executed inside an isolated, locked-down sandbox (no network access, memory/CPU limits, non-root user, enforced timeout).
5. The sandbox result is graded: pass/fail, plus a **failure taxonomy** label if it failed (`syntax_error`, `logic_error`, `api_misuse`, `timeout`, `runtime_error`).
6. Everything is stored: tasks, generated solutions, and every evaluation run (so a solution can be re-evaluated without losing history — useful for checking flakiness).
7. A benchmark runner can loop this whole pipeline across every task in the database at once and return a pass rate + failure breakdown, tagged with a label (e.g. `gemini-2.5-flash-baseline`) so different runs/models can be compared later.

## Architecture

```
Frontend (HTML/JS)  →  FastAPI backend  →  Gemini API (solution + test generation)
   Azure Static           Azure App              →  Sandbox (local Docker OR
   Web Apps                Service                    Azure Container Instances)
                               ↓
                       Azure Postgres
                       Flexible Server
```

**Local ↔ cloud dispatcher pattern:** both the sandbox and the database have a local implementation (Docker / local Postgres) and a cloud implementation (Azure Container Instances / Azure Postgres), switched with a single environment variable (`SANDBOX_BACKEND`, `DB_BACKEND`). The rest of the app never knows which one it's talking to. This was a deliberate choice, not an afterthought — see "Engineering decisions" below.

**Graceful Azure degradation:** if the Azure sandbox backend is unavailable (e.g. after the free-tier trial ends), it doesn't crash the app — it returns a normal-looking failed evaluation with a clear message telling the reader to run locally instead, which the frontend already knows how to display.

## Key features

- **Three test-authoring modes** for different skill levels: raw code, input/output examples, or fully AI-generated tests — decided per-task at creation time.
- **Property-based testing** via Hypothesis, running inside a custom sandbox image with Hypothesis pre-installed. Demonstrated catching a bug (`add(0, -1)`) that a fixed-example test would have missed.
- **Failure taxonomy**, not just pass/fail — the grader inspects stderr to classify *why* something failed.
- **Sandbox security model**: `--network none`, memory and CPU caps, non-root execution, read-only code mount, and an enforced timeout (checked via exit code 124, the Unix convention for a `timeout`-killed process).
- **Benchmark runner**: loops generate → evaluate across every task with test code, returns pass rate and a failure-type breakdown, tagged to a labeled run for later comparison.
- **Defensive API design**: proper HTTP status codes (404/400) instead of 200-with-an-error-in-the-body, plus an optional `expected_task_id` guard on evaluation to catch human mix-ups between solution and task IDs.

## Tech stack

Python, FastAPI, SQLAlchemy, PostgreSQL, Docker, Google Gemini API, Hypothesis, vanilla HTML/JS/CSS frontend, Azure (App Service, Container Instances, Container Registry, Postgres Flexible Server, Static Web Apps).

## Engineering decisions worth noting

- **Azure Container Instances over AKS for the sandbox.** ACI is pay-per-second with no idle cost; AKS requires always-on worker VMs, which would mean paying for idle compute most of the day given this workload's bursty, one-off nature. AKS would make sense if this became a high-traffic multi-tenant service — it's the natural next scaling step, just not the right choice at this scale.
- **Local/cloud dispatcher for both sandbox and database**, rather than hardcoding either — this means the app can run entirely offline for grading purposes, and the same code path is used whether you're testing locally or hitting the deployed version.
- **`function_name` is a required field**, not optional — early on, allowing it to be blank meant the LLM invented its own function name that didn't match the test code checking for it. Requiring it up front avoids a whole category of silent failures.
- **Restricting task edits to `test_code` only.** Once solutions exist for a task, changing the description would make old evaluations misleading against a task that no longer describes what they solved.

## Problems hit and fixed along the way

- **Port conflicts**: a native Postgres install (Postgres.app/Homebrew) already had port 5432. Fixed by remapping the Docker container's external port instead of hunting down and stopping the native service.
- **Model deprecation**: `gemini-2.0-flash` was fully retired mid-project; switched to the current `gemini-2.5-flash` and learned to pin explicit versions rather than "latest" aliases, which can silently swap underlying models.
- **Cross-architecture image mismatch**: a Docker image built on an Apple Silicon (ARM64) Mac failed on Azure Container Instances, which only supports `linux/amd64`. Fixed with `docker build --platform linux/amd64`.
- **Conda-contaminated `requirements.txt`**: running `pip freeze` from the wrong environment (`(base)` Conda instead of the project's `venv`) captured hundreds of unrelated packages, including one with a literal local filesystem path — which made the Azure build fail with a file-not-found error, since that path obviously didn't exist on Azure's build servers.
- **Azure free-trial region restrictions**: Postgres Flexible Server creation failed in `eastus` and `eastus2` with "location is restricted" — a known fraud-prevention measure on trial subscriptions. Resolved by trying alternate regions (`centralus` worked).
- **Zsh history expansion on passwords containing `!`**: several `az` commands failed or hung until passwords were consistently wrapped in single quotes.
- **Basic-auth / OneDeploy 400 errors**: generic zip-deploy failures with no clear cause; eventually traced to the Conda `requirements.txt` issue above rather than an auth or Kudu problem — a good reminder to check the actual Oryx build log line-by-line rather than trusting the summary.

## Running locally

```bash
# 1. Clone and enter the repo
git clone <this-repo-url>
cd ai-eval-platform

# 2. Start Postgres in Docker
docker compose up -d

# 3. Set up Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Fill in GEMINI_API_KEY at minimum.
# Set DB_BACKEND=local and SANDBOX_BACKEND=local to avoid needing Azure credentials.

# 5. Run the backend
uvicorn app.main:app --reload

# 6. Run the frontend (separate terminal)
cd frontend
python3 -m http.server 5500
# Visit http://localhost:5500
```

API docs are available at `http://localhost:8000/docs` once the backend is running.
