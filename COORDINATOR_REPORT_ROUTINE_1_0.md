# Catalog delivery — reusable routine responses

Archived initial 1.0.0 delivery report from
`0063faea59c3294de15580fe5917cc03c89f0ad8`. The original 325-variant source and
`SCRIPTED_RESPONSES_VALIDATION.json` remain unchanged. Current campaign-neutral depot
and the user's final 750/250 split are recorded in `COORDINATOR_REPORT.md`.

Owner: **IRGS Catalog**. Push only `KingSav3ge/IRGS-Catalog/main`. Pulled base:
`f391dfd535c4562e8d2a230bf36f4d2ded508837`. Resolve this report's containing Git
commit with `git rev-parse HEAD`; the exact pushed SHA is reported in chat.

The user's new priority is to reduce Player and System API token usage by
reusing a large collection of scripted responses, reserving AI for demanding
responses. This directive authorizes the Catalog content/formatting increment.
The prior proposal follow-up is preserved in
`COORDINATOR_REPORT_PROPOSAL_FOLLOWUP.md` and `SOLO_PROPOSAL_VALIDATION.json`.

## Delivered

`IRGS_Catalog/responses/routine_v1/library.json` contains **325 authored variants
across 82 families, with 12 composition recipes**: 273 system-message variants
and 52 editable player drafts (four per supported Rise action). It covers routine
request/recovery/status messages, received records/testimony/uncertainty,
inventory/units/reservations, elapsed time, project progress and camp facts.
Original authorship, local-presentation/evaluation use and no imported material
are recorded explicitly. Content metadata grants no external-processing route.

`IRGS_Catalog/scripted_responses.py` validates and deterministically formats these
records without importing Engine, App or a provider. It combines declared whole
clauses rather than arbitrary word slices. Required typed slots, bounded strings
and numbers, source/state/role matching and actor/snapshot consistency prevent
accidental mixing of incompatible responses. Source text remains plain text;
App must escape it. Committed-result compositions always preserve the exact
actual receipt, including negation and line breaks. Player drafts submit nothing
and cannot mix into system claims or combined player decisions.

Catalog verification includes the library/schema and all source pins. The
[handoff](IRGS_Catalog/responses/routine_v1/README.md) specifies trusted host input,
API examples, routine-first selection, snapshot-scoped caching and exact limits.
Unknown coverage returns to the host without guessing or automatically dispatching
AI. The library is local content; it should not be included wholesale in prompts.

## Fresh executed evidence

**132 test executions passed, zero skips:**

- 86 source/schema/actual-archive-reader tests, including 13 new response tests
  that render every one of the 325 variants and exercise invalid facts, actors,
  snapshots, quantities, expression injection, source/state/role rules, negation
  preservation and separate player agency.
- 13 current consumer tests: eight existing proposal HTTP checks plus five new
  response checks against actual App results and actor-filtered projections.
  The response checks use five actual R00 Core actions and assert **zero Engine
  provider dispatches and identical save bytes during rendering**. They cover
  actual receipts/elapsed spans, inventory/reservations/units, project/camp views,
  received records, unconfigured status and all 13 editable action drafts.
- Eight proposal consumer tests against the integrated App selection.
- Six original consumer tests against the original exact dependencies.
- 13 existing App proposal bridge tests and six existing App catalogue tests.

Catalog integrity passed **161 source files**, all 44 previews, all 32 historical
parts, all 5,146 archive files and all 5,145 delivery bindings. `git diff --check`
passed. Original fixtures, manifests/loaders, designs, archive bytes and earlier
validation records are unchanged. Only Catalog release hashes were refreshed.
See `SCRIPTED_RESPONSES_VALIDATION.json` for commands and test-source identities.

Current response/proposal tests select Engine
`8234044c089131314019ecaf6799a2f08028a3f8` and subsequent App
`4f45f5ab8473a2bddb500fe3a49122575b6483e1`. Integrated App
`277554aac21a092b8a55562309da274bbe74a3af` is separately checked for proposal
compatibility. Their committed Catalog pin remains
`401df26a1f16be864dd15d7c5250da5d75f8ccca`; qualification selects this Catalog
candidate through environment only. Original tests separately select Engine
`723627e629231b5e90f38b9d52b65c9a3967b92a` and App
`d8dc35ed653e516ccd0cacf91ee9693258491032`. Exact clean source snapshots and module
paths are checked. No user campaign is read or migrated.

## Engine/App adoption requested

The Catalog library and zero-provider reference formatter are ready for review.
**Production token usage is unchanged until Engine/App adopt this local path.**
No live token reduction, billing percentage or runtime integration is claimed.

The receiving components should map eligible public routine events to these
families, bind their actual actor-safe facts and render locally. Use editable
canned player drafts for simple intentions with ordinary explicit submission.
Keep cached message choices scoped to actor, branch, restore, revision/source,
library version and language; do not blend current facts into an older receipt.
Only demanding supported responses should request the Engine's approved AI
capability under its normal policy, authorization and finite limits. Missing
facts or rules stay unresolved; no template can supply world effects or NPC
choices. A missing template alone must not authorize a paid fallback.

App owns its dependency pin, presentation/event mapping and actual UI adoption;
Engine owns provider routing, actor/source authority and execution. Coordinator
owns exact joined qualification. This delivery edits/pushes only Catalog. No
provider call was made, no historical/private payload entered a prompt, and no
provider settings or prices were added to content. The separate general
narration/dialogue contract and human semantic/voice evaluation remain open.
