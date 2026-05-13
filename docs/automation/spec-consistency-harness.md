# Spec Consistency Harness

`npm run validate:consistency` runs an offline consistency harness for repository-local spec artifacts. It does not call GitHub, package registries, or any network service.

The harness validates:

- all local JSON files parse successfully;
- every profile id in `conformance/manifest.json` is mentioned in `CONFORMANCE.md`;
- manifest profile dependencies point to known profiles;
- manifest spec documents, schema references, test-vector files, and library-check files exist locally;
- every schema has one valid and one invalid example file;
- manifest test-vector sections and library-check sections exist as top-level keys in the referenced vector JSON;
- local Markdown links and anchors in conformance docs, automation docs, test-vector documentation, and manifest-referenced spec documents resolve locally.

The harness contains a narrow baseline for pre-existing broken anchors in normative documents that this automation-only slice cannot edit. Those entries are reported as `known anchor drift`, tracked in wot-spec#58, and should be removed from the baseline when a separate normative cleanup PR fixes the links.

The harness reports open clarification markers such as `TODO`, `FIXME`, `TBD`, `Offene`, and `wot-spec#NN` as informational output only. These markers are useful during draft work, but the offline harness does not look up issue state.

The harness deliberately does not validate cryptographic correctness, JSON Schema semantics, DIDComm library compatibility, or vector derivation. Those checks remain covered by the dedicated validators in `npm run validate`.

Future consistency checks should detect drift between existing artifacts without silently changing normative behavior. If a proposed check would require new protocol requirements, new wire-format constraints, or stricter conformance claims, make that change in a separate normative PR and update schemas, vectors, `CONFORMANCE.md`, and `conformance/manifest.json` deliberately.
