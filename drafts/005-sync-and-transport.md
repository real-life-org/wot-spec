# WoT Spec 005: Sync and Transport — Research Document

- **Status:** Research
- **Authors:** Anton Tranelis
- **Date:** 2026-04-11

## Abstract

This document captures the research questions, requirements, and methodology for designing the sync and transport layer of the Web of Trust protocol. The goal is a specification that is implementation-independent, CRDT-agnostic, and supports a decentralized network of community-operated relays.

This research is informed by a conversation with Nik Graf (secsync, ORP) on 2026-04-10 and by benchmarks on the current TypeScript implementation.

---

## 1. Requirements

### Functional

**F1: End-to-End Encryption**
All data leaving a device is encrypted and signed. No server ever sees plaintext.

**F2: Offline-First**
The app works fully offline. All mutations happen locally. Sync happens when network is available. The local state is the single source of truth.

**F3: Multi-Device**
The same identity can be used on multiple devices. All devices converge to the same state, even when they come online at different times.

**F4: Multi-User Collaboration**
Multiple users work in shared Spaces. Changes from all members are merged conflict-free.

**F5: Eventual Consistency**
All participants who receive the same messages converge to the same state. Order does not matter.

**F6: CRDT-Agnostic**
The protocol operates on encrypted binary blobs. It does not know whether the underlying CRDT is Yjs, Automerge, or something else.

**F7: Decentralized Relay Infrastructure**
No single point of failure. Communities can operate their own relays. Users on different relays can communicate with each other.

**F8: Membership Management**
Users can be invited to and removed from Spaces. Removed members lose access to future data (key rotation).

**F9: Recovery from Seed**
If a user loses all devices, the complete state must be recoverable from the BIP39 seed alone — via the relay/vault network.

**F10: Protocol Evolution**
The protocol must be versioned. Clients with different protocol versions must be able to coexist.

---

## 2. Research Questions

### Cluster A: Server Architecture & Federation
*"What is a relay, what does it do, how do many work together?"*

| # | Question |
|---|----------|
| A1 | What is the role of the server? Message broker vs. blob store vs. CRDT peer? Do we need relay AND vault or is one enough? |
| A2 | What can a server do when it only sees ciphertext? Compression? Reconciliation? Sedimentree? |
| A3 | How does a network of many relays work? Every community can run their own. Users on different relays must still communicate. |
| A4 | How does a message reach the right relay? If Alice is on Relay A and Bob is on Relay B — who routes? |
| A5 | What state does a relay hold? Only messages for its users? Or also space state for spaces whose members are on this relay? |
| A6 | Can a user be on multiple relays? E.g. community relay for spaces, personal relay for personal data? |
| A7 | What can we learn from existing federated protocols? Matrix (homeserver federation, DAG-based event ordering), Nostr (relay-based, client chooses relays, no inter-relay routing), others? |

### Cluster B: Sync Protocol & Data Model
*"What gets synced, at what granularity, with what mechanism?"*

| # | Question |
|---|----------|
| B1 | How do we sync encrypted CRDTs efficiently? Full state vs. state vector exchange vs. snapshots? What do we learn from secsync? |
| B2 | CRDT-agnosticism as design principle. The protocol must not depend on Yjs or Automerge. The spec must operate at the level of encrypted binary blobs. |
| B3 | How does the CRDT choice influence the sync architecture? Automerge brings its own sync infrastructure (Automerge Repo, Sync Server). Yjs has y-protocols. Keyhive/Sedimentree are Automerge-only. If we want CRDT-agnosticism, our protocol needs its own sync layer underneath. |
| B4 | What message types do we actually need? personal-sync, content, space-invite — are these the right abstractions? |
| B5 | How does multi-device work? Is a Personal Doc the right mechanism to sync spaces between devices? |
| B6 | One doc per space or one doc per module? Benchmarks show 7.8x speedup with module separation, but more complexity. |
| B7 | Is chat a CRDT? Append-only data has no conflicts. CRDT is overhead. |
| B8 | Document growth. A space with chat grows to 10 MB after one year. How do we limit that? |
| B9 | Reconnect costs. Full state exchange on every connect becomes expensive with large docs. |
| B10 | Snapshot strategy. When does who create a snapshot? Byzantine problem with multi-device. |

### Cluster C: Acute Bugs (Current Implementation)
*Symptoms that resolve themselves once A and B are answered.*

| # | Bug |
|---|-----|
| C1 | Sync loop — PersonalDoc changes trigger endless message cascades, browser hangs |
| C2 | Unclear startup order — PersonalSync starts before relay connect, creates failed messages |
| C3 | No clear domain separation — PersonalDoc sync and space sync trigger each other |
| C4 | Demo→RLS migration — Identity from demo app creates ghost spaces in RLS |

---

## 3. Sources

### Protocols & Systems

| Source | Relevant for | What we want to learn |
|--------|-------------|----------------------|
| **Matrix** | Cluster A | Homeserver federation, DAG events, how rooms are distributed across servers |
| **Nostr** | Cluster A | Client-centric relay model, no inter-relay routing, user chooses relays |
| **secsync** (Nik Graf) | Cluster B | Snapshot + OpLog, benchmarks, why he moved away from it |
| **Sedimentree** (Ink & Switch) | Cluster B | Deterministic compression on ciphertext, no coordinator |
| **ORP** (Nik Graf / serenity-kit) | Cluster A+B | RIBLT-based set reconciliation for encrypted data, Nik's answer to the byzantine snapshot problem |
| **Keyhive/BeeKEM** (Ink & Switch) | Cluster A+B | E2EE key management for groups, capabilities-based |
| **Automerge Sync Protocol** | Cluster A+B | Sync server as CRDT peer, state vector exchange |
| **Noosphere** (Subconscious) | Cluster A | Content-addressable, UCAN auth, decentralized name resolution |
| **DXOS/ECHO** | Cluster A | HALO identity, device invitation, P2P+signaling |
| **p2panda** | Cluster A+B | Append-only logs, topic-based replication, confidential discovery, Rust+WASM |
| **NextGraph** | Cluster A+B | E2EE + CRDTs (Yjs AND Automerge) + DIDs + P2P overlay network, closest to our problem space |
| **Willow Protocol** | Cluster A+B | Complete protocol family: Data Model + Meadowcap (capabilities) + Confidential Sync (3D range-based set reconciliation) + Drop Format (transport-agnostic). Destructive editing (real deletion). Most comprehensive spec. |
| **Jazz** | Cluster B | CoJSON, built-in groups with permissions, E2EE with signatures. Sync engine → database evolution. |
| **Loro** | Cluster B | High-performance CRDT with native E2EE in wire protocol (`%ELO` prefix), Yjs interop (`%YJS`). Alternative CRDT engine. |
| **Iroh** (n0-computer) | Cluster A | QUIC-based P2P networking layer. Transport-agnostic sync. Used by p2panda. |
| **DIDComm** | Cluster A | DID-native messaging spec (W3C). Mediator-based delivery. Conceptually relevant, libs stale. |
| **Subduction** (Ink & Switch) | Cluster A+B | Encrypted P2P sync protocol built on Sedimentree. The sync layer for Keyhive/Beelay. |

### Resource Index

#### Matrix
- Spec: [spec.matrix.org](https://spec.matrix.org/latest/)
- MSC Proposals: [github.com/matrix-org/matrix-spec-proposals](https://github.com/matrix-org/matrix-spec-proposals)
- Olm/Megolm Spec: `gitlab.matrix.org/matrix-org/olm`
- vodozemac (Rust): [github.com/matrix-org/vodozemac](https://github.com/matrix-org/vodozemac)
- Security Analysis: [nebuchadnezzar-megolm.github.io](https://nebuchadnezzar-megolm.github.io/static/paper.pdf)

#### Nostr
- Protocol: [github.com/nostr-protocol/nostr](https://github.com/nostr-protocol/nostr)
- NIPs (specs): [github.com/nostr-protocol/nips](https://github.com/nostr-protocol/nips)
- NIP-01 (base protocol): [nips/01.md](https://github.com/nostr-protocol/nips/blob/master/01.md)
- Empirical Analysis Paper (ACM 2025): [dl.acm.org/doi/10.1145/3768994](https://dl.acm.org/doi/10.1145/3768994)

#### secsync
- Repo: [github.com/nikgraf/secsync](https://github.com/nikgraf/secsync)
- Spec + Docs: [secsync.com/docs/specification](https://www.secsync.com/docs/specification)
- Benchmarks: [secsync.com/docs/benchmarks](https://www.secsync.com/docs/benchmarks)
- Talk (React Summit 2024): [gitnation.com — Building E2E Encrypted Apps](https://gitnation.com/contents/building-end-to-end-encrypted-apps-web-and-react-native)
- Talk (Local-first London): [guild.host — Secsync E2E Encryption](https://guild.host/presentations/secsync-end-to-end-encryption-ttc3oc)
- NLnet funding: [nlnet.nl/project/Naisho/](https://nlnet.nl/project/Naisho/)

#### Sedimentree
- Design Doc: [github.com/inkandswitch/keyhive/.../sedimentree.md](https://github.com/inkandswitch/keyhive/blob/main/design/sedimentree.md)
- Beelay Docs: [github.com/automerge/beelay/.../sedimentree.md](https://github.com/automerge/beelay/blob/main/docs/sedimentree.md)
- Keyhive Notebook Ch.5 (Syncing): [inkandswitch.com/keyhive/notebook/05/](https://www.inkandswitch.com/keyhive/notebook/05/)

#### ORP (Operation Reconciliation Protocol)
- Repo: [github.com/serenity-kit/orp](https://github.com/serenity-kit/orp)
- RIBLT Paper (ACM SIGCOMM 2024): [arxiv.org/abs/2402.02668](https://arxiv.org/abs/2402.02668)
- ConflictSync Paper (CRDT + RIBLT, 2025): [arxiv.org/abs/2505.01144](https://arxiv.org/abs/2505.01144)
- CertainSync Paper (2025): [arxiv.org/pdf/2504.08314](https://arxiv.org/pdf/2504.08314)

#### Keyhive / BeeKEM
- Repo: [github.com/inkandswitch/keyhive](https://github.com/inkandswitch/keyhive)
- Notebook (6 chapters): [inkandswitch.com/keyhive/notebook/](https://www.inkandswitch.com/keyhive/notebook/)
- BeeKEM Deep-Dive: [meri.garden — BeeKEM Protocol](https://meri.garden/a-deep-dive-explainer-on-beekem-protocol/)
- Keyhive in WASM: [meri.garden — Keyhive WASM](https://meri.garden/using-keyhive-in-wasm-to-model-capability-groups/)
- RECAP Workshop Paper: [recapworkshop.online — Keyhive](https://recapworkshop.online/recap25/contributions/8-keyhive.html)
- Podcast localfirst.fm #19: [localfirst.fm/19](https://www.localfirst.fm/19)
- Subduction (sync protocol): [github.com/inkandswitch/subduction](https://github.com/inkandswitch/subduction)

#### Automerge Sync Protocol
- Automerge: [github.com/automerge/automerge](https://github.com/automerge/automerge)
- automerge-repo: [github.com/automerge/automerge-repo](https://github.com/automerge/automerge-repo)
- Sync Server: [github.com/automerge/automerge-repo-sync-server](https://github.com/automerge/automerge-repo-sync-server)
- Beelay (next-gen sync): [github.com/automerge/beelay](https://github.com/automerge/beelay)
- Beelay Protocol Spec: [beelay/.../protocol.md](https://github.com/automerge/beelay/blob/main/docs/protocol.md)
- Paper "Local-first software" (Kleppmann et al. 2019): [inkandswitch.com/essay/local-first/](https://www.inkandswitch.com/essay/local-first/)
- Talk "CRDTs: The Hard Parts": [martin.kleppmann.com — Hydra 2020](https://martin.kleppmann.com/2020/07/06/crdt-hard-parts-hydra.html)

#### Noosphere
- Repo: [github.com/subconsciousnetwork/noosphere](https://github.com/subconsciousnetwork/noosphere)
- Explainer: [noosphere/.../explainer.md](https://github.com/subconsciousnetwork/noosphere/blob/main/design/explainer.md)
- Blog: [newsletter.squishy.computer — Noosphere](https://newsletter.squishy.computer/p/noosphere-a-protocol-for-thought)
- Note: Project wound down May 2024, protocol remains open source

#### DXOS / ECHO
- Repo: [github.com/dxos/dxos](https://github.com/dxos/dxos)
- Docs: [docs.dxos.org](https://docs.dxos.org/)
- HALO Identity: [docs.dxos.org/halo/](https://docs.dxos.org/halo/introduction/)
- Blog — Invitations: [blog.dxos.org — How local-first multiplayer works](https://blog.dxos.org/how-local-first-multiplayer-works-in-dxos-apps/)

#### p2panda
- Repo: [github.com/p2panda/p2panda](https://github.com/p2panda/p2panda)
- aquadoggo (node): [github.com/p2panda/aquadoggo](https://github.com/p2panda/aquadoggo)
- Specs: [aquadoggo.p2panda.org/specifications/](https://aquadoggo.p2panda.org/specifications/)
- namakemono Spec: [aquadoggo.p2panda.org/specifications/namakemono/](https://aquadoggo.p2panda.org/specifications/namakemono/)
- Access Control: [github.com/p2panda/access-control](https://github.com/p2panda/access-control)
- FOSDEM 2026 Talk: [fosdem.org — p2panda modal reflection](https://fosdem.org/2026/schedule/event/MCVBNK-p2panda-modal-reflection/)
- NLnet funding: [nlnet.nl/project/P2Panda/](https://nlnet.nl/project/P2Panda/)

#### NextGraph

- Website: [nextgraph.org](https://nextgraph.org/)
- Repo: [git.nextgraph.org/NextGraph](https://git.nextgraph.org/NextGraph)
- Docs: [docs.nextgraph.org](https://docs.nextgraph.org/)
- Workshop (Local-First Conf 2025): [youtube.com/watch?v=gaadDmZWIzE](https://www.youtube.com/watch?v=gaadDmZWIzE)
- FOSDEM 2026 Talk: [fosdem.org/2026/schedule/speaker/niko_bonnieure/](https://fosdem.org/2026/schedule/speaker/niko_bonnieure/)

#### Willow Protocol

- Website: [willowprotocol.org](https://willowprotocol.org/)
- Specs (6 primary + 8 supporting): [willowprotocol.org/specs/](https://willowprotocol.org/specs/index.html)
- Data Model, Meadowcap (capabilities), Confidential Sync, Drop Format, WTP, Willow'25
- Supporting: grouping, encoding, E2EE, private area intersection, handshake, 3D range-based set reconciliation, multiplexing, URIs
- Earthstar (TypeScript implementation): [github.com/earthstar-project](https://github.com/earthstar-project)

#### Jazz

- Website: [jazz.tools](https://jazz.tools/)
- Repo: [github.com/garden-co/jazz](https://github.com/garden-co/jazz)
- Talk (Sync Conf 2025): [youtube.com/watch?v=wils2KFCgEU](https://www.youtube.com/watch?v=wils2KFCgEU)

#### Loro

- Website: [loro.dev](https://loro.dev/)
- Repo: [github.com/loro-dev/loro](https://github.com/loro-dev/loro)
- Wire Protocol (incl. E2EE `%ELO`): [loro.dev/blog/loro-protocol](https://loro.dev/blog/loro-protocol)

#### Iroh (n0-computer)

- Website: [iroh.computer](https://iroh.computer/)
- Repo: [github.com/n0-computer/iroh](https://github.com/n0-computer/iroh)
- Talk (Sync Conf 2025): [youtube.com/watch?v=sN99A7KWUJ0](https://www.youtube.com/watch?v=sN99A7KWUJ0)

#### DIDComm

- Spec: [identity.foundation/didcomm-messaging/spec/](https://identity.foundation/didcomm-messaging/spec/)
- Repo: [github.com/decentralized-identity/didcomm-messaging](https://github.com/decentralized-identity/didcomm-messaging)

#### Subduction (Ink & Switch)

- Repo: [github.com/inkandswitch/subduction](https://github.com/inkandswitch/subduction)
- Brooklyn Zelenka's notes: [notes.brooklynzelenka.com/Notes/Subduction](https://notes.brooklynzelenka.com/Notes/Subduction)

### Local-First Conf — Relevant Talks

| Talk | Speaker | URL | Relevance |
|------|---------|-----|-----------|
| Keyhive: Local-first access control with E2EE | Brooklyn Zelenka | [youtube](https://www.youtube.com/watch?v=iLp2xBMud10) | E2EE key management, capabilities |
| Beelay: encrypted sync protocol for CRDTs | Alex Good | [youtube](https://www.youtube.com/watch?v=neRuBAPAsE0) | Encrypted CRDT sync, Automerge team |
| E2EE demystified | Nik Graf | [youtube](https://www.youtube.com/watch?v=uJLr8L-D9LE) | secsync architecture decisions |
| NextGraph: P2P and E2EE social apps | Niko Bonnieure | [youtube](https://www.youtube.com/watch?v=gaadDmZWIzE) | E2EE + CRDTs + DIDs + P2P overlay |
| CRDT performance tradeoffs | Kevin Jahns | [youtube](https://www.youtube.com/watch?v=wjUfqFWpI2k) | Yjs author on performance |
| UCAN: Be in control of your auth | Brooklyn Zelenka | [youtube](https://www.youtube.com/watch?v=_fziCbcKAd4) | Capabilities-based auth |
| Practical local-first permissions | Andrei Popa | [youtube](https://www.youtube.com/watch?v=ddBPPAYvd1Y) | Membership/permissions patterns |
| Can sync be transport agnostic? | Brendan O'Brien | [youtube](https://www.youtube.com/watch?v=sN99A7KWUJ0) | Transport layer design |
| Yjs sync via Cloudflare Workers | Timo Wilhelm | [youtube](https://www.youtube.com/watch?v=CDNGdrJajRc) | Alternative Yjs relay architecture |
| The past, present, future of local-first | Martin Kleppmann | [youtube](https://www.youtube.com/watch?v=NMq0vncHJvU) | Strategic overview |
| Local First: the secret master plan | Peter Van Hardenberg | [youtube](https://www.youtube.com/watch?v=9s8OA08ggbM) | Ink & Switch research frontiers |
| General-purpose sync with IVM | Aaron Boodman | [youtube](https://www.youtube.com/watch?v=39CizIAHpw0) | Sync engine architecture |
| Event sourcing in local-first apps | Johannes Schickling | [youtube](https://www.youtube.com/watch?v=nyPl84BopKc) | Alternative to CRDT sync |
| Your data, your rules | Gozalishvili & Joel | [youtube](https://www.youtube.com/watch?v=4n-2AXhbZPw) | Selective sharing patterns |

### Community & Ecosystem

- **Local First News**: [localfirstnews.com](https://www.localfirstnews.com/) — curated overview of the local-first ecosystem
- **Local-First Conf** (talks): [youtube.com/@localfirstconf](https://www.youtube.com/@localfirstconf/videos)
- **localfirst.fm** (podcast): [localfirst.fm](https://www.localfirst.fm/)
- **Ink & Switch** research: [inkandswitch.com](https://www.inkandswitch.com/)

### People

- **Nik Graf** — walked the path secsync → ORP himself, concrete experience (call 2026-04-10)
- **Sebastian Galek** — co-author of wot-spec, Rust implementation (Human Money Core), brings different perspective
- **Ink & Switch** (Martin Kleppmann, Brooklyn Zelenka et al.) — research on Keyhive, Sedimentree, local-first
- **Gordon Brander** — Noosphere/Subconscious, thinking about decentralized knowledge graphs

### Key Insight from Nik Graf (2026-04-10)

Nik's evolution: Serenity → secsync → ORP. Key learnings:

1. **Individual encrypted updates become slow over time.** 250k changes: individual = 1.6s load, snapshot = 18ms (90x faster).
2. **Snapshots solve performance but create the byzantine problem.** Multiple clients creating snapshots in parallel, going offline/online — merge becomes chaotic.
3. **Sedimentree solves this** with deterministic compression. Chunk boundaries are computed from hash properties — all peers independently arrive at the same chunks. No coordinator needed.
4. **ORP (RIBLT)** enables efficient set reconciliation: two peers identify their differences without exchanging complete datasets.

---

## 4. Design-Space Exploration: First Findings

Based on analysis of four talks from Local-First Conf 2024/2025 (Beelay, Keyhive, NextGraph, secsync) and the conversation with Nik Graf (2026-04-10).

### 4.1 Emerging Consensus

All four projects converge on the same fundamental architecture:

1. **Server sees only encrypted blobs** — not a CRDT peer, not a message broker with routing logic. The server stores and forwards ciphertext. Period.

2. **Deterministic compression** (Sedimentree) solves the byzantine snapshot problem. Chunk boundaries are computed from hash properties (leading zeros). All peers independently arrive at the same chunks without coordination.

3. **RIBLT for set reconciliation** — the amount of data exchanged is 1.3-1.7x the actual difference. Solves the "airplane problem": two peers who mostly agree exchange only what's different.

4. **Auth as a CRDT** (Keyhive Capabilities) — not server middleware. Signed delegation chains travel with the data. No central auth server needed.

5. **CRDT-agnostic at protocol level** — Beelay: "anything shaped like a commit graph". NextGraph: Automerge + Yjs + RDF in one system. The sync layer operates on encrypted binary blobs.

### 4.2 Comparison Matrix

| Aspect | Beelay | Keyhive | NextGraph | secsync/ORP |
|--------|--------|---------|-----------|-------------|
| **Server role** | Blob store for encrypted chunks | Untrusted, ciphertext only | Broker: store-and-forward | Central relay + snapshot store |
| **Compression** | Sedimentree (deterministic) | Sedimentree (same stack) | Not specified | Snapshots (client-side) → ORP |
| **Set reconciliation** | RIBLT | Via Beelay | Own protocol | RIBLT (in ORP) |
| **Auth model** | Via Keyhive (capabilities) | Capability graph (CRDT) | Cryptographic capabilities + inbox | Invitation URLs |
| **CRDT-agnostic** | Yes | Yes | Yes (AM + Yjs + RDF) | Yes (Yjs + AM) |
| **Multi-server** | Not addressed | Not addressed | Multi-broker with failover | Not addressed |
| **Maturity** | Alpha (prototype) | Alpha | Protocol ready, framework 2025/26 | Beta (secsync), early (ORP) |

### 4.3 Key Findings per Research Question

**Cluster A: Server Architecture**

| Question | Finding |
|----------|---------|
| A1: Server role | Consensus: **encrypted blob store**, not CRDT peer. Server stores/forwards ciphertext. Client does all CRDT logic. |
| A2: What can server do with ciphertext? | Store chunks, serve them by hash. Sedimentree chunks are content-addressed — server doesn't need to understand them. |
| A3: Network of relays | Only NextGraph addresses this: **multi-broker with replication and failover**. User chooses brokers. No domain names needed (IP only). |
| A4: Cross-relay routing | NextGraph: **Inbox system** — each user has inbox on their broker(s), identified by public key. Sender encrypts to inbox pubkey. No routing needed — sender knows recipient's broker. |
| A5: What state does relay hold? | Encrypted chunks (Beelay) or encrypted messages (NextGraph). Never plaintext. |
| A6: User on multiple relays | NextGraph: Yes — data replicated to multiple brokers for availability/failover. |
| A7: Learn from existing protocols | NextGraph's broker model is closest to Nostr (client chooses relays, no inter-relay routing). But with E2EE and CRDT sync instead of signed events. |

**Cluster B: Sync Protocol**

| Question | Finding |
|----------|---------|
| B1: Efficient E2EE CRDT sync | **Sedimentree + RIBLT**. Not full state, not snapshots, not individual updates. Deterministic chunks + set reconciliation. Data exchanged ≈ 1.3x actual difference. |
| B2: CRDT-agnosticism | All projects achieve this. Key: operate on **commit graphs** or **encrypted binary blobs**, not on CRDT-specific primitives. |
| B4: Message types | Keyhive reduces to two concepts: **commits** (data) and **delegations** (auth). Everything else is infrastructure. Simpler than our current personal-sync/content/space-invite distinction. |
| B5: Multi-device | NextGraph: three stores (private/protected/public) + group stores. No single "PersonalDoc" that causes loops. |
| B10: Snapshot strategy | **Sedimentree eliminates the question**. No "who creates the snapshot" — compression is deterministic and coordination-free. |

### 4.4 Gap: Federation

The biggest gap across all four projects: **none except NextGraph addresses multi-server federation seriously**. Beelay and Keyhive assume a single sync server (or direct peer connections). This is an area where we need to look at Matrix and Nostr more deeply, or adopt NextGraph's broker model.

### 4.5 Implications for WoT

Our current architecture (Message-broker Relay + Snapshot-replace Vault + CompactStore) maps to none of the above cleanly. The research suggests we should move toward:

1. **Merge Relay and Vault** into a single encrypted blob store (like Beelay/NextGraph broker)
2. **Replace Full State Exchange** with Sedimentree + RIBLT (or at minimum, State Vector Exchange)
3. **Replace our PersonalDoc-triggers-everything pattern** with a cleaner separation (NextGraph's three stores)
4. **Adopt a capability model** for auth instead of manual Group Key distribution
5. **Design for multi-broker** from the start (NextGraph's model)

These are not immediate implementation changes — they are the direction for the protocol specification.

---

## 5. Synthesis: Answering Our Research Questions

Based on deep-dive analysis of Matrix, Nostr, Willow, p2panda/Iroh, Beelay/Sedimentree/Subduction, and secsync/ORP.

### Cluster A: Server Architecture & Federation

**A1: What is the role of the server?**

> **Answer: Encrypted Blob Store + Store-and-Forward Inbox.**

All analyzed projects converge: the server stores encrypted data and forwards it. It never sees plaintext. But the exact model varies:

| Model | Who uses it | Tradeoffs |
|-------|-------------|-----------|
| Message Broker (relay queues until ACK) | Our current Relay, Nostr | Simple, but no state — can't help with sync efficiency |
| Encrypted Blob Store (content-addressed chunks) | Beelay/Subduction | Server can serve chunks by hash, enables efficient sync, stateless |
| Broker (store-and-forward + availability) | NextGraph | Best of both — messages + persistent data, multi-broker failover |
| P2P with Shared Nodes (always-online peer) | p2panda | Most decentralized, shared nodes are conceptually identical to brokers |

**Recommendation for WoT:** Combine the Blob Store (Beelay) with the Broker model (NextGraph). Our server should:
1. Store encrypted Sedimentree chunks (content-addressed, persistent)
2. Provide an inbox for async message delivery (store-and-forward)
3. Be operable by any community (like Nostr relays, but with WoT authorization)
4. NOT be a CRDT peer — all CRDT logic stays on the client

This merges our current Relay + Vault into one service.

---

**A2: What can a server do when it only sees ciphertext?**

> **Answer: Store chunks by hash, serve them on request, track reachability, provide RIBLT symbols.**

Specifically (from Beelay/Subduction):
- Maintain a reachability index (which documents link to which — this is a simple CRDT itself, not encrypted)
- Compute and serve RIBLT coded symbols for collection-level reconciliation
- Serve Sedimentree summaries (fragment boundaries, checkpoint hashes — metadata, not content)
- Serve blob parts by hash + offset + length (range requests)
- Accept uploads of new commits/fragments

What it CANNOT do: compress, merge, validate content, run queries, or understand the data in any way.

From Willow: the server can also do Private Interest Overlap (PIO) — help peers discover shared interests without revealing non-shared ones. This is valuable for WoT discovery.

---

**A3: How does a network of many relays work?**

> **Answer: Client-centric model with multi-broker replication. No inter-relay routing.**

Three models emerged:

| Model | How it works | Problem |
|-------|-------------|---------|
| **Matrix Federation** | Servers route to each other via Server-Server API | Massive complexity, State Resolution bottleneck, account = server |
| **Nostr Multi-Relay** | Client publishes to N relays, recipient checks sender's relays | 98% redundant traffic, 95% of relays can't cover costs |
| **NextGraph Multi-Broker** | User replicates to 2-3 brokers, automatic failover | Simplest, most robust, no inter-relay protocol needed |

**Recommendation for WoT:** NextGraph's broker model. Each user chooses 1-3 brokers. Data is replicated across them. No federation protocol between brokers — the client handles replication.

This avoids Matrix's complexity and Nostr's redundancy problem. Communities operate their own brokers. Users can move between brokers because identity lives in the key, not on the server.

---

**A4: How does a message reach the right relay?**

> **Answer: Sender knows recipient's broker(s) via published relay list or direct exchange.**

Two approaches:

| Approach | How | Used by |
|----------|-----|---------|
| **Relay List** | User publishes their broker URLs (like Nostr NIP-65) | Nostr, could work for WoT |
| **Inbox** | User has a pubkey-addressed mailbox on their broker(s) | NextGraph |

**Recommendation for WoT:** Combine both. Users publish their broker list in their public profile (wot-profiles). Senders encrypt messages to the recipient's inbox pubkey and deliver to their broker(s). If the broker is offline, try the next one.

No routing between brokers needed. The client knows where to send because the recipient's profile says so.

---

**A5: What state does a relay hold?**

> **Answer: Encrypted Sedimentree chunks + inbox messages. No plaintext, no CRDT state.**

Specifically:
- **Sedimentree fragments** (content-addressed encrypted blobs) for each document the relay hosts
- **Sedimentree metadata** (fragment boundaries, checkpoint hashes) for sync
- **Inbox messages** (encrypted, store-and-forward, deleted after delivery)
- **Reachability index** (which documents are transitively linked — a simple CRDT)

The relay does NOT hold: decryption keys, membership lists, CRDT state, user data in plaintext.

---

**A6: Can a user be on multiple relays?**

> **Answer: Yes. This is the default mode, not an edge case.**

From NextGraph: users replicate to 2-3 brokers for availability and failover. From Nostr: users publish to multiple relays (average 34.6 copies, but that's excessive).

**Recommendation for WoT:** 2-3 brokers per user. One primary (community-operated), one backup (personal or public). Data is replicated to all. Failover is automatic — if primary is down, client uses backup.

Matrix's fundamental problem (account = server, no portability) does not exist for us because our identity lives in the BIP39 seed, not on any server.

---

**A7: What can we learn from existing federated protocols?**

> **Answer: Simplicity wins. Federation is the enemy of simplicity.**

| Protocol | Lesson |
|----------|--------|
| **Matrix** | Federation works at scale (28M accounts) but adds enormous complexity. State Resolution is a bottleneck. Account portability is unsolved after 10 years. Don't do this. |
| **Nostr** | Radical simplicity works. Three message types. $5/month server. But: no routing, no state, 98% redundant traffic. Take the simplicity, add structure. |
| **NextGraph** | The sweet spot: broker model with replication, no federation protocol, no DNS dependency. This is what we should build. |
| **p2panda** | Shared Nodes (always-online peers) are the most elegant server concept. They're just peers that happen to be always on. |

**The key insight:** Don't build federation. Build replication. The client replicates to multiple brokers. If a broker goes down, the data is on the others. No inter-broker protocol needed.

---

### Cluster B: Sync Protocol & Data Model

**B1: How do we sync encrypted CRDTs efficiently?**

> **Answer: RIBLT for set reconciliation + Sedimentree for compression. Not full state, not snapshots, not individual updates.**

The evidence is overwhelming:

| Approach | Bandwidth | Problem |
|----------|-----------|---------|
| Individual encrypted updates | O(N) — all updates | Slow at scale (secsync benchmarks: 29s for 250k changes) |
| Full state exchange | O(doc size) — entire doc | Wasteful when peers mostly agree |
| Snapshots | O(snapshot) — compressed | Byzantine problem with multi-device |
| **Sedimentree + RIBLT** | **O(diff)** — only what's different | **No coordinator needed, 1.35x overhead** |

Concrete numbers from Beelay:
- 1 billion items, 5 differences → ~240 bytes communication
- Typical sync: 1.5-2 round trips
- Server is stateless — horizontal scaling possible

This is the clear winner. The question is whether to adopt Subduction directly or build our own implementation using the same algorithms.

---

**B2: CRDT-agnosticism as design principle.**

> **Answer: Achieved by operating on hash-linked DAGs of opaque blobs.**

Beelay requires: `CommitId` (32 bytes, hash of content) + `Parents` (set of parent CommitIds). That's all. The sync layer doesn't know what's inside the commits.

For Yjs compatibility: Yjs doesn't naturally produce a hash-linked DAG (it uses State Vectors). An adapter would need to:
1. Hash each Yjs update with BLAKE3 → CommitId
2. Track parent relationships (which updates depend on which)
3. Expose via `CommitStore` + `Parents` traits

This is non-trivial but feasible. p2panda proves it: their "Bring your own CRDT" approach works with Yjs.

**Recommendation:** Our protocol spec (wot-spec) describes encrypted blobs with hash-linked DAG structure. The CRDT adapter (implementation-level) translates Yjs/Automerge into this structure.

---

**B3: How does the CRDT choice influence the sync architecture?**

> **Answer: It doesn't, IF the protocol operates on the DAG layer.**

Automerge: natural hash-linked DAG, direct integration with Beelay/Subduction.
Yjs: needs adapter (State Vectors → DAG), but works.
Loro: has native wire protocol with E2EE support (`%ELO`), could be a future option.

**The adapter pattern works.** p2panda, NextGraph, and Beelay all prove this. Our existing adapter architecture (ReplicationAdapter, StorageAdapter, CryptoAdapter) is the right design.

---

**B4: What message types do we actually need?**

> **Answer: Two concepts: Commits (data) and Delegations (auth). Everything else is infrastructure.**

Keyhive reduces the entire model to:
- **Commits** — CRDT operations (encrypted, content-addressed)
- **Delegations** — capability chains (signed, self-certifying)

Our current types (personal-sync, content, space-invite, group-key-rotation) map to:
- `personal-sync` → commits on personal document
- `content` → commits on space document
- `space-invite` → delegation (capability grant) + initial commits
- `group-key-rotation` → delegation (new key distribution)

**Recommendation:** Simplify to commits + delegations at the protocol level. Message type is a routing hint, not a fundamental concept.

---

**B5: How does multi-device work?**

> **Answer: Not via a single PersonalDoc that triggers everything. Three separate stores.**

NextGraph's model: Private (self only) / Protected (shared) / Public. Plus Group stores.
p2panda: Topics as the unit of sync. Each topic is independent.

Our PersonalDoc mixes everything: spaces, keys, contacts, profile. This causes the sync loop (C1-C4). The fix is architectural, not a guard or debounce.

**Recommendation:** Split PersonalDoc into:
1. **Identity store** — profile, contacts, verifications (synced between own devices)
2. **Key store** — group keys, encrypted at rest (synced between own devices)
3. **Space stores** — one per space, independent (synced with space members)

Each store syncs independently. No cross-triggering.

---

**B6: One doc per space or one doc per module?**

> **Answer: One doc per module, at least for chat.**

Our benchmarks show 7.8x speedup for delta operations with module separation. Doc growth analysis shows chat is the primary growth driver (10 MB/year).

p2panda's architecture naturally supports this: each topic can be a module within a space. Beelay's collection-level RIBLT handles many small documents efficiently.

**Recommendation:** Separate chat from other modules. Contacts + attestations can share a doc (they grow slowly). Chat gets its own doc (or isn't a CRDT at all — see B7).

---

**B7: Is chat a CRDT?**

> **Answer: Probably not. Append-only data has no conflicts. A simpler model suffices.**

Chat messages don't need conflict resolution — they're append-only. A CRDT adds overhead (tombstones, vector clocks, merge complexity) for no benefit.

p2panda's approach: append-only logs (Namakemono) for sequential data, CRDTs for collaborative data. NextGraph's inbox system: encrypted messages delivered async.

**Recommendation:** Chat as encrypted append-only messages delivered via inbox/relay, persisted locally. Not a CRDT document. This eliminates the biggest growth driver from our CRDT sync.

---

**B8: Document growth — how to limit it?**

> **Answer: Sedimentree compression + shallow document history + separate chat.**

Three mechanisms:
1. **Sedimentree** compresses old history into exponentially larger chunks (1M commits → ~15 level-2 fragments)
2. **Shallow documents** (p2panda/Namakemono) — keep only last N operations per author, garbage-collect the rest
3. **Separate chat** (B7) — biggest growth driver is no longer in the CRDT

Willow adds: **Prefix Pruning** — true deletion in a CRDT-like system. Write to a parent path, all children with older timestamps are deleted.

---

**B9: Reconnect costs?**

> **Answer: With RIBLT, reconnect cost is proportional to what changed, not to document size.**

Our current approach: full state exchange on every connect. With 5k contacts: 45ms (our benchmark).

With RIBLT: exchange only the difference. If 5 things changed since last sync: ~240 bytes, regardless of total document size. This eliminates reconnect as a scaling concern.

---

**B10: Snapshot strategy — byzantine problem?**

> **Answer: Sedimentree eliminates the question entirely.**

No "who creates the snapshot" decision needed. Chunk boundaries are deterministic (leading zeros in BLAKE3 hash). All peers independently compute the same chunks. The chunks themselves are a CRDT — no coordination, no byzantine problem.

secsync tried centralized snapshots → failed (byzantine problem). Sedimentree solved it by making compression deterministic and coordination-free.

---

### Architecture Proposal

Based on all findings, the WoT sync and transport architecture should be:

```
┌─────────────────────────────────────────────────────────────┐
│                        CLIENT                               │
│                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌───────────┐  │
│  │ Identity │  │ Key      │  │ Space    │  │ Space     │  │
│  │ Store    │  │ Store    │  │ Store A  │  │ Store B   │  │
│  │ (private)│  │ (private)│  │ (shared) │  │ (shared)  │  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └─────┬─────┘  │
│       │              │             │              │         │
│  ┌────┴──────────────┴─────────────┴──────────────┴─────┐  │
│  │              CRDT Adapter (Yjs / Automerge)          │  │
│  └────┬─────────────────────────────────────────────────┘  │
│       │                                                     │
│  ┌────┴─────────────────────────────────────────────────┐  │
│  │           Sedimentree (deterministic chunking)        │  │
│  │           + RIBLT (set reconciliation)                │  │
│  └────┬─────────────────────────────────────────────────┘  │
│       │                                                     │
│  ┌────┴─────────────────────────────────────────────────┐  │
│  │           E2EE Layer                                  │  │
│  │           Symmetric (spaces) + Double Ratchet (1:1)  │  │
│  └────┬─────────────────────────────────────────────────┘  │
│       │                                                     │
│  ┌────┴─────────────────────────────────────────────────┐  │
│  │           Transport (WebSocket / QUIC / Iroh)         │  │
│  └────┬─────────────────────────────────────────────────┘  │
│       │                                                     │
└───────┼─────────────────────────────────────────────────────┘
        │
   ┌────┴────┐     ┌─────────┐
   │ Broker  │────│ Broker  │   (community-operated, no federation)
   │    A    │     │    B    │   (client replicates to both)
   └─────────┘     └─────────┘
```

**Decision: Combine (Option B from our guide).**

We don't adopt any single protocol wholesale. We combine:
- **Sedimentree + RIBLT** from Beelay/Subduction (sync mechanism)
- **Broker model** from NextGraph (server architecture)
- **Two-schema encryption** from p2panda (symmetric + Double Ratchet)
- **Capability model** inspired by Keyhive/Meadowcap (auth)
- **Formal security model** from secsync (threat analysis)
- **Simplicity principle** from Nostr (dumb servers, smart clients)
- **Privacy discovery** from Willow (PIO for space discovery)
- **Our own identity** (BIP39 + Ed25519 + did:key)
- **Our own CRDT adapter** (Yjs/Automerge behind interface)

**What we build ourselves:**
- The protocol specification (wot-spec)
- The broker implementation (TypeScript, simple, community-operable)
- The CRDT adapter layer
- The WoT-specific authorization (trust graph as auth source)

**What we adopt/import:**
- RIBLT algorithm (from ORP — TypeScript implementation exists!)
- Sedimentree algorithm (from Subduction — Rust+WASM, or reimplement in TS)
- Iroh as optional transport (Rust+WASM, for NAT traversal when needed)
- secsync's threat model and Verifpal proofs as security baseline

### Updated Findings from Second Round of Deep-Dives

The second round (Keyhive BeeKEM notebook, Jazz, Loro, Ossa, DXOS, Noosphere, research papers) refines the architecture proposal:

#### Permissions Model: Jazz over Keyhive (for now)

Jazz's group permissions model is the most pragmatic fit for our current needs:
- 5 roles (Admin/Manager/Writer/Reader/WriteOnly), cryptographically enforced
- Write = Ed25519 signature per transaction, Read = symmetric key (XSalsa20)
- Automatic key rotation on member removal
- Server CANNOT read (E2EE) and CANNOT forge (signatures)
- Pure TypeScript, no WASM dependency

Keyhive (BeeKEM) is theoretically superior (conflict keys, no server needed) but:
- Pre-alpha, not audited
- Forward secrecy deliberately sacrificed
- Mutual admin revocation is an open research question
- Rust/WASM only

**Recommendation:** Start with Jazz-style group permissions (simpler, TypeScript). Design the adapter interface so Keyhive can be swapped in later.

#### CRDT Engine: Yjs now, Loro as migration path

Loro's wire protocol supports `%YJS` — Yjs clients can sync with a Loro server. This creates a seamless migration path:
- Phase 1: Yjs (current, proven, 69KB bundle)
- Phase 2: Loro server with Yjs interop (get Shallow Snapshots + Moveable Tree)
- Phase 3: Full Loro (when WASM bundle size is acceptable for mobile)

Loro's Shallow Snapshots solve our document growth problem without Sedimentree.

#### Key Agreement: MLS vs Keyhive — open question

Kerkour's analysis raises a valid point: "Keyhive is designed for P2P. We have a server anyway, so MLS may be more appropriate."

| Aspect | MLS (RFC 9420) | Keyhive/BeeKEM |
|--------|---------------|----------------|
| Forward Secrecy | Yes | No (deliberate) |
| Post-Compromise Security | Yes | Yes |
| Server required | Yes (ordering) | No |
| Concurrency | Needs total order | Conflict keys handle it |
| Standard | IETF RFC | Research project |
| Maturity | Production (Signal, Matrix) | Pre-alpha |

Since our architecture has brokers (servers), MLS's requirement for ordering is not a blocker. But Keyhive's conflict keys are more natural for CRDTs. **Decision deferred — needs prototyping.**

#### ACL Consistency: An open research question

Ossa's Parker hypothesizes: "Secure decentralized access control REQUIRES total ordering." This contradicts Keyhive's approach (causal ordering suffices). Jazz avoids the question by making key rotation a simple group operation (but has race conditions with concurrent admin actions).

For our MVP: Creator-only removal (our current model) is pragmatically safe. For production: this needs resolution.

#### UCAN for Broker Delegation

From Noosphere: UCAN enables users to delegate publish-rights to brokers WITHOUT sharing private keys. Directly applicable to our broker model — the broker can store and forward data on behalf of the user without ever having the user's keys.

#### Hybrid Sync: CertainSync + RIBLT

From the research papers: CertainSync Extended Hamming for d ≤ 3 (guaranteed, most common case: short offline), RIBLT for d > 3. ConflictSync's Bloom pre-filter for < 93% similarity. These can be combined for optimal efficiency across all scenarios.

#### Architectural Convergence

Gordon Brander (Noosphere) observed: "All similar projects converged to: self-sovereign keys + decentralized data + ordinary servers." This validates our direction. DXOS's invitation flow (7-step challenge-response) and control/data feed separation further confirm our architecture.

#### Jazz as Infrastructure Layer — a serious candidate

Jazz (y-jazz, auto-jazz, loro-jazz) wraps any CRDT library with Groups + Permissions + E2EE + Sync. The sync server is completely oblivious — it only syncs encrypted diffs. This is exactly what Kleppmann's "Generic Syncing Service" vision describes.

Key question for us: **Do we adopt Jazz as our infrastructure layer?** Or take only the concepts?

Arguments for adopting Jazz:
- y-jazz gives us Yjs + permissions + E2EE + sync in one package
- TypeScript, MIT license, actively developed
- Groups with 5 roles, key rotation, Ed25519 signatures — almost identical to what we need
- Sync server is self-hostable (`npx jazz-run sync`)
- Growing ecosystem (social networks, Figma/Notion alternatives built on it)

Arguments for building ourselves:
- Jazz uses its own identity system (no BIP39, no did:key)
- All devices of an account share one keypair (we have per-device keys via HKDF)
- No RIBLT/Sedimentree (full history sync, no deterministic compression)
- Vendor dependency (Garden Computing)
- CoJSON is proprietary CRDT format (y-jazz wraps Yjs but adds overhead)

**Recommendation:** Evaluate y-jazz as a pragmatic shortcut for MVP. If it works with our identity layer, it could save months of implementation. But design our protocol spec (wot-spec) independently — Jazz is an implementation option, not the protocol.

#### Version Control as Platform Feature (Ink & Switch / Patchwork)

Van Hardenberg's talk reveals why Automerge matters beyond just "another CRDT":

> "Automerge is uniquely designed not just around convergence, but about realizing that the creative process is about convergence AND divergence."

Branching, merging, review, proposals — all built into the commit graph. This is what Sedimentree compresses. This is what Beelay syncs. This is not possible with Yjs (no natural commit history).

For our project this means:
- **Short term:** Yjs (performance, bundle size, ecosystem)
- **Long term:** Automerge when Beelay/Keyhive are stable — we get version control, E2EE, and malleable software for free
- **The adapter pattern** makes this transition possible without breaking apps

#### Kleppmann's Vision = Our Vision

> "A generic syncing service, app-independent, standardized protocol, multiple interoperable providers."

This is exactly what we're building:
- wot-spec = the protocol standard
- Broker = the syncing service (community-operated)
- WoT + RLS apps = the apps on top
- Sebastian's Rust implementation = second provider proving interoperability

We are not just building an app. We are building infrastructure for a new way of making software.

#### Final Architecture Decision Matrix

| Component | Short-term (MVP) | Mid-term (Production) | Long-term (Vision) |
|-----------|-----------------|----------------------|-------------------|
| **CRDT** | Yjs (proven, fast) | Yjs + Loro interop | Automerge (version control) |
| **Sync** | Current Relay (fix bugs) | RIBLT (from ORP, TypeScript) | Sedimentree + RIBLT (Subduction) |
| **Auth** | Jazz-style groups OR own GroupKeyService | Capability model (Keyhive-inspired) | Keyhive/BeeKEM (when stable) |
| **Encryption** | AES-256-GCM (current) | Two-schema (symmetric + Double Ratchet) | MLS or BeeKEM (when decided) |
| **Server** | Relay + Vault (current, fix loops) | Unified Broker (NextGraph model) | Multi-Broker network |
| **Transport** | WebSocket | WebSocket + Iroh (optional) | QUIC Multipath |
| **Identity** | BIP39 + Ed25519 + did:key | Same | Same (non-negotiable) |
| **Data Model** | PersonalDoc (fix separation) | Identity/Key/Space stores | Per-module docs + append-only chat |

---

*This synthesis was produced on 2026-04-11/12 based on deep-dive analysis of 10 projects, 4 research papers, and 9 conference talks spanning the entire local-first ecosystem.*

---

## 6. Source Profiles

Standardized profiles per source. These feed directly into the synthesis (Step 4).

### Profile Template

```
### [Project Name]

**Type:** Protocol / Library / Framework / Research
**License:** ...
**Language:** ...
**Maturity:** Production / Beta / Alpha / Research
**Usable as:** Whole protocol / Individual modules / Inspiration only

#### Architecture Decisions
- Server role: ...
- Sync mechanism: ...
- Auth model: ...
- Encryption: ...

#### Requirements Check (F1-F12)
| F1 E2EE | F2 Offline | F3 Multi-Device | F4 Multi-User | F5 Consistency | F6 CRDT-agnostic | F7 Decentralized | F8 Membership | F9 Recovery | F10 Versioning |
|---------|-----------|----------------|--------------|---------------|-----------------|-----------------|-------------|------------|-------------|
| ✅/❌/➖  | ...       | ...            | ...          | ...           | ...             | ...             | ...         | ...        | ...         |

#### Usable for Us?
- **Directly adoptable:** ...
- **Modules usable:** ...
- **Inspiration:** ...
- **Blockers:** ...

#### Key Insights
- ...
```

---

### Beelay (Ink & Switch / Automerge Team)

**Type:** Protocol + Library
**License:** MIT
**Language:** Rust + WASM
**Maturity:** Alpha (prototype, not production-ready)
**Usable as:** Individual modules (RIBLT, Sedimentree) or whole protocol
**Profile status:** Preliminary (based on conference talk only). Deep-dive needed: `beelay/docs/protocol.md`, `beelay/docs/sedimentree.md`, `beelay-core` API.

#### Architecture Decisions

- **Server role:** Encrypted blob store. Server stores and serves content-addressed encrypted chunks. No CRDT logic on server.
- **Sync mechanism:** Two-layer sync. Layer 1: Auth graph via RIBLT (set reconciliation). Layer 2: Document commit graphs via Sedimentree (deterministic chunking). Data exchanged = 1.3-1.7x actual difference.
- **Auth model:** Via Keyhive (capability graph, CRDT-based). See Keyhive profile.
- **Encryption:** Per-chunk encryption. Chunk boundaries determined by leading zeros in hash. Each chunk contains key to previous chunk. One root key unlocks entire history.

#### Requirements Check (F1-F12)

| F1 E2EE | F2 Offline | F3 Multi-Device | F4 Multi-User | F5 Consistency | F6 CRDT-agnostic | F7 Decentralized | F8 Membership | F9 Recovery | F10 Versioning |
|---------|-----------|----------------|--------------|---------------|-----------------|-----------------|-------------|------------|-------------|
| ✅ | ✅ | ✅ | ✅ | ✅ | ✅ designed for it | ❌ single server assumed | ✅ via Keyhive | ➖ not addressed | ➖ not addressed |

#### Usable for Us?

- **Directly adoptable:** Not yet (alpha). But architecture is the clearest answer to our sync question.
- **Modules usable:** RIBLT (set reconciliation) is standalone. Sedimentree chunking is standalone. Both are Rust+WASM.
- **Inspiration:** The two-layer sync (auth graph first, then documents) is elegant. Document prioritization (sync what's in UI first). Deterministic chunking eliminates byzantine snapshot problem.
- **Blockers:** Alpha status. Automerge-centric prototypes (but core libs are CRDT-agnostic by design). No multi-server. Rust/WASM only (no pure TypeScript).

#### Key Insights

- "Anything shaped like a commit graph" — explicitly designed for more than just Automerge.
- The "airplane problem" as design driver: two peers who mostly agree should exchange only what's different.
- Server cannot compress E2EE data — this is THE fundamental problem that Sedimentree solves.
- For 1 million changes: only ~10 hashes needed to describe the chunk structure.
- Chunks themselves are a CRDT — no coordination needed for compression.

---

### Keyhive / BeeKEM (Ink & Switch)

**Type:** Protocol + Library
**License:** MIT
**Language:** Rust + WASM
**Maturity:** Alpha ("don't put it in production")
**Usable as:** Auth layer (independent of Beelay sync)
**Profile status:** Preliminary (based on conference talk only). Deep-dive needed: Notebook chapters 2-6, BeeKEM deep-dive (meri.garden), revocation mechanics, `keyhive_core` + `keyhive_wasm` API.

#### Architecture Decisions

- **Server role:** Untrusted. Server sees only encrypted blobs. Auth travels with the data (capabilities, not server middleware).
- **Sync mechanism:** Auth graph is itself a CRDT that gets synced. Membership changes are signed delegation chains.
- **Auth model:** Capability-based. Everything has a keypair (docs, users, devices, groups — no distinction). Signed delegation chains: Document → User → Device. Four levels: Pull → Read → Write → Admin.
- **Encryption:** Causal encryption — chunk boundaries from hash, key chaining between chunks. Group key agreement via BeeKEM (TreeKEM variant for CRDT concurrency).

#### Requirements Check (F1-F12)

| F1 E2EE | F2 Offline | F3 Multi-Device | F4 Multi-User | F5 Consistency | F6 CRDT-agnostic | F7 Decentralized | F8 Membership | F9 Recovery | F10 Versioning |
|---------|-----------|----------------|--------------|---------------|-----------------|-----------------|-------------|------------|-------------|
| ✅ | ✅ | ✅ devices = keypairs in graph | ✅ | ✅ auth graph is CRDT | ✅ generic design | ❌ not addressed | ✅ add/remove member API | ➖ not addressed | ➖ not addressed |

#### Usable for Us?

- **Directly adoptable:** Not yet (alpha, not audited). But the capability model is the best answer to our auth question.
- **Modules usable:** keyhive_core (Rust), keyhive_wasm (WASM+TS bindings). Could replace our GroupKeyService + manual key distribution.
- **Inspiration:** Keys never move — only certificates (delegations) are exchanged. This is fundamentally different from our current approach of sending Group Keys via ECIES. The "boring Google Docs share button" as API goal.
- **Blockers:** Alpha. No security audit. Complex (BeeKEM key agreement). Rust/WASM only.

#### Key Insights

- Auth must live BELOW the data layer in local-first (not above, like cloud middleware).
- No distinction between users, devices, groups, documents — all are keypairs with delegation chains.
- The entire API is: `addMember(key, role)` and `removeMember(key)`. Everything else follows from the graph.
- Scale target: 100k docs, 10k readers, 1k writers, 100 admins.
- Membership graph IS a CRDT — distributed, self-certifying, no coordinator.

---

### NextGraph (Niko Bonnieure)

**Type:** Protocol + Framework
**License:** MIT / Apache-2.0
**Language:** Rust (76%), TypeScript (14%), WASM
**Maturity:** Protocol ready, framework releasing 2025/26
**Usable as:** Whole protocol (if we adopt their ecosystem) or inspiration for broker/relay model
**Profile status:** Preliminary (based on conference workshop only). Deep-dive needed: protocol spec details, broker internals, overlay network mechanics, CRDT-agnostic implementation (AM+Yjs in same system), `nextgraph-rs` code.

#### Architecture Decisions

- **Server role:** "Broker" — encrypted store-and-forward. Not a CRDT peer. Two-tier network: Tier 1 = devices (plaintext), Tier 2 = brokers (ciphertext only). Brokers work with IP only, no domain names needed.
- **Sync mechanism:** DAG of encrypted commits. Each document has a permanent cryptographic ID (Nuri). CRDT operations synced via brokers. Separate from inbox messaging.
- **Auth model:** Cryptographic capabilities embedded in URIs (Nuri). Three stores: Private (self only), Protected (shared with permissions), Public (anonymous). Group stores for collaboration.
- **Encryption:** E2EE in transit + encrypted at rest. Cannot trust OS-level disk encryption.

#### Requirements Check (F1-F12)

| F1 E2EE | F2 Offline | F3 Multi-Device | F4 Multi-User | F5 Consistency | F6 CRDT-agnostic | F7 Decentralized | F8 Membership | F9 Recovery | F10 Versioning |
|---------|-----------|----------------|--------------|---------------|-----------------|-----------------|-------------|------------|-------------|
| ✅ transit + rest | ✅ | ✅ wallet syncs | ✅ via groups | ✅ | ✅ AM + Yjs + RDF | ✅ multi-broker | ✅ group members | ✅ 12-word mnemonic | ➖ not specified |

#### Usable for Us?

- **Directly adoptable:** Theoretically yes — closest to our vision. But: alpha, tiny community, single-point-of-knowledge (Niko), strong RDF commitment, no custom key import (wallet generates its own).
- **Modules usable:** Broker concept and inbox mechanism as architecture reference. Not as importable modules.
- **Inspiration:** Multi-broker with replication and failover. Three stores (private/protected/public) instead of one PersonalDoc. Inbox system for async messaging (pubkey-addressed, not DID-routed). Social queries (SPARQL through trust network). No DNS dependency.
- **Blockers:** Can't import our BIP39 identity. RDF/SPARQL commitment adds complexity we don't need. Single maintainer. Grant-dependent.

#### Key Insights

- "Not too decentralized" — pure P2P fails because of asynchronicity. Brokers solve availability.
- Inbox mechanism: pubkey-addressed mailbox on broker. Sender encrypts to inbox pubkey. Asynchronous. Elegant.
- Three stores solve the PersonalDoc problem: clear separation of private/shared/public data.
- Social queries: federated SPARQL through encrypted P2P data. Transitively trusted, anonymized on the way back.
- CRDT-agnostic in practice: same framework supports Automerge + Yjs + custom RDF CRDT.

---

### secsync / ORP (Nik Graf / serenity-kit)

**Type:** Protocol (secsync) + Library (ORP)
**License:** Apache-2.0 (secsync), MIT (ORP)
**Language:** TypeScript
**Maturity:** Beta (secsync, 439 commits), Early experimental (ORP, 6 commits)
**Usable as:** Architecture reference (secsync) / RIBLT module (ORP)
**Profile status:** Preliminary (based on conference talk + personal call). Deep-dive needed: secsync full specification (`secsync.com/docs/specification`), server architecture (`secsync.com/docs/server`), ORP `IMPLEMENTATION_PLAN.md`, RIBLT integration with Sedimentree.

#### Architecture Decisions

- **Server role:** Central relay + snapshot store. Server stores encrypted snapshots and OpLog. Client loads snapshot + recent ops at start.
- **Sync mechanism:** secsync: Snapshot + Updates + Ephemeral messages. XChaCha20-Poly1305 AEAD. Problem: byzantine snapshots with multi-device. ORP: Moving to RIBLT-based set reconciliation (inspired by Sedimentree). Solves the byzantine problem.
- **Auth model:** External. Invitation URLs with key in hash fragment (never sent to server). OPAQUE for password-based auth.
- **Encryption:** XChaCha20-Poly1305 (libsodium). Large nonces eliminate nonce-management problem in distributed systems.

#### Requirements Check (F1-F12)

| F1 E2EE | F2 Offline | F3 Multi-Device | F4 Multi-User | F5 Consistency | F6 CRDT-agnostic | F7 Decentralized | F8 Membership | F9 Recovery | F10 Versioning |
|---------|-----------|----------------|--------------|---------------|-----------------|-----------------|-------------|------------|-------------|
| ✅ | ✅ | ⚠️ byzantine problem (secsync) | ✅ | ✅ | ✅ Yjs + AM | ❌ central server | ⚠️ key rotation only | ➖ not addressed | ➖ not addressed |

#### Usable for Us?

- **Directly adoptable:** secsync: No (byzantine problem acknowledged by author). ORP: Not yet (6 commits).
- **Modules usable:** ORP's RIBLT implementation (TypeScript!) could be valuable — same algorithm as Beelay but in our language.
- **Inspiration:** The evolution secsync → ORP is a roadmap of what NOT to do and what TO do. Benchmarks (secsync.com/docs/benchmarks) are the reference for performance comparison. Invitation URLs for key exchange are elegant and simple.
- **Blockers:** secsync: known architectural limitation (byzantine snapshots). ORP: too early. Single maintainer (Nik, part-time).

#### Key Insights

- Nik's journey IS our learning: individual updates → snapshots → deterministic compression.
- "CRDTs and E2EE are a perfect match" — CRDTs guarantee same ops → same state regardless of order. Just encrypt the ops.
- XChaCha20 large nonces: no distributed counter needed. Random nonce, collision probability negligible.
- Key rotation (member removal) is where complexity explodes. Nik's advice: use existing frameworks if your use case fits.
- Vision: modular building blocks, not monolithic frameworks. Account management, trust establishment, key agreement as separate composable libraries.

---

## 6. Methodology

## 7. Next Steps

### Deep-Dive Guide

#### Goal

Determine whether we can adopt an existing sync protocol, combine building blocks from multiple projects, or need to design our own — and make that decision based on evidence, not assumptions.

#### The Central Question

**Must we build our own sync protocol, or does one exist that we can adopt?**

Three possible outcomes:

- **A) Adopt** — An existing protocol fits our requirements. We adopt it and build on top.
- **B) Combine** — No single protocol fits, but we can assemble building blocks (e.g. Sedimentree for compression + Nostr model for relays + Meadowcap for auth).
- **C) Build** — Nothing fits our combination of requirements. We specify our own protocol, inspired by the best ideas from the research.

#### Non-Negotiables

- **CRDT-agnostic specification** — The wot-spec protocol must not require a specific CRDT engine. It describes encrypted binary blobs.
- **Own identity** — BIP39 + Ed25519 + did:key, as specified in wot-spec/001. Not negotiable.
- **Compatible with our apps** — Web of Trust + Real Life Stack (TypeScript, React, Capacitor).

#### Negotiables

Everything else is open if it meets requirements F1-F12:

- **Encryption** — Our current AES-256-GCM works, but we'd adopt a better solution if one exists.
- **Sync protocol** — The core question of this research.
- **Relay/Server** — Own implementation or compatible with an existing protocol.
- **Key Management** — Our GroupKeyService or Keyhive/BeeKEM or MLS.
- **Compression** — Sedimentree or our own snapshot strategy.
- **CRDT engine** — Implementation may use a specific CRDT (e.g. Automerge for Beelay). We wrap it behind our adapter interface. The app doesn't know. If a better solution appears later, we swap the adapter.

Key distinction: **Implementation may be CRDT-specific. Specification must not be.**

#### What to Extract per Source

1. **Requirements fit** — F1-F12 checklist. Where does it match, where not, where conflict?
2. **Can we use it directly?** — Library we can import? Language? Maturity? License?
3. **Can we use parts of it?** — Standalone modules? (e.g. p2panda-encryption without p2panda-net, RIBLT without Beelay)
4. **Server/relay model** — What does the server store? How does routing work? Multi-server?
5. **What do they solve better than us?** — Where is their architecture superior?
6. **What don't they solve?** — Gaps we must fill ourselves.

#### Evaluation Criteria for "adopt vs. build"

Adopt when:
- Fulfills F1-F12
- CRDT-agnostic or adaptable behind our adapter interface
- Actively maintained, >1 maintainer
- License compatible (MIT/Apache)
- TypeScript or WASM usable
- Identity layer replaceable with our did:key

Build when:
- No existing project fulfills our combination of requirements
- But: informed and inspired by the best ideas from research

---

### Step 3: Deep-Dive All Remaining Sources

#### Federation & Transport (Cluster A)

- [ ] **Matrix** — Federation protocol, DAG events, room distribution across homeservers
- [ ] **Nostr** — Client-centric relay model, NIP-01, no inter-relay routing
- [ ] **p2panda** — Topic-based replication, confidential discovery, gossip protocol, namakemono spec
- [ ] **Automerge Sync Server** — CRDT peer as server, state vector exchange, Beelay protocol spec
- [ ] **DXOS/ECHO** — HALO identity, device invitation, MESH P2P transport
- [ ] **Noosphere** — Content-addressable, UCAN auth, decentralized name resolution (wound down, protocol open)
- [ ] **Willow Protocol** — Complete spec family: Data Model, Meadowcap, Confidential Sync, Drop Format, 3D RBSR
- [ ] **Iroh** (n0-computer) — QUIC networking, transport-agnostic sync layer
- [ ] **DIDComm** — DID-native messaging spec, mediator pattern
- [ ] **Subduction** (Ink & Switch) — Encrypted P2P sync protocol on Sedimentree

#### Sync & Encryption (Cluster B)

- [ ] **ORP** — RIBLT implementation details, IMPLEMENTATION_PLAN.md, demo code
- [ ] **Sedimentree** — Full design doc deep-dive, Beelay sedimentree.md, stratum mechanics
- [ ] **Keyhive/BeeKEM** — Capability graph internals, BeeKEM key agreement, revocation, notebook chapters 2-6
- [ ] **Loro Protocol** — Native E2EE in wire protocol (`%ELO` prefix), Yjs interop
- [ ] **Jazz** — CoJSON, groups with permissions, sync engine architecture
- [ ] **Ossa Protocol** — DHT + BFT + E2EE CRDTs, decentralized lookup

#### Research Articles

- [ ] **Serkour: CRDT + E2EE Research Notes** — Compares Keyhive vs. MLS vs. Hybrid approach
- [ ] **RIBLT Paper** (ACM SIGCOMM 2024) — Rateless Invertible Bloom Lookup Tables
- [ ] **ConflictSync Paper** (2025) — CRDT + RIBLT combined
- [ ] **CertainSync Paper** (2025) — Rateless set reconciliation with certainty
- [ ] **"Local-first software" Paper** (Kleppmann et al. 2019) — Foundational
- [ ] **"Synchronizing Semantic Stores with CRDTs"** (Ibáñez, Skaf-Molli, Molli, Corby — INRIA 2012) — [PDF](https://inria.hal.science/hal-00686484/document) — Commutative operations on RDF triples, theoretical basis for NextGraph's Graph-CRDT. Relevant for modeling WoT trust graph as CRDT.

#### Talks (Local-First Conf + Sync Conf)

- [ ] **Kevin Jahns — CRDT performance tradeoffs** — Yjs author on performance
- [ ] **Andrei Popa — Practical local-first permissions** — Membership/auth patterns
- [ ] **Brendan O'Brien — Can sync be transport agnostic?** — Transport layer design (iroh/n0)
- [ ] **Johannes Schickling — Event sourcing in local-first** — Alternative to CRDT sync
- [ ] **Timo Wilhelm — Yjs sync via Cloudflare Workers** — Alternative relay architecture
- [ ] **Aaron Boodman — General-purpose sync with IVM** — Sync engine architecture
- [ ] **Anselm Eickhoff (Jazz) — Sync engine → database** — CoJSON, groups, E2EE planned
- [ ] **Martin Kleppmann — Past, present, future of local-first** — Strategic overview
- [ ] **Peter Van Hardenberg — Local First: secret master plan** — Ink & Switch roadmap

### Step 4: Synthesize

- [ ] Create comparison matrix across ALL sources (extend section 4.2)
- [ ] Identify patterns and anti-patterns
- [ ] Formulate architecture proposal for WoT sync & transport
- [ ] Map proposal to our requirements (F1-F12)

### Step 5: Review & Refine

- [ ] Review with Sebastian — align with Rust implementation perspective
- [ ] Adversarial design — try to break the proposal
- [ ] Identify the 2-3 most open questions for prototyping

### Step 6: Specify

- [ ] Draft `wot-spec/spec/005-transport.md` (server role, federation, message delivery)
- [ ] Draft `wot-spec/spec/006-sync.md` (sync protocol, reconciliation, compression)

---

*This document is a living research artifact. It will evolve as we explore the design space.*
