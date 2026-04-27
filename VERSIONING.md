# Versionierung

Dieses Repository versioniert die Web-of-Trust-Spezifikation als nachvollziehbare Release-Snapshots. Die Dokumentnummern `001`, `002`, usw. sind stabile Dokumentnamen, keine Versionsnummern.

## Ebenen

### Repository-Releases

Git-Tags und GitHub Releases markieren eingefrorene Snapshots der gesamten Spec:

- `v0.1.0-draft` - erster oeffentlicher Draft-Snapshot
- `v0.2.0-interop` - erster Snapshot mit bestandenen TypeScript/Rust-Interop-Tests
- `v0.3.0-sync` - erster Snapshot mit minimalem Broker/Personal-Doc-Sync
- `v1.0.0-identity-trust` - stabiler Identity-/Trust-Snapshot nach Interop zwischen mindestens zwei Implementierungen

Vor `v1.0.0` sind Breaking Changes erlaubt. Sie MUESSEN im `CHANGELOG.md` dokumentiert werden.

Ab `v1.0.0` gilt SemVer:

- MAJOR: Breaking Changes an normativen Formaten oder Conformance-Anforderungen
- MINOR: Rueckwaertskompatible neue Features, Profile, Schemas oder Testvektoren
- PATCH: Klarstellungen, redaktionelle Fixes, zusaetzliche nicht-brechende Tests

### Spec-Profile

Implementierungen geben an, welche Profile sie unterstuetzen:

| Profil | Bedeutung |
|---|---|
| `wot-identity@0.1` | Identitaet, Key-Derivation, Signaturen, JWS/JCS, DID-Resolution |
| `wot-trust@0.1` | Attestations, Verification-Attestations, QR-/Nonce-Verifikation |
| `wot-sync@0.1` | Verschluesselung, Append-only Log, Broker, Discovery, Gruppen, Personal Doc |
| `wot-rls@0.1` | Real-Life-Stack-spezifische Erweiterungen |
| `wot-hmc@0.1` | Human-Money-Core-spezifische Erweiterungen |

Ein Profil ist nur dann implementiert, wenn die Anforderungen in `CONFORMANCE.md` fuer dieses Profil erfuellt sind.

### Wire- und Schema-Versionen

Nachrichtenformate und Vocabularies tragen eigene Wire-Versionen. Diese Versionen bleiben in den Nachrichten selbst sichtbar:

- Type-URIs: `https://web-of-trust.de/protocols/log-entry/1.0`
- VC Contexts: `https://web-of-trust.de/vocab/v1`
- SD-JWT VC Types: `.../TrustList/v1`

Wire-Versionen werden nur erhoeht, wenn sich das jeweilige konkrete Format aendert. Ein Repository-Release kann mehrere Wire-Versionen enthalten.

## Branches

`main` ist der laufende Draft. Er darf sich zwischen Releases aendern und ist nicht automatisch stabil.

Stabile Referenzen verwenden Git-Tags, nicht Branch-Namen.

## Normativ vs. Research

Normativ sind:

- `01-wot-identity/`
- `02-wot-trust/`
- `03-wot-sync/`
- `04-rls-extensions/`
- `05-hmc-extensions/`
- `test-vectors/`
- `CONFORMANCE.md`

Nicht normativ sind:

- `research/`
- offene Fragen in Dokumenten, die explizit als Zukunft oder Research markiert sind

## Release-Kriterien

Ein Release darf nur erstellt werden, wenn:

1. `CHANGELOG.md` einen Eintrag fuer die Release-Version enthaelt.
2. `CONFORMANCE.md` den erwarteten Konformitaetsumfang beschreibt.
3. Die vorhandenen Testvektoren in `test-vectors/` aktuell sind.
4. Breaking Changes seit dem letzten Release explizit benannt sind.

## Breaking Changes

Als Breaking Change gelten insbesondere:

- Aenderung von HKDF-Info-Strings oder Key-Derivation
- Aenderung von JWS-Headern, Pflichtfeldern oder Signatur-Inputs
- Aenderung von DID-Resolution-Anforderungen
- Aenderung von AES-GCM-Nonce-Konstruktion oder Blob-Format
- Aenderung von Capability-, Log-Entry-, Attestation- oder Trust-List-Formaten
- Verschaerfung von `MUSS`-Anforderungen, die bestehende konforme Implementierungen brechen

Klarstellungen ohne Format- oder Verhaltensaenderung sind keine Breaking Changes.
