# Catalog delivery — solo-runtime-01

Owner: **IRGS Catalog**. Destination: `KingSav3ge/IRGS-Catalog/main`. Pulled base:
`f22049396795425838add515960a3e95a5e98189`. Resolve this candidate's exact SHA with
`git rev-parse HEAD`; the full pushed SHA is reported in the component chat.
Coordinator update `0a6a754494b2b5c12f47bbd392d215ce81ebf663` was also pulled
before committing: target iteration **IRGS 3.4.0 — in development**. Fixture and
schema identities remain independent. Previous-cycle evidence is retained in `COORDINATOR_REPORT_HISTORICAL_DETAILS_01.md`.

## Delivered test content and behavior

`IRGS_Catalog/evaluation/solo_r00_v1/` supplies fixture
`irgs-solo-r00-eval-v1`, version 1.0.0, schema 1. Its ten cases include five actual
legitimate actions: walk to the clearing, establish the camp, reserve shelter
inputs, advance to the first work boundary and complete shelter. The other cases
cover denied building at the commons, a deliberately unsupported grain-creation
proposal, stale revision, exact replay and changed-payload request identity reuse.
No new mechanic or alternate simulator is added. Engine creates all state from
its reviewed R00 choices and executes its actual `execute_settlement_action`
handler. App supplies durable commits, revision checks and result recovery.

Actor documents and evaluator setup/oracle are physically separate. The
hash/schema-checked `export_actor_input` API reads only the manifest and selected
actor file, rejects evaluator paths and extra fields, and never opens evaluator
files. Full intake validation and strict actor export both reject reserved hidden
markers even after hashes are refreshed. Every canned actor context is checked
against the actual App actor-filtered view at its point in the sequence.

The manifest records stable fixture/case/source/intent identities, explicit
synthetic authorship and processing rights limited to authored fixture text.
Unknown imported rights gain no permission. Engine authorization remains required
for actual transfer; content selects no provider/model/key/price/route. Setup,
full templates, raw saves and Historical Details do not enter actor exports.

At every accepted step, existing stock plus accepted consumption equals opening
stock. NPC repair consumes one NPC timber at elapsed 1,800; founder shelter
consumes three founder timber at 3,900 and creates two shelter places. Axes and
grain remain unchanged. Action requests return at material work boundaries;
causal clock, elapsed time and storage revision are checked separately.

The fixture is outside public campaign discovery, canon, playable starts and
release approval. All 44 previews, supplied packages and original archive bytes
remain unchanged. Catalog source verification now also checks fixture intake.

## Exact selected consumers and executed evidence

- Engine `723627e629231b5e90f38b9d52b65c9a3967b92a`.
- App `d8dc35ed653e516ccd0cacf91ee9693258491032`.
- That App's committed Engine pin matches the selected Engine. Its Catalog pin
  remains `3e898acb2179f18a41d7967817bedf429df29d3f`; tests explicitly select this
  Catalog candidate through `IRGS_CATALOG_ROOT`. No pointer is changed here.

Both dependency snapshots are isolated and unedited. Consumer tests check full
Git identities and imported module paths. All saves are temporary synthetic
state. Fresh results, with **zero skips**:

- **73 Catalog/source/consumer tests passed**, including twelve new schema and
  six new actual Engine/App consumer checks, all existing record tests and full
  Historical Details source/reader checks.
- **11 existing App Rise HTTP tests passed**, including request recovery,
  persistence, finite work, authorization and filtered views.
- **Six existing App catalogue tests passed**, preserving all 44 previews,
  discovery boundaries and temporary-world continuity.
- Catalog integrity passed **155 source files**, ten fixture cases, 32 historical
  parts, all 5,146 archive files and all 5,145 delivery bindings. Only Catalog
  release hashes were refreshed. `git diff --check` passed.

New consumer checks also prove restart-safe result lookup, an exact duplicate
under concurrency applying once, and failed persistence leaving save bytes
unchanged before a single successful retry. Schema checks exercise incorrect
rights, hidden-field/marker contamination, wrong audience, path traversal,
symlinks, tampering, duplicate JSON fields/case IDs and broken source/replay refs.
See `SOLO_FIXTURE_VALIDATION.json` for commands, dependencies and the resolved
initial combined-test environment omission.

## Pending integration and live prerequisites

Catalog's assigned fixture content and baseline qualification are complete for
review. This does not finish the Solo AI runtime. App-owned production fixture
loading and its exact Catalog pin update, the next Engine/App proposal/provider
contracts, requalification against those contracts, and isolated joined acceptance
remain pending. The coordinator selects and reviews that exact component set;
no earlier-cycle approval applies to this candidate.

No live provider call was made. Any live smoke test needs configured approved
access, route and credentials under Engine policy. The fixture does not supply
those settings or authorize private/history payload transfer. No other repository
was edited or pushed. There is no missing archive input or Catalog source blocker.
