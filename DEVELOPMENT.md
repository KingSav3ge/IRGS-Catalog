# IRGS Catalog development guide

Current guide: 25 October 2026. Owner: `KingSav3ge/IRGS-Catalog/main`.
Start with [CHAT_CONTINUATION.md](CHAT_CONTINUATION.md).

## Qualified baseline and scope

IRGS **3.4.0 development**, Core compatibility **3.3**. Develop shared systems
across campaigns and themes. Rise R00 and the existing non-Rise authored opening
are actual supported regression contexts. Synthetic theme/profile checks prove
their recorded formatting/declaration behavior, not new campaign mechanics.

The [coordinator integration](https://github.com/KingSav3ge/IRGS/blob/65351ebcfe2538d880f576a3ce4aa2230537e08d/provenance/qa/shared_response_integration_3_4_0_review.json) qualified joined `65351ebcfe2538d880f576a3ce4aa2230537e08d`:

| Component source | Qualified commit |
| --- | --- |
| Engine | `2f9476c6090878257d17cab3ad3a83a7ce18a5dc` |
| App/Web | `aae8a25656c890181e0aa569df2c716968ec3642` |
| Catalog | `27fff8385d1c01fdfe9ad7254b7647e6bc12a01e` |

Recorded integration results: 680 Core tests run (679 passed, one private-fixture
policy skip); 201 Web run (194 passed, seven Windows skips); 105 interface checks;
104 Catalog checks; eight independent HTTP checks. Two-context Chromium and
clean-package qualification passed with zero live inference. These are attributed
prior results, not tests newly executed by this guide update.

Later guide-only commits do not alter this qualified source set. Preserve
independent content/schema versions and historical evidence. See
[shared scope](IRGS_SYSTEMS_SCOPE.md), [continuation](CHAT_CONTINUATION.md) and
[the work order](COORDINATOR_WORK_ORDER.md).

## Ownership and completed content

Own `IRGS_Catalog/` campaign listings/previews/design, response content/schema,
provenance and synthetic evaluation material. App owns the viewer; Engine owns
rules/initializers and its independently bundled runtime. Keep Catalog formatter
code a reference implementation, with authentication and execution in its hosts.

- Depot `irgs-response-depot-v1@1.0.0`, schema 2: 750 system variants, 250 editable
  drafts, 127 families and 32 separately counted recipes. Preserve original packs.
- Shared nine-case non-Rise/Rise fixture and actor/oracle separation; current App
  now consumes selected depot drafts and exact receipt composition in production
  code. Engine independently bundles the exact same neutral depot bytes.
- All 44 previews, supplied packages, adopted canon references and complete
  Historical Details delivery remain preserved. The archive has 32 parts,
  5,146 files and 5,145 bindings; no acquisition or split-work remains.

Read [depot](IRGS_Catalog/responses/depot_v1/README.md),
[shared fixture](IRGS_Catalog/evaluation/shared_responses_v1/README.md) and
[campaign records](IRGS_Catalog/design/campaign_catalogue/README.md).
Earlier records describing consumer adoption as pending retain their original date.

## Next bounded increment

Add a separately versioned compatibility follow-up for the currently integrated
Engine/App pair, with actual local_responses and saved presentation checks in
independently initialized non-Rise and Rise contexts. Preserve existing fixture
manifests, payload hashes and declared consumer commits exactly; do not repin old
evidence. Select clean exact current consumers and verify App's committed pins.
Test real outcomes, drafts that submit nothing, actor/oracle separation, zero
provider calls, stable older receipts, retries and failed/missing-source fallback.
The current-pair follow-up can proceed now. Extend phase/communication evaluation
only after owner-published contracts supply supported behavior and known facts.
Keep the depot at 750 system variants, 250 editable drafts and 32 recipes unless
the user changes that request. New text alone completes no simulation system.

## Check Catalog and exact consumers

```bash
python -B IRGS_Catalog/verify_catalog.py
python -B -m unittest tools.tests.test_scripted_responses tools.tests.test_scripted_response_expansion tools.tests.test_shared_response_contract -v
```

The 104-check source/archive/contract selection used in current qualification is:
`tools.tests.test_campaign_records`, `test_historical_details`,
`test_historical_details_delivery`, `test_solo_evaluation`,
`test_solo_proposal_contract`, `test_scripted_responses`,
`test_scripted_response_expansion`, `test_shared_response_contract` (each under
`tools.tests`). Optional real reader cases require explicit source selectors:

| Selector | Meaning |
| --- | --- |
| `IRGS_ENGINE_ROOT` | Selected Engine `IRGS_3_3` directory. |
| `IRGS_CATALOG_ROOT` | This Catalog `IRGS_Catalog` directory; source-relative manifest tests must select this same root. |
| `IRGS_HISTORICAL_ENGINE_RUNTIME` | Selected Engine `IRGS_3_3/runtime`. |
| `IRGS_HISTORICAL_APP_SOURCE` | Selected App `IRGS_Web`. |

Existing `test_shared_response_consumers` requires clean exact original snapshots
Engine `9ecf3b8864f5f93be6b15c8cf6087e6bd66c8443`, App
`e1efcfe7a7eb47eb80208fce21d0b18a2b231a1f`, and its recorded Catalog pin
`94b8ca6d976da48b3c6ca65e014b28c6d9a120c2`. Select repository roots through
`IRGS_SHARED_ENGINE_SOURCE` / `IRGS_SHARED_APP_SOURCE`. Run in a fresh process.
Its eight checks passed against those declared snapshots; current consumers were
qualified separately. Other legacy suites keep their own manifest selections.
Never weaken identity guards or replace old fixture IDs to make new heads pass.

After intentional Catalog source/content edits, refresh only
`python -B tools/refresh_component_releases.py --component catalog`, then verify
again and execute actual compatible consumer checks. Optional skips are not
executed compatibility evidence. Root guide edits need no Catalog release refresh.

## Rules for every increment

Keep one authoritative Core and the nine K-owners; provider work retains the six
existing Director categories. Distinguish intent, authorization, committed effects,
received information and presentation. Only actual actor-legitimate records may
support a response. Testimony and uncertain information retain their status.
Keep storage revision, causal order, elapsed spans, civil dates and information
times distinct. Select real rules/adapters; themes and text create no capability.

Routine responses require no provider, key or model tokens. Preserve exact
receipts, negation, actual zero/absent durations, editable intentions and explicit
submission. Missing text or rules retain a literal/unresolved result and cannot
authorize paid fallback. Keep pinned code/content intake on the exact verified
bytes; retain the component-update regression in App.

Use temporary synthetic saves. Never read/migrate user campaigns or run the
external private-save fixture. Preserve original archives, source records,
rights, adopted canon and 44 previews. Historical Details is fully delivered;
archive reacquisition is complete. Preview/content presence grants no release
or mechanical authority. General freeform/combat, generated dialogue, sustained
institutions, full C2, live model quality and wider hosting retain their open
requirements; Co-op remains deferred.

## Deliver the increment

Keep completed, active and remaining work current. After an actual source edit,
refresh only the owning component release, run relevant behavioral checks and
verify source integrity. Hash refresh and planning alone qualify no feature.
Use Python 3.12+ without `-O`; interface/browser tooling uses Node 20+.

Push only this repository's `main`. Return the full pushed SHA, actual changed
behavior, APIs/adapters, exact dependencies, commands/results/skips and remaining
limits to IRGS Enviroment. Coordinator imports product source only after all
three viable updates, compatible App pins and fresh joined qualification.
Root guide/work-order edits alone need no component release refresh or invented
runtime delivery. Preserve local work before pulling; avoid resets and force pushes.

Previous milestone/status records: [dated history](DEVELOPMENT_HISTORY_2026-10-25.md).
