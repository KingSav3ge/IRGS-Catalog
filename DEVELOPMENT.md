# IRGS Catalog development guide

## Active target: functional Alpha 4.0

The entire **3.x.x series is Pre-Alpha**. Current published edition is **3.4.3**;
the next functional milestone is **4.0.0 Alpha**, subject to the shared acceptance
gates. Previous release remains **3.3.3**. No version metadata is changed by
this instruction update.

Read in order: [continuation](CHAT_CONTINUATION.md),
[shared Alpha plan](ALPHA_4_0_PLAN.md), [owner work order](COORDINATOR_WORK_ORDER.md),
[acceptance register](ALPHA_4_0_ACCEPTANCE.json) and
[version policy](VERSION_POLICY.md). These are the active instructions.
Earlier pending-adoption and next-3.4.3 notes have been superseded by the
published 3.4.3 integration.

## Current assignment and ownership

**A4-CAT-01 separate current communication/start consumers and A4-CAT-02 Alpha context/source/rule assessment, then A4-CAT-03 multi-session journeys.**

Own IRGS_Catalog/: listings, previews, design/source documents, independent actor/evaluator fixtures and acceptance. Publish only KingSav3ge/IRGS-Catalog/main. The coordinator reviews a
viable compatible Engine/App/Catalog set and owns unified integration/publication.
Do not add another simulator or edit a dependency's product sources from here.

Complete shared IRGS gameplay across distinct contexts. Rise R00 is one
regression; two ordinary Alpha contexts with non-Rise evidence are required.
Do not widen preview counts or add cosmetic sections instead of completing
consequential supported decisions and continuing play.

## Development loop

1. Preserve local work and fetch/fast-forward this repository safely.
2. Pick the next work-order task; read the actual contract and implementation,
   not just older summaries. Record concrete current gaps.
3. Implement a bounded useful increment and publish an early versioned interface
   handoff where another owner depends on it.
4. Exercise actual effects, failed paths, actor filtering and continuation in
   synthetic temporary state. Review cannot mutate; acceptance is explicit.
5. Refresh only the owning component hashes after intentional product-source
   edits, verify and run meaningful checks. Root guide edits need no source hash
   refresh and no invented runtime test claim.
6. Update task/evidence status, push only this component and report full SHA,
   exact tested dependencies/pins, actual results, limits and remaining work.

## Checks

Use Python 3.12+ without -O. The work order defines task-specific behavioral
checks and final handoff evidence. Starting commands:

~~~bash
python -B IRGS_Catalog/verify_catalog.py
python -B -m unittest tools.tests.test_player_start_contract tools.tests.test_start_context_contract tools.tests.test_phase_response_contract -v
~~~

Run relevant source/archive/depot contracts and separately versioned exact
Engine/App consumers, using each fixture's declared selectors. Preserve old
identity guards. Refresh only Catalog hashes after intentional content edits.

Do not use a user's save, credentials or personal configuration as a fixture.
Keep generated test logs/packages outside source. Missing provider credentials
do not block offline work. Live evaluation requires separately configured
authorization and a finite budget; synthetic transport is not live quality proof.

## Status and historical evidence

[The acceptance register](ALPHA_4_0_ACCEPTANCE.json) is a requirement/status plan,
not executed evidence; all Alpha gates start unqualified. Attribute every
qualification to an exact source set and reviewer. Partial coverage does not
close general DEV/C2 or imply every concept is playable.

The previous guide is preserved byte for byte in
[the dated development history](DEVELOPMENT_HISTORY_THROUGH_3_4_3.md).
Its old source identities, skips and pending-at-the-time statements describe
their original scope. The shared Alpha plan records the reviewed 3.4.3 baseline.
Preserve original archives/citations and accurately dated evidence.
