# Project instructions

@advisor-agents.md

Before doing any work, read and follow [advisor-agents.md](advisor-agents.md).

<!--
This file is the project's own, not the advisor's. It was created because the
project had no agent instruction file when the advisor was installed, and it
holds nothing but the references that make the advisor reachable: Claude Code
expands the import, Codex follows the sentence. Everything else in it is yours
to write, and no later delivery will touch what you add.
-->

## Agent skills

### Issue tracker

Issues are tracked in GitHub Issues on SebastianoTomasi/VideoEditing via the `gh` CLI. See `docs/agents/issue-tracker.md`.

### Triage labels

Default vocabulary: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: one root `GLOSSARY.md` plus `docs/adr/`. See `docs/agents/domain.md`.
