# Web of Trust Protocol Specification

An open, implementation-independent specification for a decentralized Web of Trust — identity, attestation, and trust propagation based on real-world encounters.

## Goal

Define a modular protocol that enables:

- **Decentralized Identity** — Self-sovereign, based on established cryptographic standards (BIP39, Ed25519, did:key)
- **Attestation** — Signed claims based on real-world encounters (Proof of Personhood)
- **Trust Propagation** — Graph-based trust with decay, multipath, and configurable thresholds
- **Privacy** — Blinded keys, selective disclosure
- **Interoperability** — Multiple implementations in different languages can interoperate

## Implementations

This specification is currently informed by two independent implementations:

- [Web of Trust Core](https://github.com/real-life-org/web-of-trust) — TypeScript, Web Crypto API
- [Human Money Core](https://github.com/minutogit/human-money-core) — Rust, Ed25519 (dalek)

The spec is not tied to either implementation.

## Structure

    spec/             Specification documents
    rfcs/             Proposals for spec changes (RFC process)
    rfcs/template.md  RFC template

## RFC Process

Changes to the specification are proposed through RFCs (Request for Comments). The process follows the consent principle: a proposal is accepted unless there is a substantiated objection.

See [rfcs/template.md](rfcs/template.md) for the template.

## Contributing

This is an open specification. Contributions are welcome from anyone building decentralized trust systems. Open an issue or submit an RFC.

## License

This specification is licensed under [CC-BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).
