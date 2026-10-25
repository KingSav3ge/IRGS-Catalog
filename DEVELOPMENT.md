# Catalog development

## Current priority — shared IRGS systems

The user's current direction is development across campaigns and themes.
Read [the shared scope](IRGS_SYSTEMS_SCOPE.md) and
[the current work order](COORDINATOR_WORK_ORDER.md) before selecting work.
Rise R00 remains one regression fixture. Shared-system completion requires
supported non-Rise evidence; campaign-specific mechanics retain their own scope.
The records below preserve previously delivered work and historical evidence.

Target iteration: **IRGS 3.4.0 — in development**. See the active Solo runtime work order and completion plan. Previously qualified versions and evidence retain their recorded identities.

Updated 2026-10-25. Owner: IRGS Catalog. Push destination:
`KingSav3ge/IRGS-Catalog/main`. The coordinator in **IRGS Enviroment** owns joined
integration and review of the exact Engine/App/Catalog dependency set.

## Completed

| ID | Increment | Evidence |
| --- | --- | --- |
| CAT-01 | Independent Catalog data and preserved original campaign designs. | `b6c1362`; component instructions and source verifier. |
| CAT-02 | Expanded v0.5 previews for all 44 concepts, preserving prior adoption and runtime boundaries. | `c70dc16`; import reconciliation and pinned original package. |
| CAT-03 | Validate editorial campaign records before App handoff, independently of refreshed source hashes. | `verify_catalog.py`; `tools/tests/test_campaign_records.py`; `CAMPAIGN_RECORD_VALIDATION.json`. |
| HD-01a | Deterministic 16 MiB whole-ZIP packaging and verified reconstruction tools. | `IRGS_Catalog/historical_details_package.py`; synthetic multipart round-trip and rejection tests. |
| HD-01b | Manifest/member-index contract and explicit unavailable state in Catalog verification. | `IRGS_Catalog/historical_details/README.md`; `verify_catalog.py`; missing-source checks. |
| HD-01c | Inspect supplied extracted Drive folder and preserve its unchanged delivery manifest as intake evidence. | `IRGS_Catalog/historical_details/intake/`; no claim of full payload verification. |
| HD-02 | Retrieve the exact original ZIP and preserve every byte in 32 parts. | Original and reassembled size/SHA-256 verified; original database, books and ancillary files retained. |
| HD-03 | Verify the actual full dataset, source bindings and reader collection counts. | All 5,146 files hashed, all 5,145 delivery bindings verified; one self-excluded delivery manifest; ten collections counted. |
| SOLO-CAT-01 | Versioned synthetic R00 evaluation content, actor/oracle separation, explicit rights and schema validation. | Ten cases and five legitimate actions; `IRGS_Catalog/evaluation/solo_r00_v1/`; `solo_evaluation.py`. |
| SOLO-CAT-02 | Actual selected Engine/App consumer qualification using temporary synthetic state. | 18 new schema/consumer tests; finite materials, hidden boundary, denial, unsupported action, stale/replayed requests, restart, concurrent duplicate and failed-save recovery. See `SOLO_FIXTURE_VALIDATION.json`. |
| SOLO-CAT-03 | R00 content integrated into the coordinated 3.4.0 development build. | [Coordinator source/evidence review](https://github.com/KingSav3ge/IRGS/blob/main/provenance/qa/primary_update_3_4_0_review.json); current App pins the delivered Catalog. |
| SOLO-CAT-04 | Reproducible Catalog-owned qualification of the actual proposal HTTP flow. | Six compatibility schema checks and eight consumer tests for each selected App commit; `SOLO_PROPOSAL_VALIDATION.json`. Original fixture and baseline qualification preserved. |
| SCR-CAT-01 | Initial authored routine response library for the user's API token reduction request. | Preserved 1.0.0: 325 variants, 82 families, 12 recipes; `IRGS_Catalog/responses/routine_v1/`. |
| SCR-CAT-02 | Deterministic typed formatting, actor/snapshot/source/state checks and exact receipt anchoring. | `scripted_responses.py`; 13 content/composition tests render every variant. No provider imports or dispatch. |
| SCR-CAT-03 | Qualify text against actual Engine/App receipts, projections and supported editable drafts. | Five synthetic consumer tests assert no provider dispatch or save mutation during rendering. `SCRIPTED_RESPONSES_VALIDATION.json`. |
| SCR-CAT-04 | Campaign-neutral depot with 750 system responses and 250 editable drafts. | Schema 2, depot 1.0.0: 1,000 distinct stored variants, 127 families, 32 recipes; typed campaign facts and unbound semantic intent tags. Original Rise pack preserved separately. `RESPONSE_DEPOT_VALIDATION.json`. |

## Current increment — 25 October 2026

The user's final scope is a response depot for any campaign/theme, containing
750 system responses and 250 editable player drafts. The schema-2 depot 1.0.0
supplies exactly 1,000 distinct stored variants in 127 families and 32 recipes.
Recipes, substitutions and possible combinations do not inflate that count.
Typed placeholders carry the active campaign's known people, places, resources,
tasks and received records. All 250 drafts use semantic intent tags and the
state `draft`; Engine/App adapters map explicit submissions to supported
operations or retain unresolved declarations. Text adds no mechanic, automatic
player decision or NPC agreement. Campaigns expose only applicable families.

`responses/depot_v1/` is the default source. The schema-1, 325-variant Rise pack
in `responses/routine_v1/` remains byte-identical under its original identity.
Renamed generic families/slots belong to the new depot rather than silently
changing historical indices. Four synthetic themes exercise portability;
actual R00 tests provide one real campaign compatibility case.

Committed-result recipes preserve the actual receipt exactly. Assembly rejects
missing/extra fields, incompatible states, conflicting shared facts, mixed actors
or snapshots, and mixtures of player intentions with system responses. Source
filtering/authentication and all world mechanics remain with Engine/App.

The user confirms Engine is building its runtime version and App its
implementation layer. Catalog supplies content/schema/reference fixtures; its
existing reference formatter gains the new identity/schema and default source.
Rendering makes zero API calls. Production adoption, event mapping, scoped caches
and live token measurements belong to Engine/App. Missing facts/rules do not
authorize a paid fallback or fabricated result. Do not send the full depot in
provider prompts. General narration/dialogue remains separate pending work.

Fresh acceptance passed 150 test executions with zero skips, including all
1,000 variants, all 32 recipes, four synthetic themes and actual depot consumer
checks for each selected App. Rendering made zero provider dispatches and left
save bytes unchanged. Integrity passed 163 source files, all 44 previews and
the complete original archive. Exact commands and dependencies are recorded in
`RESPONSE_DEPOT_VALIDATION.json`; the initial
`SCRIPTED_RESPONSES_VALIDATION.json` remains historical evidence.

## Previous increment — proposal compatibility

The original `solo-runtime-01` content, App pinning and joined development
qualification are complete. The coordinator integrated Catalog
`401df26a1f16be864dd15d7c5250da5d75f8ccca`, Engine
`8234044c089131314019ecaf6799a2f08028a3f8` and App
`277554aac21a092b8a55562309da274bbe74a3af`. Its independent browser and clean-package
checks exercised five Rise actions through shelter completion at elapsed 3,900.
These are attributed coordinator results, not fresh tests run by Catalog.

This follow-up updates that status and adds a separate compatibility contract and
actual proposal/acceptance HTTP tests. It qualifies the integrated Engine with
both the integrated App above and component follow-up App
`4f45f5ab8473a2bddb500fe3a49122575b6483e1`. Both Apps commit the selected Engine
and original Catalog `401df26`. Tests select this Catalog candidate explicitly;
the new follow-up and subsequent App are not thereby approved for joined release.

All ten original cases now run through the actual Engine broker/validator/ledger
and App host with offline synthetic transport. Five accepted actions retain
finite resources, committed summaries and exact intent across restart and
concurrent retries. Other cases reject at their actual boundary. Extra checks
cover foreign actors, forged context, provider output failures, acceptance,
identical restore, cancellation, late output, failed saves and unconfigured use.
No provider call, user save, alternate simulator or new playable content is added.

Fresh qualification passed 114 test executions with zero skips: 73
source/schema/archive-reader checks, six original consumer checks, eight proposal
HTTP checks for each of the two Apps, 13 existing App proposal bridge tests and
six App catalogue tests. Integrity passed 158 Catalog source files and the full
original archive. Each exact dependency selection runs in a separate process.

The original fixture, manifest and loader remain byte-identical. Its initial
contract still selects Engine `723627e629231b5e90f38b9d52b65c9a3967b92a` and App
`d8dc35ed653e516ccd0cacf91ee9693258491032`; those six consumer checks run separately
from the new dependency selections. `SOLO_FIXTURE_VALIDATION.json` remains
historical evidence rather than being relabelled as current proposal testing.

## Previous-cycle execution record

`historical-details-01` was the preceding increment. Full source preservation
and byte-level acceptance are complete. The manifest matches committed Engine
`b3e7d760a2cf3712292b09328566cf1ed0d78c97`. Consumer checks use that reader and
the App reference service from `e8ef2b0e683a46fab4fe586e86afd26196ab2869`
as explicit isolated source snapshots. See the validation record for executed
results; these checks do not change or approve App dependency pointers.

Executed acceptance: 39 source/consumer tests passed (30 synthetic, five actual
complete-delivery checks, four actual Engine/App service checks), plus six
existing App catalogue tests. Full Catalog integrity verification passed for 140
source files and all 44 existing campaign concepts. No checks in these runs were
skipped. The complete multipart set subsequently passed coordinator review, App pinning
and joined qualification; these older test identities remain historical evidence.

The campaign portfolio still marks Century, Kira and Rise **In Development** and
41 other concepts **Planned**. These labels describe concept development; the
Catalog does not implement their Engine mechanics or App viewer.

The Catalog follow-up, `CAT-03`, closes a reproduced authoring gap:
refreshed source hashes alone previously allowed duplicate catalogue IDs,
unknown development statuses and release/entitlement claims to pass verification.
Source verification now checks identity/type/slate consistency, explicit preview
and readiness flags, discovery IDs and held starting references. It preserves
Planned, Concept Draft and In Development as separate states; App remains the
owner of draft filtering and runtime projection. Current campaign descriptions,
source archives, Historical Details bytes and its manifest pin are unchanged.
See `CAMPAIGN_RECORD_VALIDATION.json` for this follow-up's executed checks.

Fresh follow-up checks passed: 55 source/consumer tests (including the 16 new
record-validation tests), six App catalogue tests and complete Catalog integrity
verification. All tests executed with zero skips.

## Blocked

- **HD-04 resolved:** coordinator review, exact App dependency selection and
  joined qualification are complete for historical-details-01.
- The original source-access blocker is resolved. There is no missing source
  input for the Catalog deliverable.
- No Catalog source blocker remains for the completed R00/proposal follow-up.
- No Catalog source blocker remains for the scripted response library. Consumer
  adoption of this new Catalog commit is pending; the current App does not yet
  select this formatter for routine presentation, so live token savings are unmeasured.
- **NARRATION-CAT-01 awaiting Engine/App contract:** the current API only proposes
  existing actions; App returns Core summaries with `narrative: null`. The
  coordinator lists general narration/dialogue and semantic/voice review as
  unfinished. New synthetic narration/dialogue inputs need a supported request,
  result, actor/source and validation contract before actual qualification.

## Remaining

1. Engine/App adopt the campaign-neutral depot with campaign-specific intent/event
   adapters for eligible routine presentation and
   editable drafts, preserving source/actor scope and explicit decisions. Select
   this Catalog commit through their reviewed dependency pins and qualify the
   actual call-avoidance/cache/fallback behavior. Coordinator owns joined review.
2. When Engine/App publish general narration/dialogue contracts, add separately
   versioned actor-safe evaluation inputs/oracles and actual consumer checks;
   retain explicit synthetic rights and report human semantic review separately.
3. Preserve original rights, sources, uncertainty and archive bytes in future
   indexing; the ten reader collections remain a view of the full archive.
4. Resume optional catalogue/artwork expansion after the runtime delivery.
   Campaign release remains independent of previews and archive preservation.

## Verification record

See `RESPONSE_DEPOT_VALIDATION.json` for the current depot's commands,
selected sources and scope. `SCRIPTED_RESPONSES_VALIDATION.json` and
`COORDINATOR_REPORT_ROUTINE_1_0.md` retain initial response-library evidence.
`SOLO_PROPOSAL_VALIDATION.json` and
`COORDINATOR_REPORT_PROPOSAL_FOLLOWUP.md` retain the proposal follow-up evidence.
`SOLO_FIXTURE_VALIDATION.json`, `HISTORICAL_DETAILS_VALIDATION.json`,
`CAMPAIGN_RECORD_VALIDATION.json` and `COORDINATOR_REPORT_HISTORICAL_DETAILS_01.md`
retain labelled previous-cycle evidence; `COORDINATOR_REPORT_SOLO_RUNTIME_01.md`
preserves the initial R00 delivery report. All behavioral fixtures are synthetic
and temporary; no user campaign saves are read or migrated.

## AI evaluation content and rights backlog

The coordinator added this sequenced backlog in work-order commit
`02db97383a8a0c785250b98585253d24f3365a9b`. The
[master addendum](https://github.com/KingSav3ge/IRGS/blob/main/AI_PROVIDER_STRATEGY.md),
[research review](https://github.com/KingSav3ge/IRGS/blob/main/AI_PROVIDER_REVIEW.md)
and [16 proposed evaluation cases](https://github.com/KingSav3ge/IRGS/blob/main/provenance/qa/ai_provider_strategy/EVALUATION_CASES.json)
were read; model evaluations remain unrun.

Future Catalog evaluation inputs must preserve source identity, version, rights,
uncertainty and permitted processing classification. Public access is not
permission for external processing. Exclude private saves; label synthetic
characters/situations as evaluation fixtures rather than campaign canon or
playable content. Keep evaluator-only hidden facts out of actor/model inputs.
Review any derivative or creator processing rights independently before use.

Engine owns provider access, routing and validation; App owns administration and
presentation. Catalog records do not select models, store credentials/prices or
authorize transfer. This increment sends no archive content to providers and
does not adopt generated prose. The current R00 fixture supplies validated
synthetic inputs and actual baseline consumer compatibility for the active work
order, with current proposal HTTP compatibility now qualified separately. It
does not run the earlier 16 proposed model-quality evaluations or complete
general narration/dialogue. Live smoke still requires configured authorized
access, an eligible workload and finite limits through Engine/App; none is
dispatched by this content increment. Each new component/joined set needs its
own review, separate from the already integrated original 3.4.0 baseline.
