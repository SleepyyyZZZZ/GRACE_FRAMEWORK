# GRACE Framework

**G**uided **R**easoning & **A**utonomous **C**ode **E**ngineering — a semantic-markup,
multi-agent software-engineering framework. GRACE turns a plain repository into an
environment where autonomous LLM agents (Claude Code, Codex, Gemini, and any generic
agent) read, navigate and generate code through a strict **semantic exoskeleton**
instead of relying on chat history or human-readable comments alone.

> Session language of the protocol is **Russian**; all in-code semantic markup is in English.

---

## What you get

| Area | Contents |
| --- | --- |
| **Agent protocols** | [CLAUDE.md](CLAUDE.md), [AGENTS.md](AGENTS.md), [GEMINI.md](GEMINI.md) — the inviolable interaction protocol, semantic template, LDD 2.0 logging and AppGraph rules, one per agent runtime. |
| **Skills** | `.claude/skills/`, `.agent/skills/`, `.codex/skills/` — phase skills (`mode-architect`, `mode-code`, `mode-debug`, `mode-qa`), protocol skills (`graph-protocol`, `devplan-protocol`, `document-protocol`, `data-transform`), stack skills (`fastapi`, `python-patterns`, `python-testing`, `postgresql-table-design`, `react-*`, `ui-ux-pro-max`, `security-review`, `context7-auto-research`). |
| **Hooks** | `.claude/settings.json` + `.claude/scripts/hooks/` — session state persistence, pre-compact snapshots, debug-statement guards and an automatic semantic-markup gate on `Stop`. |
| **Semantic gate** | [tools/check_semantics.py](tools/check_semantics.py) — read-only validator for the semantic template across Python / TS / JS / Vue and `AppGraph.xml`. Zero ERRORs is a hard gate. |
| **Knowledge graph** | [docs/AppGraph.xml](docs/AppGraph.xml) — global `<KnowledgeGraph>` that bridges every local module graph. |
| **Planning** | `plans/active/` and `plans/archive/` — one dev plan per iteration (`$START_DEV_PLAN`). |
| **Runtime** | [Dockerfile](Dockerfile), [docker-compose.yml](docker-compose.yml), [requirements.txt](requirements.txt), [test_lib.py](test_lib.py), `tests/` — reproducible Python 3.11 environment. |

## Core ideas (TL;DR)

1. **Semantic exoskeleton.** Every file carries a `MODULE_CONTRACT`, `MODULE_MAP`, `RATIONALE`,
   `CHANGE_SUMMARY` and `USE_CASES`; every function a `CONTRACT`; every logical block paired
   `# START_BLOCK_… / # END_BLOCK_…` tags. This is built-in, zero-context documentation for the
   next agent — not comments for humans.
2. **Phase activation protocol.** Work runs through Architect → Code → Debug → QA phases, and an
   agent **must** load the matching `mode-*` skill before acting in a phase.
3. **Log-Driven Development 2.0.** Strict log line format
   `[CLASSIFIER][IMP:n][FUNCTION][BLOCK][OP] message [STATUS]` so a log instantly maps back to a code block.
4. **Two-level AppGraph.** Every module directory keeps a local `AppGraph.xml`; the global
   `docs/AppGraph.xml` references each one. An orphaned local graph is a violation.
5. **Semantic Verification Gate.** After any code change run `python3 tools/check_semantics.py`;
   zero ERRORs is mandatory before a task is considered done.

---

## Quick start (use the framework in this repo)

```bash
pip install -r requirements.txt        # pytest + project deps
python tools/check_semantics.py        # run the semantic gate
python -m pytest tests/ -s -v          # run the suite
# or, fully containerised:
docker compose up --build
```

Point your agent at the protocol file for its runtime: **Claude Code** reads `CLAUDE.md`
(+ `.claude/`), **Codex** reads `AGENTS.md` (+ `.codex/`), **Gemini** reads `GEMINI.md`.

---

## Bootstrap GRACE into ANY repository

This repository **is** the clean framework. To drop it into another project, run one of the
bootstrap scripts below from inside the target repo. They fetch the framework and copy the
framework files in **without** touching your project's `.git`, and without overwriting your
own `README.md` by default.

### PowerShell (Windows)

```powershell
# from the root of your target repository
iwr -useb https://raw.githubusercontent.com/SleepyyyZZZZ/GRACE_FRAMEWORK/main/bootstrap.ps1 | iex
```

or, if you have the file locally:

```powershell
./bootstrap.ps1 -Target .
```

### Bash (macOS / Linux / Git Bash)

```bash
# from the root of your target repository
curl -fsSL https://raw.githubusercontent.com/SleepyyyZZZZ/GRACE_FRAMEWORK/main/bootstrap.sh | bash
```

or, if you have the file locally:

```bash
./bootstrap.sh .
```

### Manual (any OS)

```bash
git clone --depth 1 https://github.com/SleepyyyZZZZ/GRACE_FRAMEWORK.git grace-tmp
# copy everything except the framework's own git/readme/bootstrap meta files
rsync -a --exclude '.git' --exclude 'README.md' --exclude 'bootstrap.*' grace-tmp/ ./
rm -rf grace-tmp
```

After bootstrapping, open `CLAUDE.md` (or `AGENTS.md` / `GEMINI.md`) and start working — the
agent will pick up the protocol, skills and hooks automatically.

---

## Repository layout

```
.
├── CLAUDE.md / AGENTS.md / GEMINI.md   # per-runtime interaction protocol + semantic template
├── .claude/                            # Claude Code: skills, hooks, settings.json
├── .agent/                             # generic agent: skills
├── .codex/                             # Codex: config.toml + skills
├── tools/check_semantics.py            # semantic markup validator (the gate)
├── docs/AppGraph.xml                   # global knowledge graph
├── plans/{active,archive}/             # dev plans, one per iteration
├── src/                                # your application code lives here
├── tests/                              # pytest suite + test_guide.md
├── business_requirements.md            # requirements template
├── Dockerfile / docker-compose.yml     # reproducible runtime
└── requirements.txt / test_lib.py      # deps + environment probe
```

## License

Provided as-is for use as an agent-engineering framework. See upstream for terms.
