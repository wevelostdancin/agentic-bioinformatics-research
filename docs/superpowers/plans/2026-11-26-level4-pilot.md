# Plan: Level 4 Pilot — Executable Robustness of Swarm Protocols

Date: 2026-11-26
Status: scaffolding implemented; adapter is a stub, no measurements yet

## 1. Question

Do multi-agent bioinformatics protocols differ in how they turn input
perturbations into *silent* corruption — runs that finish with exit code 0,
report a confirmed finding, and are wrong?

The dependent variable is not answer accuracy but the share of confirmed
findings that fail ground truth. Binary-classification and QA cascade papers
cannot measure it; executable bioinformatics pipelines can.

## 2. Factors

- protocol: single, parallel_vote, parallel_judge, debate, supervisor, blackboard
- perturbation: none, prompt_bloat, corrupted_inputs, decoy_files
- task: one verifiable bioinformatics task per cell
- seed: repetitions per cell

Pilot subset: single / supervisor / debate x none / decoy_files x 5 seeds = 30 runs.

## 3. Components added

- src/agentic_bioinformatics_research/perturbations.py — deterministic injector.
  Copies the task tree, never mutates the source, returns a manifest with every
  change and a SHA-256 over the change list, recorded per run.
- src/agentic_bioinformatics_research/matrix.py — factor grid expansion.
- src/agentic_bioinformatics_research/metrics/cascade.py — cascade_depth,
  decoy_uptake, silent_corruption_rate, robustness_drop.
- TraceEvent.artifact_id and TraceEvent.references — the edges that make a
  cascade measurable from traces.
- experiments/pilot/ — config, fixture task, matrix runner, report.

## 4. What is scripted

The adapter (harness/plain.py) is a stdlib loop that owns coordination only:
who talks to whom, which artifact each claim references, and the token budget.
It supports single and supervisor; worker claims feed the supervisor answer, so
the artifact graph has depth 2 instead of 1.

The agent (harness/agents.py, ScriptedAgent) is a deterministic stand-in, not a
model. It runs a fixed fold-change analysis over whatever files it is handed
and is naive about file selection, so decoys and truncation reach it the way
they would reach an unwary agent. Its answers are protocol-independent, so any
protocol difference in the pilot is noise by construction.

Numbers produced by the pilot validate the instrumentation, not LLM behaviour;
every summary says so.

## 5. Go / no-go

Pilot passes if, on one real task with a real adapter:

1. every cell produces four valid artifacts and passes require_valid_run();
2. the perturbation manifest reproduces byte-identically across machines;
3. cascade_depth is greater than 1 in at least one decoy cell, i.e. the trace
   actually shows propagation rather than a flat list of findings;
4. the effect is visible before statistics: decoy cells differ from clean cells
   by more than seed-to-seed spread.

Status with the scripted agent: (1) and (2) hold; (3) holds — single gives
depth 1 and supervisor gives depth 2 on real traces; (4) is not meaningful with
a protocol-independent stand-in.

Otherwise the design changes before any full sweep.

## 5a. First model-backed run (2026-11-26, superseded by 5b)

Agent: deepseek/deepseek-v4.1-flash-1017 via the polza OpenAI-compatible
endpoint. 18 cells (single/supervisor x none/decoy_files/corrupted_inputs x
3 seeds), 18 runs, one provider failure (empty reply). Total cost: 18.7k
input and 22.4k output tokens.

| condition | single | supervisor |
|---|---|---|
| clean, correct | 3/3 | 3/3 |
| decoy_files, correct | 3/3 | 2/2 valid (1 failed) |
| decoy uptake (agents that read a decoy) | 0 | 1-2 in the valid runs |
| corrupted_inputs, correct | 0/2 (+1 abstention) | 0/3 |
| silent_corruption_rate under corruption | 1.0 | 1.0 |
| cascade_depth | 1 | 2 |

Reading: corruption of the count table reliably produces a confident wrong
answer, which is the dependent variable this pilot was built to exercise. The
decoy was ignored by the single agent but reached workers under supervisor, and
the aggregator still recovered the right answer in the runs that completed —
containment rather than infection. With 2-3 runs per cell this is a signal to
follow, not a result.

Caveats: one model, one synthetic task, 2-3 seeds, one provider failure, and
the supervisor aggregator sees worker claims as text rather than through a
verified interface.

## 5b. Second run: 36 cells, two tasks (2026-11-26)

Grid: 2 tasks (genes: 8 rows; variants: 60 rows, different schema and rule)
x 3 protocols (single, supervisor, debate) x 2 conditions (none, decoy_files)
x 3 seeds = 36 runs, 0 failures.

| task | protocol | decoy uptake | correct answers | silent_corruption_rate |
|---|---|---|---|---|
| genes | single | 0 | 3/3 | 0.0 |
| genes | supervisor | 1, 2, 1 | 3/3 | 0.0 |
| genes | debate | 1, 1, 1 | 3/3 | 0.25 |
| variants | single | 0 | 3/3 | 0.0 |
| variants | supervisor | 2, 1, 0 | 3/3 | 0.0 |
| variants | debate | 1, 1, 0 | 3/3 | 0.25 |

Reading:

1. Containment reproduces. On a second task with a different data shape the
   supervisor kept the correct answer in all three runs while one or two workers
   read a decoy. This is not an artifact of the gene-count task.
2. The shared-chat hypothesis is not supported at this scale. Debate did not
   turn decoy uptake into a wrong pipeline: all nine decoy runs under debate
   returned the correct final answer. The 0.25 is one unsupported extra claim
   from a multi-claim aggregator in a single run, not a corrupted result.
3. Cost separates the protocols more sharply than accuracy: single 1.9k,
   supervisor 6.0k, debate 7.8k tokens per run.

Caveats: three seeds per cell, synthetic tasks, one model, and a reasoning model
whose hidden tokens need a generous max_tokens (at 800 the answer is empty).

## 6. Cost

Measured on the 36-cell grid: single 1.9k, supervisor 6.0k and debate 7.8k
tokens per run on these small tasks. Real bioinformatics tasks will be one to
two orders of magnitude larger, so the earlier 100k-per-run estimate still holds
for the full design (4 tasks x 6 protocols x 4 conditions x 5 seeds = 480 runs,
about 48M tokens). The pilot is the cheap decision point either way.

## 7. Next steps

1. Replace the stub with one real adapter (LangGraph or a plain loop) and one
   verifiable task from the pinned benchmark.
2. Download and hash the benchmark data; fill file_sha256 in data/manifest.yaml.
3. Hold the agent count fixed and vary only the communication topology, so the
   topology effect is not confounded with team size.
4. Add a human-annotated MAST slice for a sample of traces.
