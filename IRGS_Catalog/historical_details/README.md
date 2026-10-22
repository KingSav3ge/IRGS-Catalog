# Historical Details

Catalog owns preservation of the complete **Historical Grand Archive 1.1** ZIP.
Engine owns its reference reader; App owns the Creator interface. This directory
currently contains an unavailable-source manifest and intake evidence. It contains
no archive payload parts and is not a completed import.

The expected original is `IRGS_Historical_Grand_Archive_v1_1.zip`, 533,064,680 bytes,
SHA-256 `51246eb6898a228f42f0794ed19ce69af275a2a4661c0fb6a1d3baebe3efc773`.
That identity comes from the work order's prior local attachment check. It has
not been reverified against the original ZIP in this worker.

## Import and check

Use Python 3.12+ without `-O`. Once the exact original is accessible, create a new
staging package outside the checkout:

```text
python -B IRGS_Catalog/historical_details_package.py import-archive /path/to/IRGS_Historical_Grand_Archive_v1_1.zip /tmp/historical-details-candidate
python -B IRGS_Catalog/historical_details_package.py verify /tmp/historical-details-candidate/manifest.json
```

The importer refuses a source with a different byte count or hash and refuses to
overwrite an existing destination. It splits the entire original ZIP, preserving
the central database, books, source assets, rights records and ancillary files.
All parts except the last contain exactly 16,777,216 bytes. The expected original
requires 32 parts; the last contains 12,970,984 bytes. Parts stay below 100 MiB.
No ZIP member is extracted or executed.

After reviewing the staged package, move its manifest, `parts/` and member index
into this directory while preserving these instructions and intake evidence.
Run the source checks, refresh only Catalog hashes, and verify again:

```text
python -B -m unittest discover -s tools/tests -p 'test_*.py' -v
python -B tools/refresh_component_releases.py --component catalog
python -B IRGS_Catalog/verify_catalog.py
```

Optional verified reconstruction writes only a new output file:

```text
python -B IRGS_Catalog/historical_details_package.py reassemble IRGS_Catalog/historical_details/manifest.json /tmp/historical-details-original.zip
```

The output is created only after validating all parts, the original ZIP identity,
every member, delivery bindings and collection counts. Existing output files are
preserved. Failed checks leave no completed reconstructed output.

## Manifest contract, version 1

`manifest.json` is UTF-8 JSON, at most 1 MiB. Consumers pin its exact SHA-256 and
the exact Catalog commit. Core fields match the Engine multipart reader's current
working contract; coordinator review of committed Engine/App versions remains
required before selecting a candidate dependency set.

| Field | Meaning |
| --- | --- |
| `schema_version` | Integer `1`. |
| `id`, `display_name` | `historical-details`, `Historical Details`. |
| `status` | `complete` only after full source verification; currently `blocked_missing_source`. |
| `archive` | Original `name`, exact `bytes`, lowercase SHA-256 `sha256`. |
| `part_size_bytes` | Integer `16777216`. |
| `parts` | Ordered records containing one-based `ordinal`, relative `path`, `bytes`, `sha256`. Empty while blocked. |
| `source_verification` | `verified_from_complete_payload` or `not_run_missing_source`. |
| `coverage` | Full-byte preservation status, member-index binding, delivery-binding count and ten collection bindings with record counts. |

Part paths are exactly
`parts/IRGS_Historical_Grand_Archive_v1_1.zip.part0001` through `.part0032`.
Paths must be portable and contained in this directory; links, duplicate names,
reordering, truncated parts, unrecorded parts and changed hashes fail verification.
The manifest never authorizes another source identity or path automatically.

For a complete package, `coverage.member_inventory` binds
`member_inventory.json` by path, bytes, SHA-256 and member count. The separate
index binds the original archive identity and records every file's archive path,
ZIP ordinal, uncompressed bytes, SHA-256 and delivery-manifest coverage. It lists
unbound members explicitly. Keeping the full index separate prevents thousands
of member records from exceeding the Engine selection-manifest limit.

The ten reader collections are a **partial view of the preserved full archive**.
Collection metadata retains the exact archive member and hash and records parsed
row counts; duplicate source IDs are retained as separate rows. Original records,
source attribution, uncertainty, dates, units and rights remain unchanged inside
the payload. No indexed subset may be labelled as the full archive. A source
declaration or a matching checksum establishes neither historical truth nor a
new license, campaign adoption, player knowledge or scheduled outcomes.

## Current intake

The chat attachment exceeded the environment's 32 MiB transfer limit. The user
then supplied a Drive folder containing extracted archive files, followed by an
exact ZIP file link. Drive metadata confirms the expected original name and size.
The authenticated Drive download rejects files over 256 MiB; the streaming direct
link currently requires sign-in. An accessible streaming download is still needed.
See [intake evidence](intake/README.md). Repacking the extracted files would create
a different ZIP and cannot satisfy the expected original ZIP identity.
