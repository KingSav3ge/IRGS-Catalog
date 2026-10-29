# Catalog grounding and world-authoring handoff

29 October 2026. Current edition **3.4.5 Pre-Alpha**; no Alpha gate is closed.
This is a partial A4-CAT-03/04 and WB-CAT-01/02 increment.

The [grounding rubric](IRGS_Catalog/evaluation/grounding_quality_v1/README.md)
separates actor inputs from evaluator truth, structural source/intent checks
from explicit reviewer judgments, and proposal from actual committed effects.
It rejects changed intentions, unreceived actions/sources and structured receipt
contradictions; it does not infer free-text semantics, verify reviewer claims or
qualify live model quality. Independent HTTP consumers create fictional quay and
R00 worlds normally, evaluate received testimony against actual structured
receipts, rerun the two-session journeys with consequences and recovery, and
apply the rubric to in-process fake proposals before actual reviewed acceptance.
The fake transport and no-provider local rendering are separate evidence.

The [authoring reference examples](IRGS_Catalog/evaluation/authoring_examples_v1/README.md)
provide two original fictional families, separate actor/evaluator material,
source and asset provenance, topology, distinct actors, a proposed finite item
and selected knowledge. Engine has not published its world-draft/package DTO;
these are requirements data, not executable packs, Engine validation or a tested
world builder. No vendor assets, user saves or private campaign data are used.

| Selection | Exact commit |
| --- | --- |
| Engine / App's Engine pin | `296e46a1beed10d0ebf2841f133bb52fade83697` |
| App | `7e1a5929b2f30479aa315789f75bfa6c46761438` |
| App's Catalog pin | `e97d87f0d17a16dbe0ce186badafe663188321a1` |

The actual App Engine pin matches the selected Engine; the new Catalog candidate
is an explicit test override and is not adopted by App. App's committed pinned
set separately passes integrity. The previous handoff is preserved at
[COORDINATOR_REPORT_ALPHA_ORDINARY_01.md](COORDINATOR_REPORT_ALPHA_ORDINARY_01.md).

**168 Python tests passed with zero skips; 153 frontend checks passed.** These
include 115 Catalog tests, four selected ordinary HTTP tests, two multi-session
journeys, two fake-transport consumers, 32 Engine tests and 13 App tests. Catalog
integrity verifies 224 files, all 44 previews and the complete original archive;
Engine, App and App's pinned dependencies pass integrity. A separate final
standalone verification reran after the source manifest refresh. Exact commands,
hashes, synthetic observations and limits are in
[GROUNDING_QUALITY_VALIDATION.json](GROUNDING_QUALITY_VALIDATION.json).

Further ordinary consequences, autonomous NPC/institution decisions,
needs/recovery, consequential conflict and older-branch receipt fencing remain
open. Live provider quality requires a protected eligible route and an authorized
finite budget. World-authoring import/export, Engine validation/initialization,
App editor and reviewed playtests remain owner dependencies. No live AI, new
browser, Windows, clean-package, joined release or Alpha qualification is claimed.
The [working brand architecture](BRAND_ARCHITECTURE.md) records the user's
leading studio, platform and engine names subject to clearance and leaves the
Catalog/Atlas name open.
