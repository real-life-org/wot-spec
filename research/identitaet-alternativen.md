# Identitäts-Alternativen — Exploration

> **Nicht normativ:** Dieses Dokument ist Hintergrund, Analyse oder Planung. Normative Anforderungen stehen in den Spec-Dokumenten und in `CONFORMANCE.md`.

- **Status:** Exploration (keine normative Entscheidung)
- **Autoren:** Anton Tranelis
- **Datum:** 2026-04-19

## Zweck dieses Dokuments

Wir sammeln hier Alternativen und Ideen zum Thema **User-Identität, Seed-Management, Authentifizierung und Recovery**. Ziel ist keine Entscheidung, sondern eine strukturierte Übersicht der Design-Räume, die andere Projekte geöffnet haben und aus denen wir lernen können.

Die Grundfrage: **Müssen wir bei 12-Wörter-BIP39-Mnemonics bleiben, oder gibt es bessere Muster für unseren Use Case?**

## Ausgangspunkt: Was wir aktuell haben

Siehe [Core 001](../01-wot-core/001-identitaet-und-schluesselableitung.md) für die aktuelle Spec.

```
BIP39 Mnemonic (12+ Wörter)
  → PBKDF2-HMAC-SHA512 (2048 Runden)
  → 64-Byte Seed
  → HKDF-SHA256(seed, info="wot/identity/ed25519/v1")
  → 32-Byte Ed25519-Seed
  → Ed25519-Keypair → did:key
```

Der Seed wird auf dem Gerät verschlüsselt gespeichert (passphrase-basiert). User schreibt die 12 Wörter auf Papier als Cold-Backup.

## Die Kritik — warum 12 Wörter UX-problematisch sind

**Regelmäßig geäußert:**

- Zu lang zum Merken — muss aufgeschrieben werden
- Aufschreiben auf Papier ist unmodern, unvertraut, verlierbar
- Wer das Papier verliert und keinen Zugriff aufs Gerät hat, verliert die Identität
- "12 zufällige Wörter" wirken auf viele wie Crypto-Jargon, hohe Abschreckungs-Schwelle
- Unterschiedliche Wortlisten (englisch vs. deutsch vs. Custom) erzeugen Verwirrung und Interop-Probleme

**Messbar in der Praxis:** Bei Web-of-Trust-Onboarding bricht ein nennenswerter Anteil der User an der "12 Wörter aufschreiben"-Hürde ab.

## Alternative Muster in der Landschaft

### 1. NextGraph — Pazzle + Wallet-File

**Niko Bonnieure**, [nextgraph.org](https://nextgraph.org)

- **"Wallet"**: lokal beim ersten App-Start erzeugter Identitäts-Container, ohne Server-Call
- **"Pazzle"**: System generiert 9 Bilder zufällig, User merkt sich die **Reihenfolge** — ein visuell memorierbarer Login
- **Rationale**: "User wählen unsichere Passwörter, also lassen wir sie gar nicht wählen. Wir tauschen user-gewählte Entropie gegen system-gewählte, visuell memorierbare Entropie."
- **BIP39-Mnemonic als Backup** — nicht abgeschafft, nur aus der Default-UX rausgenommen
- **Device-Transfer**: QR-Code, TextCode (über Messenger), USB-Stick
- **Durable Backup**: Print-to-Paper-PDF
- **Kein Social Recovery dokumentiert**
- **Wallet-Format-Spec ist "TBD"** — formale Kryptografie noch nicht publiziert

Quellen: [docs.nextgraph.org/en/wallet](https://docs.nextgraph.org/en/wallet/)

### 2. CryptPad — Username + Passwort + Login-Block

[cryptpad.org](https://cryptpad.org), XWiki SAS

- **Anonymous by default**: Drive funktioniert ohne Account
- **"Account" = username + password**, beides selbst-gewählt
- **KDF**: `scrypt(password, username+salt, N=2⁵⁶, r=1024, p=1, dkLen=128)`
- **Login-Block-Indirektion** (das elegante Kernkonzept):
  - Passwort + Username → scrypt → 192 deterministische Bytes
  - Davon: ed25519-Block-Keypair + symmetrischer Block-Key
  - Block-URL auf Server = Ed25519-Public-Key des Blocks
  - Client signiert HTTP-Challenge mit Block-Privkey → Server liefert verschlüsselten Blob
  - Blob enthält die **eigentliche, langlebige Identität** (Drive-Keys, Ed25519-Keypair)
- **Passwort identifiziert nur zum Server** — die echte Identität ist separat
- **Passwort-Wechsel**: neuer Block, langlebige Identität bleibt erhalten, via "Ancestor-Proof" (alter Privkey signiert neuen Pubkey)
- **Read/Write-Key-Derivation**: editKey (zufällig) + password → SHA-512 → hash[0:32] = Write-Signing-Seed, hash[32:64] = viewKey (Read-Capability). Asymmetrisch: Write impliziert Read, aber nicht umgekehrt.
- **Kein Recovery** bei vergessenem Passwort — Datenverlust final
- **Minimum 8 Zeichen Passwort**, keine Entropie-Prüfung (zxcvbn nicht im Codebase)
- **Plausible Deniability**: Server kennt weder Username noch Hash — nur Block-URL, die scheinbar zufällig aussieht

Quellen: CryptPad Source (`src/common/common-credential.js`, `src/common/outer/login-block.js`), [Whitepaper](https://blog.cryptpad.org/images/whitepaper.pdf)

### 3. Argent — Social Recovery via Guardians

[argent.xyz](https://argent.xyz), Ethereum Smart Wallet

- **Keine Seed-Phrase** im UX
- **Smart Contract** auf Ethereum hält Keys
- **Guardians**: User wählt vertraute Personen, andere Wallets oder Argent-2FA-Service als Guardians (typisch 3-7)
- **Recovery**: ≥ Hälfte der Guardians + 48h Security-Delay → neuer Signing-Key autorisiert
- **Day-to-day**: Passwort / Biometrie auf dem Gerät
- **Tradeoffs**: Ethereum-Abhängigkeit, Gas-Kosten, On-Chain-Footprint
- **Nicht direkt übertragbar** auf nicht-Blockchain-Systeme — aber das **Konzept** (M-von-N Guardians aus Trust-Graph) ist portabel

Quellen: [Argent Recovery](https://support.argent.xyz/hc/en-us/articles/360007338877), [Vitalik: Social Recovery Wallets](https://vitalik.eth.limo/general/2021/01/11/recovery.html)

### 4. Jazz — Passkeys + Mnemonic-Fallback

[jazz.tools](https://jazz.tools), Garden Computing

- **Passkey (WebAuthn)** als Default — FaceID/TouchID/Hardware-Key vom OS verwaltet
- **Passphrase (BIP39-like)** als Fallback für Serverless-Betrieb
- **Local-First Anonymous Account** bei erstem Visit, später "upgradable" zu vollem Account
- **Tradeoff**: Passkey-Recovery liegt beim Platform-Vendor (Apple/Google iCloud Keychain)

Quellen: [jazz.tools auth docs](https://jazz.tools/docs/react/key-features/authentication/overview)

### 5. Soul Wallet / Safe / ERC-4337 — Passkey + Guardian-Hybrid

- **Account Abstraction** auf Ethereum (ERC-4337)
- **Passkey als Signing-Key** für day-to-day
- **Guardian-Recovery** als Recovery-Pfad
- **Session Keys** für limitierte Permissions
- **Keine Mnemonics** im UX

Quellen: [Soul Wallet](https://www.soulwallet.io), [passkeys-4337 smart-wallet](https://github.com/passkeys-4337/smart-wallet)

### 6. Signal — Phone Number als Identitäts-Anker

- **Telefonnummer** = Identität
- **PIN + SVR** für Message-History-Recovery
- **UX-Benchmark**: Onboarding in Sekunden, keine kryptographischen Artefakte
- **Tradeoff**: Zentrale Abhängigkeit (Mobilfunk-Provider, SIM-Swap-Angriffe)
- **Nicht unser Modell** (wir wollen zentrale Abhängigkeiten vermeiden), aber relevanter UX-Referenzpunkt

### 7. Passkeys / WebAuthn — als Primitive

- **Kein Identity-System** für sich, sondern ein Authenticator
- **Platform-Sync via iCloud Keychain / Google Password Manager**
- **Recovery wird implizit an Apple/Google delegiert** — konfliktär mit Souveränitäts-Anspruch
- **Interessant als Layer**, nicht als Root

### 8. Keyhive / Beelay — Multi-Device Key Agreement

Ink & Switch Research, pre-alpha

- **Ed25519/X25519 per-device Identitäten**
- **Gruppenmitgliedschaft via Delegations-Ketten**
- **Multi-Device-Sync** ohne trusted Intermediaries
- **Keine publizierte User-Recovery-Story** — Identitäts-Recovery ist "füge neues Device hinzu bevor du das letzte verlierst"
- **Interessant als Backend-Primitive**, nicht als User-Story

Quellen: [Keyhive](https://www.inkandswitch.com/project/keyhive/)

### 9. Standard Notes, Bitwarden, Tutanota — Password-KDF-Systeme

- **Standard Notes**: PBKDF2-SHA512 → Argon2id, getrennter `masterKey` und `serverPassword`
- **Bitwarden**: PBKDF2-SHA256 (600k) oder Argon2id, master-key als Indirektions-Schicht
- **Tutanota**: Argon2id seit 2023, `authVerifier` + `userPassphraseKey`
- **Gemeinsam**: Passwort → starker KDF → Master-Key, der separaten Daten-Key entschlüsselt
- **Alle haben Recovery-Optionen** (Emergency-Codes, E-Mail-Recovery, etc.)

## Techniken, die wir adaptieren könnten

### A. Login-Block-Indirektion (von CryptPad)

**Das mit Abstand wertvollste Muster**, das wir im Research gefunden haben.

**Kern-Idee:** Entkoppele "was identifiziert mich zum Server" von "was verschlüsselt meine Daten". Erste Ebene ist rotierbar (Passwort-Wechsel, 2FA), zweite Ebene ist langlebig (Identitäts-Keypair, DID).

**Für uns:**

```
Ebene 1 (Day-to-Day):
  Passwort (user-gewählt) + Username
    → Argon2id (OWASP-2024-Parameter)
    → Block-Key

Ebene 2 (langlebig):
  Block-Key entschlüsselt lokalen Block
    → Block enthält BIP39-Seed (oder abgeleitetes Ed25519-Material)
    → Ed25519-Identität → did:key (DID bleibt stabil bei Passwort-Wechsel)
```

Passwort vergessen? → Fallback zu BIP39-Mnemonic auf Papier → Block neu erzeugen
Gerät verloren? → Anderes Gerät + Passwort oder Mnemonic → gleiche DID

### B. Read/Write-Key-Derivation via SHA-512 (von CryptPad)

Direkt auf Space-Capabilities übertragbar:

```
editKey (18 zufällige Bytes)
  → SHA-512
  → hash[0:32]  = ed25519-Signing-Seed (Write-Capability)
  → hash[32:64] = viewKey (Read-Capability)
```

Wer editKey hat, kann daraus deterministisch viewKey ableiten. Wer nur viewKey hat, kann nicht auf editKey zurückrechnen (SHA-512 ist Einweg). **Asymmetrische Capability ohne Server-Roundtrip.**

Für Space-Invitation-Links könnten wir genau das machen: Invite-Link enthält entweder editKey (Member) oder viewKey (Read-Only Viewer).

### C. Ancestor-Proof für Key-Rotation (von CryptPad)

Beim Schlüssel-Rotieren signiert der alte Private Key den neuen Public Key:

```
oldSignature = Ed25519.sign(oldPrivKey, newPubKey)
```

Server / Peers können kryptographisch verifizieren, dass die Rotation autorisiert ist — ohne selbst irgendeinen Schlüssel zu kennen.

Passt zu unserem **Guardian-Based Recovery** (zukünftig) und zu **Device-Revokation** (M6).

### D. Pazzle als Unlock-Mechanism (von NextGraph)

**Nicht als Root-Secret**, sondern als **Unlock für einen lokalen verschlüsselten Container**.

Für uns denkbar: User bekommt bei Setup 9 zufällige Bilder, merkt sich die Reihenfolge als narrative Mnemotechnik ("rote Blume, dann blauer Berg, dann ..."). Diese Reihenfolge entsperrt den lokalen Wallet-Container auf dem Gerät. Der Container enthält die echte Identität (Ed25519-Keypair oder BIP39-Seed).

**UX-Vorteil**: visuell memorierbar, kein Tippen
**Tradeoff**: funktioniert nur in der eigenen App (nicht portierbar wie BIP39)

### E. Guardian-Vouching über den WoT-Graph

**Unser strukturelles Alleinstellungsmerkmal**: Wir haben verifizierte Kontakte. Das ist die Infrastruktur, aus der Guardian-Vouching natürlich wächst — ohne artifiziellen Setup-Aufwand wie bei Argent.

**Grundidee (aus NLnet-Bewerbung, WP2):** User, der den Zugriff auf seinen primären Key verliert oder den Key rotieren will, erzeugt einen neuen Key. Eine konfigurierbare Anzahl verifizierter Kontakte (z.B. 3-von-5) bestätigt die Identitätskontinuität durch signierte Vouching-Attestations.

**Konzept:**

```
Bei Identitäts-Setup:
  User wählt n verifizierte Kontakte als Guardians (z.B. 5)
  Threshold wird gesetzt (z.B. 3)
  Nichts Geheimes wird verteilt — keine Shares, keine Shamir-Kryptographie
  Die Guardian-Liste wird im DID-Document (bei did:peer:4) oder in
    einer signierten Attestation (bei did:key) publiziert

Bei Recovery oder Key-Rotation:
  User generiert neues Keypair
  User kontaktiert Guardians (persönlich, per Video-Call, via verifiziertem Kanal)
  Jeder Guardian verifiziert: "Bist du wirklich Alice?" (out-of-band)
  Guardian signiert eine Vouching-Attestation

  Bei did:peer:4: DID-Document-Update wird vom Guardian-Quorum co-signiert
                  (neuer Key wird registriert, alter revoziert, DID bleibt)
  Bei did:key:    Equivalence-Proof wird vom Guardian-Quorum signiert
                  (alte DID → neue DID Migration)

  Wenn Threshold erreicht: Rotation/Migration wird netzwerkweit wirksam
  Kontakte der betroffenen Identität propagieren den Übergang über DIDComm
```

**Vorteile gegenüber Shamir-Secret-Sharing:**

- Viel einfacher zu implementieren — nur Ed25519-Signaturen, keine Threshold-Kryptographie
- Nutzt exakt die Primitive, die wir schon haben (signierte Attestations)
- Kein Risiko, dass kompromittierte Shares den alten Seed offenlegen
- Funktioniert symmetrisch für Verlust UND Kompromittierung (in beiden Fällen neuer Key, Guardians bestätigen)
- Kein Setup-Aufwand für Guardians — sie sind automatisch die Personen, mit denen der User bereits verifiziert ist
- Guardians können ihre Rolle jederzeit ablehnen, ohne dass sofort Daten migriert werden müssen

**Zusammenspiel mit Ansatz A (did:peer:4):**

Bei did:peer:4 fügt sich Guardian-Vouching besonders sauber ein. Guardians signieren nicht einen Equivalence-Proof zwischen zwei DIDs, sondern ein **DID-Document-Update**, das:

- Den neuen Master-Key als `verificationMethod` hinzufügt
- Den alten Master-Key mit `revokedAt`-Timestamp markiert
- Guardian-Quorum als `proof` trägt

Das hat strukturelle Vorteile: **die DID bleibt stabil**, Keys rotieren, externe Referenzen bleiben gültig. Die NLnet-Bewerbung formuliert den Mechanismus unter der did:key-Annahme ("user creates new DID"), wo Rotation zwangsläufig DID-Wechsel bedeutet. Bei did:peer:4 entfällt dieser Zwang.

**Angriffsszenarien und Mitigationen:**

- **Angreifer hat kompromittierten Key, will Migration selbst triggern, um den User auszusperren** → Guardian-Vouching erfordert Out-of-Band-Verifikation (persönlich, per Video). Angreifer kann die Guardians nicht alle täuschen.
- **Angreifer kompromittiert mehrere Guardian-Accounts** → Threshold-Schutz und die Tatsache, dass Guardians Hauptkontakte des Users sind, machen das schwer. Plus: User kann bei Verdacht proaktiv Guardians wechseln.
- **Social Engineering einzelner Guardians** → Out-of-Band-Verifikation als Pflicht macht einzelne Angriffe wirkungslos, solange der Threshold nicht erreicht wird.

NextGraph forkt `threshold_crypto` — für Vouching brauchen wir das nicht, aber eventuelles Kollaborations-Feld wenn wir später Advanced-Features wollen.

### F. Web5 HdIdentityVault als Referenz-Implementation (von Web5/DIF)

Web5 (TBD, jetzt DIF) hat mit dem `HdIdentityVault` eine **produktionsreife Implementation** genau des Hybrid-Modells gebaut, das wir hier diskutieren. Der Code liegt in `packages/agent/src/hd-identity-vault.ts` im Repo [decentralized-identity/web5-js](https://github.com/decentralized-identity/web5-js), MIT-Lizenz.

**Was der Code macht:**

```
Mnemonic (BIP39, englisch, 12 Wörter)
  → PBKDF2 → Root Seed (64 Bytes)
  → SLIP-0010 HD-Derivation (ed25519-keygen/hdkey)
  → Deterministisch abgeleitete Keys über BIP44-Pfade:
    • m/44'/0'/0'/0'/0'           → Vault HD Key (für CEK-Ableitung)
    • m/44'/0'/{timestamp}'/0'/0' → Identity Key (DID-Kontrolle)
    • m/44'/0'/{timestamp}'/0'/1' → Signing Key (Day-to-Day)

Vault CEK (Content Encryption Key, 32 Bytes)
  ← HKDF-512(Vault-Privkey, info: "vault_cek")

Vault-Inhalt (portable DID + Keys)
  ← verschlüsselt mit CEK (AES-256-GCM)
  ← als Compact JWE gespeichert

Password wrappt CEK
  ← JWE mit alg: PBES2-HS512+A256KW
  ← Salt = HKDF-512(Vault-Pubkey, info: "vault_unlock_salt")
```

**Was davon wir adaptieren sollten:**

1. **Das Login-Block-Pattern komplett** — exakt die Architektur aus unserem Hybrid-Vorschlag, aber production-tested. Wir sollten den Code als Referenz lesen beim Implementieren.

2. **Deterministische Salt-Ableitung aus Public Key** — eleganter als eigener Salt-Speicher. Der Salt ist public, kann aber ohne den Public Key nicht reproduziert werden.

3. **JWE mit PBES2-HS512+A256KW** — standard-konformes Format für passwort-gewrapptes Content-Encryption-Key. Interoperabel mit JOSE-Ökosystem.

4. **Getrennte Keys für Identity und Signing** — Identity-Key kontrolliert das DID-Document, Signing-Key macht Day-to-Day-VCs. Gute Separation of Concerns.

5. **SLIP-0010 via `ed25519-keygen/hdkey`** — wenn wir Sebastians SLIP-0010-Vorschlag akzeptieren, ist diese Library der naheliegende Baustein (TypeScript-Implementation, die Web5 bereits produktiv nutzt).

**Was wir NICHT übernehmen:**

- **Fehlendes Guardian-Recovery** — Web5 hat nur Mnemonic als Backup. Unser NLnet-WP2-Guardian-Vouching ist ein echter Mehrwert, der fehlt.
- **Englisch-only BIP39** — Web5 nutzt ausschließlich die englische Standard-Wortliste. Wir werden das wahrscheinlich ähnlich halten, aber ohne das ausdrücklich zu übernehmen.
- **Statisches Passwort** für CEK-Unwrap ohne Passkey-Alternative — Web5 hat keinen Passkey-Unlock-Pfad via PRF-Extension. Den können wir zusätzlich einbauen.

**Konkrete Implementation-Empfehlung:**

Wenn wir den Login-Block-Teil umsetzen, sollten wir **den Web5-Code direkt studieren** und als Referenz nehmen. Die Architektur-Entscheidungen sind dort bereits getroffen, das Password-Wrapping-Format (JWE mit PBES2) ist standard-konform, die Edge-Cases sind produktiv durchdacht. Das spart uns Wochen eigener Design-Arbeit.

Pfad zum Code: `/tmp/web5-js/packages/agent/src/hd-identity-vault.ts` (lokal geklont, ~800 Zeilen, gut lesbar).

## Primäre Key-Rotation — die strukturelle Frage

**Status: Bisherige Präferenz für Ansatz A (did:peer:4). Noch keine endgültige Entscheidung.**

### Das Problem

Unabhängig von Unlock-Mechanismen (Passwort, Passkey, Pazzle) und Backup-Pfaden (Mnemonic, Guardian-Recovery) bleibt eine strukturelle Schwachstelle im aktuellen Design: **der primäre Key kann nicht rotiert werden.**

Zwei Szenarien, die das konkret macht:

1. **Privkey-Kompromittierung:** Jemand hat Zugriff auf den Ed25519-Privkey bekommen (Seed-Leak, Hardware-Kompromittierung, Phishing). Im aktuellen Modell ist die DID damit für immer verbrannt. Neue DID = neue Identität, alle Attestations, Trust-Beziehungen, Mitgliedschaften sind weg.

2. **Privkey-Verlust ohne Kompromittierung:** User hat keinen Zugriff mehr auf den Key (kein Device, kein Mnemonic, kein Passwort), aber der Key ist auch nicht in feindlichen Händen. Ohne Guardian-Recovery = neue DID, selbes Problem.

Die Recovery-Mechanismen (Mnemonic, Guardian-Shamir) bringen den User auf **denselben** primären Key zurück. Bei Kompromittierung ist das genau der falsche Ausgang.

### Warum did:key das strukturell ausschließt

did:key kodiert den Public Key direkt in die DID:

```
did:key:z6MkhaXgBZDvotDkL5257faiztiGiC2QtKLGpbnnEGta2doK
         └─── Base58btc(0xed01 || ed25519_pubkey) ────┘
```

Key rotieren = Pubkey ändern = DID ändern. **Es gibt keinen "Identity Anchor", der stabil bleibt, während der Key rotiert** — der Key *ist* der Anchor.

### Drei strukturelle Optionen

**Ansatz A: DID-Methode wechseln — konkret did:peer:4**

Die DID wird zu einem stabilen Identifier, das DID-Document enthält Keys als Attribute. Keys können rotiert werden, die DID bleibt.

did:peer:4 bietet:
- Stabile DID (Hash des initialen Documents)
- Multi-Key-Support im DID-Document (Master + Device + Passkey + Encryption)
- Updates via signierte Update-Attestations
- Kein Server, keine Domain, kein Ledger — Distribution P2P-kompatibel

**Was damit funktioniert:**
- Privkey kompromittiert → Guardian-Quorum signiert Update-Attestation, revoziert kompromittierten Key, aktiviert neuen Key. DID bleibt.
- Privkey verloren → Guardian-Quorum autorisiert neuen Key. DID bleibt.
- Device-Kompromittierung → Master signiert Update-Attestation. DID bleibt.
- Passwort/Passkey-Wechsel → nicht im DID-Document, nur lokaler Unlock-Container.

**Was wir dafür bauen müssten:**
- DID-Document-Publishing-Infrastruktur (wot-profiles-Service eignet sich konzeptionell, muss erweitert werden)
- DID-Document-Resolving in allen Clients
- Update-Attestation-Protokoll mit klaren Rollen (wer darf was signieren)
- Versioning im DID-Document (Clients müssen aktuelle Version erkennen, veraltete ablehnen)

**Ansatz B: DID-Migration via Equivalence Proofs**

did:key bleibt. Rotation = neue DID erzeugen. Ein formalisiertes Migrations-Protokoll überträgt den Kontext (Trust-Attestations, Mitgliedschaften) auf die neue DID.

**Flow bei Kompromittierung:**

```
1. User erzeugt neue DID (neuer Seed, neuer Ed25519-Keypair)
2. Migration-Attestation wird erstellt:
   - Signiert von 3-von-5 Guardians (Quorum)
   - Inhalt: "did:key:...old migriert zu did:key:...new"
   - Optional Time-Lock (z.B. 7 Tage Widerrufsfrist)
3. Migration wird über Inbox an alle Kontakte verteilt
4. Kontakte aktualisieren ihre Trust-Attestations, Mitgliedschaften auf neue DID
5. Alte DID gilt nach Migration als "retired" — Signaturen werden ignoriert
```

**Was damit funktioniert:**
- Kompromittierung mit Guardian-Quorum → saubere Migration
- Verlust mit Guardian-Recovery → Guardians autorisieren Migration zu neuer DID
- Externe Referenzen werden "stale", aber ein Resolver-Protokoll könnte Migrations-Ketten verfolgen

**Was wir dafür bauen müssten:**
- Migration-Attestation-Format (neuer Signatur-Typ in Core 003)
- Guardian-Quorum-Protokoll
- Time-Lock-Mechanismus gegen Race-Conditions mit Angreifer
- Migration-Propagation über DIDComm-Inbox
- Update-Logik in allen Kontakt-Apps

**Ansatz C: did:dht — Multi-Key-DID über BitTorrent Mainline DHT**

Dritte Option, sichtbar geworden durch die Web5-Recherche (20.04.2026). did:dht wurde von TBD für Web5 entwickelt, ist jetzt bei DIF, und nutzt die bestehende BitTorrent Mainline DHT (~20 Mio. Nodes weltweit) als Publishing-Infrastruktur für DID-Documents via BEP44.

**Konzept:**
- DID-Document wird im Mainline-DHT unter einer Schlüssel-abgeleiteten Adresse publiziert
- Updates via BEP44 (signierte, versionierte Records)
- Multi-Key-Support im DID-Document (wie bei did:peer:4)
- Resolver nutzen bestehende DHT-Infrastruktur, keine eigene Infrastruktur nötig

**Was damit funktioniert:** Dasselbe wie bei did:peer:4 — Key-Rotation, Multi-Device, Multi-Key. Zusätzlich: **Globale Auflösung** via 15-Jahre-alte BitTorrent-Infrastruktur.

**Vorteile gegenüber did:peer:4:**
- Keine eigene Publishing-Infrastruktur nötig (Mainline DHT existiert)
- Globale Auflösbarkeit ohne Peer-Discovery
- Web5/DIF hat produktionsreife Implementation (TypeScript in `web5-js`, Rust via `pkarr`), MIT-lizenziert

**Nachteile gegenüber did:peer:4 (Detail-Recherche 20.04.2026):**
- **1000-Byte-Limit** via BEP44 — für Multi-Key/Multi-Service-DID-Documents eng, zwingt zu Kompression
- **Retention-PoW auf Gateways** — Mainline hält Records nur ~2h, danach müssen Gateways (via SHA-256-PoW) die Persistenz verlängern. **In der Praxis de facto zentralisiert** über wenige Gateway-Betreiber (pkarr.org, TBD-Gateway)
- **Identity-Key nicht rotierbar** — Rotation geschieht nur via `_prv._did`-Record im neuen DID, Chain-of-Custody. Weniger elegant als did:peer:4
- Abhängigkeit von externem Netzwerk (Mainline DHT), das nicht unseres ist
- "BitTorrent" klingt für manche User/Institutionen ideologisch belastet
- Web5-Adoption unklar — Projekt in Maintenance bei DIF seit Nov 2024

**Was wir dafür bauen müssten:**
- did:dht-Resolver integrieren (fertig verfügbar in `@web5/dids`)
- Publishing-Flow für DID-Documents (BEP44-Signaturen)
- Gateway für Web-Only-Clients
- Eventuell eigenen Gateway betreiben, um nicht von pkarr.org/TBD abhängig zu sein — dann sind wir wieder bei "eigene Infrastruktur"

### Direkter Vergleich

| Kriterium | A (did:peer:4) | B (Migration) | C (did:dht) |
|---|---|---|---|
| DID-Stabilität | ✅ bleibt für immer | ❌ ändert sich bei Rotation | ✅ bleibt für immer |
| Kompromittierung → Recovery | ✅ Update-Attestation | ✅ Migration + Guardian-Quorum | ✅ DHT-Update via Guardian-Signatur |
| Verlust → Recovery | ✅ Guardian-Update | ✅ Guardian-autorisierte Migration | ✅ Guardian-Update |
| Externe Referenzen | ✅ bleiben gültig | ❌ werden stale | ✅ bleiben gültig |
| Multi-Key (Device, Passkey) | ✅ First-Class | ⚠️ Ad-hoc | ✅ First-Class |
| Infrastruktur-Aufwand | 🟠 eigene Publishing-Schicht | 🟡 Migration-Protokoll | 🟢 externe Mainline-DHT nutzbar |
| Globale Auflösbarkeit | ❌ nur wenn Peer den Document hat | ❌ nur innerhalb unseres Netzes | ✅ weltweit via DHT |
| Abhängigkeit von Fremd-Infrastruktur | ✅ keine | ✅ keine | ❌ Mainline DHT |
| Referenz-Implementation vorhanden | ❌ wir schreiben | ❌ wir schreiben | ✅ web5-js (MIT) |
| Baubasis für andere Features | ✅ Multi-Device, Passkey | ❌ isoliert | ✅ Multi-Device, Passkey |

### Offline-Fitness und Community-Use-Case

Ein weiterer Vergleichs-Punkt, der durch die DIF-Recherche (20.04.2026) sichtbar wurde: **did:webvh** — die vierte Multi-Key-DID-Option, von BC Gov (Kanada) und Schweizer Bundes-Wallet (swiyu) getrieben.

**did:webvh in Kürze:** DID als URL mit kryptographisch verifizierbarer Versionshistorie (`did:webvh:<scid>:domain.de/path`). Das DID-Document liegt als `did.jsonl` auf einem Webserver, jede Version ist signiert und hash-verkettet zur vorherigen. Authentizität ist kryptographisch (SCID im Namen nagelt Genesis fest), nicht server-vertrauensbasiert.

**Warum did:webvh keine eigene Option D bekommt:** Obwohl aktiver entwickelt als did:peer:4, ist es für unseren Kern-Use-Case strukturell schlechter geeignet — weil es einen Webserver pro User erfordert.

#### Offline-Vergleich did:peer:4 vs. did:webvh

| Szenario | did:peer:4 (Ansatz A) | did:webvh |
|---|---|---|
| Erster Kontakt ohne Internet | ✅ long-form im QR-Code nativ | ❌ braucht HTTP GET zum Webserver |
| Offline-Key-Rotation publizieren | ✅ via Store-and-Forward | ❌ braucht Server-Upload |
| Offline-Signatur-Verifikation (bekannte DID) | ✅ wenn Document gepeert | ✅ wenn gecached |
| Ganz ohne Online ausgekommen | ✅ möglich | ❌ Genesis muss online publiziert werden |
| Server-Ausfall | ✅ nicht betroffen | ❌ DID nicht mehr resolvebar für Neuankömmlinge |
| Offline-Mesh (LAN, Bluetooth, Festival) | ✅ nativ unterstützt | ❌ nicht unterstützt |
| Globale Auffindbarkeit für fremde Verifier | ❌ braucht Registry | ✅ URL reicht |
| Governmental Adoption | ❌ nicht vorhanden | ✅ CH swiyu 2026, BC Gov |
| Keine Infrastruktur-Abhängigkeit | ✅ User mit Handy reicht | ❌ Webserver nötig |

#### Was das für unsere Zielgruppe bedeutet

Unsere Haupt-Use-Cases sind Communities, Ecovillages, Nachbarschafts-Netze, Kooperativen, Festivals — Kontexte, in denen **Offline-Fähigkeit und Infrastruktur-Unabhängigkeit konstitutiv** sind. Dort ist did:peer:4 strukturell überlegen.

did:webvh ist stark, wo wir **external verifier** erreichen wollen (Regierungen, Enterprise-Systeme, öffentliche Referenzen). Das ist nicht unsere Phase-1-Aufgabe, aber könnte langfristig als **Bridge-Layer** relevant werden.

**Hybrid-Gedanke für Phase 3+:** User hat primär eine did:peer:4-Identität. Optional kann er eine did:webvh-Version ausstellen, die auf dasselbe Key-Material zeigt — für Kontexte, in denen eine URL-basierte DID relevant ist. Das wäre additive Option, nicht Ersatz.

Für v1 bleibt did:peer:4 die richtige Wahl — die Offline-Eigenschaften passen direkt zum "Community-Resilienz"-Narrativ, das auch strategisch unser Kern ist.

### Aktuelle Präferenz: Ansatz A

**Stand 20. April 2026 (präzisiert nach Web5-Detail-Recherche):** Wir tendieren zu Ansatz A (did:peer:4). Die Detail-Recherche zu did:dht hat gezeigt, dass dessen Vorteile weniger stark sind als auf den ersten Blick:

- Die "globale Auflösbarkeit via 20M DHT-Nodes" ist **praktisch nur über wenige Gateway-Betreiber** verfügbar (PoW-basierte Retention, Mainline hält Records nur 2h)
- Das **1000-Byte-Limit** der BEP44-Payload ist eng für Multi-Key/Multi-Service
- **Identity-Key-Rotation** ist weniger elegant als bei did:peer:4

Ansatz C bleibt eine Alternative, insbesondere wenn wir die fertige Web5-Referenz nutzen wollen — aber die Souveränitäts-Eigenschaften von Ansatz A sind klarer, als ich ursprünglich dargestellt hatte.

**Ansatz B** ist aus heutiger Sicht die schwächste Option, weil DID-Instabilität einen Preis hat, den wir nicht zahlen müssen, wenn A oder C verfügbar sind.

**Was noch geklärt werden muss:**

- Lässt sich did:peer:4 realistisch mit unserer wot-profiles-Infrastruktur umsetzen?
- Wie stark ist die Mainline-DHT-Abhängigkeit in der Praxis einschränkend? (Gateway-Nodes in restriktiven Netzen)
- Wieviel Komplexität bringt Ansatz A oder C für Clients (speziell den TypeScript-WoT-Core)?
- Wie wird Sebastians Rust-Impl das adoptieren (human-money-core)?
- Können wir did:dht als **fertige Referenz** nutzen und damit Time-to-Market halten?

Diese Fragen stehen offen. Ansatz A ist die aktuelle Richtung, C eine ernstzunehmende Alternative, nicht die bereits gewählte.

## Multi-Key-Konsequenzen — Signieren, Verifikation, Offline

Wenn wir Ansatz A (did:peer:4) verfolgen, bringt das Multi-Key-DID-Modell eine Reihe von Konsequenzen für Signatur-Erstellung und -Verifikation, die bei did:key trivial waren. Diese Konsequenzen sind lösbar (andere Projekte wie Aries, ION haben es gelöst), aber sie erweitern die Spec substantiell.

### Wie Signieren technisch funktioniert

Jedes Gerät (Laptop, Phone, Hardware-Token) hat seinen eigenen Ed25519-Keypair, als `verificationMethod` im DID-Document registriert, mit klaren Relations:

- `authentication` — für Broker-Login
- `assertionMethod` — für Attestation-Signing

Wenn ein Device eine Attestation signiert, verweist die JWS explizit auf den signierenden Key:

```json
{
  "alg": "EdDSA",
  "kid": "did:peer:4...alice#device-phone"
}
```

Der `kid` ist keine bloße Kennung, sondern eine verifizierbare Referenz auf die genaue Verification Method im DID-Document.

### Wie Verifikation funktioniert

Der Verifier-Flow ist ein Mehr-Schritt-Prozess:

1. **DID-Document resolven** (alle Verification Methods laden)
2. **Key unter `kid` finden** und prüfen, ob er zur Zeit der Signatur:
   - Im Document stand
   - Die richtige Relation hatte (bei Attestation: `assertionMethod`)
3. **Signatur kryptographisch verifizieren**

Das ist der Standard-DID-VC-Flow (wie in Aries, ION, Veramo). Deutlich komplexer als bei did:key, wo der Key Teil der DID war und in einem Schritt verifizierbar war.

### Das Historie-Problem (Key-Revocation)

Angenommen:

- T1: Alice signiert Attestation mit `device-phone-v1`
- T2: Alice verliert Phone, revoziert `device-phone-v1` im DID-Document
- T3: Bob will die Attestation verifizieren

**Ist die Signatur noch gültig?** Zwei mögliche Semantiken:

**A) Historisch gültig:** Signatur war zum Zeitpunkt der Erstellung gültig → bleibt gültig. Die Attestation ist wie ein altes Zertifikat, das zum Zeitpunkt der Ausstellung von einer autorisierten CA kam.

**B) Aktuell gültig:** Signatur ist nur gültig, wenn der Key aktuell im DID-Document steht.

Für **Attestations** (langlebige Claims über Fakten) macht A mehr Sinn. Für **Login-Challenges** (aktuelle Autorisierung) macht B mehr Sinn.

**Das heißt: wir brauchen eine zeitliche Dimension.** Zwei Möglichkeiten:

1. **Versionierte DID-Documents** — jede Version hat Timestamp. Attestation referenziert die Version, die zum Signier-Zeitpunkt aktuell war. Verifier prüft gegen diese Version.

2. **Append-only DID-Document** — Keys werden nie gelöscht, sondern mit `revokedAt`-Zeitstempel markiert. Alte Signaturen bleiben gültig gegen Keys, die zum Signier-Zeitpunkt nicht revoziert waren.

Beide sind funktional gleichwertig; append-only ist einfacher zu implementieren.

**Problem bleibt bei Kompromittierung:** Wenn `device-phone-v1` kompromittiert wurde und der Angreifer damit nachträglich zurück-datierte Attestations signiert ("datiert" auf T0.5, bevor Alice die Kompromittierung merkte), kann der Verifier das nicht unterscheiden — sofern die Attestation nicht auf einen unabhängigen Zeitanker verweist.

**Mitigation:** Attestations enthalten einen Zeitstempel plus Referenz auf eine Log-Sequence-Number, die vom Relay mitsigniert wird. Angreifer kann keine alten Log-Sequence-Numbers erfinden.

### Das Offline-Problem

**Bei did:key:** trivial. Die DID enthält den Pubkey. Offline-Verifikation = Signatur gegen in-DID-Key prüfen. Ein Durchgang, keine Netzwerk-Anfrage.

**Bei did:peer:4:** Verifier braucht das DID-Document. Woher?

Drei Strategien, die sich ergänzen:

**1. DID-Document wird beim ersten Kontakt ausgetauscht und lokal gecached**

Bei der In-Person-Verifikation (Core 004) werden DID-Documents mit ausgetauscht. Jeder Peer cached die DID-Documents seiner Kontakte lokal. Offline-Verifikation nutzt den Cache.

Konsistent mit unserem "Peer = Peer"-Modell: wenn zwei Peers sich direkt kennen, müssen sie nicht über einen Dritten resolven.

**2. DID-Document-Updates werden gegossipt**

Jede Änderung am DID-Document (Key hinzugefügt, revoziert, Guardian-Set geändert) wird als Update-Attestation in den Log geschrieben und über DIDComm verteilt. Peers, die mit Alice verbunden sind, bekommen Updates automatisch.

Analog zu Sebastians H03 Trust-List-Gossip, nur für DID-Document-Updates statt Trust-Listen.

**3. DID-Document-Snapshot wird mit Attestations mitgeliefert**

Ähnlich wie bei SD-JWT-VC, wo der Issuer-Key direkt im Header als `jwk` sitzen kann. Wir könnten Attestations optional einen Snapshot des DID-Documents zum Signier-Zeitpunkt mitliefern lassen. Redundanz, aber Verifikation komplett ohne externen Resolver.

Das würde Attestations um einige KB vergrößern, ist aber für wichtige, langlebige Attestations (z.B. Verification bei Erst-Begegnung) angemessen.

### Konkrete Offline-Szenarien

**Szenario 1: In-Person-QR-Code-Verifikation (Core 004), beide offline**

- Alice und Bob zeigen QR-Codes mit ihren DIDs
- Die DIDs sind did:peer:4 short-form — Verifikation erfordert DID-Document
- Lösung: QR-Code enthält die long-form mit eingebettetem Document, oder ein zusätzlicher QR-Code für das DID-Document
- Nach Scan haben beide Seiten die DID-Documents, können Challenge-Response-Signaturen verifizieren

Für den ersten Verifikations-Schritt reicht das initiale DID-Document. Spätere Updates werden über die Inbox nachgezogen, sobald wieder Connectivity besteht.

**Szenario 2: Alice signiert offline eine Attestation für Bob (z.B. gegenseitige Attestation nach Verifikation)**

- Alice signiert mit `#device-phone`
- Attestation enthält `kid` und Alice's DID
- Attestation wird Bob übergeben (QR, NFC, Bluetooth)
- Bob hat Alice's DID-Document bereits lokal (aus dem Verifikations-Handshake davor)
- Bob kann sofort verifizieren

**Szenario 3: Bob verifiziert später eine Attestation, Alice hat in der Zwischenzeit ihre Keys rotiert**

- Bob hat lokal Alice's DID-Document Stand T0
- Attestation wurde zu T1 signiert, Alice hat zu T2 rotiert
- Bob ist jetzt zu T3 offline, hat den Update T2 noch nicht bekommen
- Bob verifiziert gegen seinen lokalen Stand T0
- Signatur passt zu Keys aus T0 — akzeptiert (korrekt: die Attestation wurde zu T1 signiert, als der alte Key gültig war)
- Wenn Bob online kommt, bekommt er Update T2 — bei Historisch-gültig-Semantik ändert das nichts an vergangenen Signaturen

**Szenario 4: Bob verifiziert eine Attestation mit einem ihm unbekannten Device-Key**

- Alice hat ein neues Device-Key `#device-tablet` hinzugefügt
- Alice signiert mit Tablet-Key
- Bob hat nur alten DID-Document-Stand ohne Tablet-Key
- Bob kann die Signatur nicht verifizieren
- Bob muss Update anfordern → offline ist das problematisch, muss warten bis Connectivity zu Alice oder dritter Quelle
- Oder: die Attestation liefert den aktuellen DID-Document-Snapshot mit → Bob kann sofort verifizieren

### Implikationen für die Spec

Wir brauchen zusätzlich zu Core 001-002:

1. **DID-Document-Update-Attestation-Format** — wer darf was signieren (Master, Guardian-Quorum, Device-Keys mit begrenzten Rechten)
2. **DID-Document-Distribution-Protokoll** — Updates im eigenen Log + Gossip an Kontakte + abrufbar vom wot-profiles-Service
3. **Verifikations-Algorithmus mit zeitlicher Dimension** — Historisch-gültig-Semantik, append-only Revocation, optional Log-Sequence-Timestamps
4. **Attestation-embedded DID-Document-Snapshots** für Offline-Verifikation kritischer Attestations (optional)
5. **QR-Code-Format bei In-Person-Verifikation mit long-form DID**

Das ist substantiell. Jeder dieser Punkte ist konzeptionell geklärt (andere Projekte machen das), aber wir müssen es für unseren Kontext spezifizieren.

### Gegenüberstellung did:key vs. did:peer:4

| Aspekt | did:key | did:peer:4 |
|---|---|---|
| Signieren | Ed25519-Signature mit Mnemonic-Key | Ed25519-Signature mit Device-Key (via `kid`) |
| Verifikation online | DID → Pubkey → prüfen (1 Schritt) | DID → DID-Document → Key unter `kid` → prüfen (3 Schritte) |
| Verifikation offline | Immer möglich (Pubkey in DID) | Möglich wenn DID-Document gecached |
| Key-Rotation | Nicht möglich (DID wechselt) | Standard-Operation, DID bleibt |
| Multi-Device | Nicht sauber (alle teilen einen Key) | First-Class (Device-Keys separiert) |
| QR-Code-Handshake | DID reicht | DID + DID-Document (long-form oder zusätzlich) |
| Spec-Umfang | Core 001-002 (einfach) | Core 001-002 + DID-Document-Update + Distribution + Versioning |

### Nebeneffekt: Mnemonic verliert an Alleinstellung

did:peer:4 löst das Wortlisten-Problem **nicht direkt**. Wenn ein User seinen Mnemonic in einer bestimmten Wortliste aufgeschrieben hat und in eine App wechseln will, die diese Wortliste nicht kennt, scheitert die Wiederherstellung — bei did:key und bei did:peer:4 identisch.

Aber did:peer:4 macht **andere Migrations-Wege natürlicher**, die das Wortlisten-Problem umgehen:

1. **Guardian-Vouching (NLnet WP2):** User nimmt in neuer App neuen Private Key, Guardians signieren DID-Document-Update. Kein Mnemonic nötig. Bei did:peer:4 ist das der kanonische Rotations-Mechanismus. Bei did:key müsste jede App zusätzlich ein DID-Migrations-Protokoll kennen.

2. **Device-zu-Device-Transfer:** Private Key wird via QR, NFC oder USB übertragen. Bei did:peer:4 durch Multi-Key-Unterstützung natürlich (neuer Device-Key kommt ins DID-Document, alter bleibt parallel gültig).

3. **Raw-Key-Export/Import:** Private Key als Hex oder JSON rüberkopieren. Funktioniert grundsätzlich in beiden DID-Methoden.

**Das eigentlich Entlastende:** Das Wortlisten-Problem ist strukturell eine Folge davon, den Mnemonic als alleinigen oder primären Backup-Weg zu behandeln. Sobald gleichwertige Alternativen verfügbar sind (Guardian, Device-Transfer, Raw-Export), verliert der Mnemonic seine Alleinstellung — und damit auch die Wortlisten-Blockade für Migration.

Bei did:peer:4 ist das realistischer, weil Guardian-Vouching kanonisch in allen konformen Apps verfügbar ist. Bei did:key bliebe es eine Sonderlösung.

**Ehrliche Nuance:** Für User, die **ausschließlich** den Mnemonic als Backup haben, bleibt das Wortlisten-Problem auch bei did:peer:4 bestehen. Die Entschärfung gilt für User, die andere Wege zur Verfügung haben.

### Ehrliche Bilanz

**did:peer:4 gibt uns Key-Rotation und Multi-Key-Support**, kostet uns dafür:

- **Verifikation wird nicht-trivial** — Resolver nötig, Timestamp-Semantik, Document-Versionen
- **Offline wird komplizierter** — Cache-Strategie, DID-Document-Distribution, eventuell eingebettete Snapshots
- **Spec wird deutlich größer** — neue Protokolle für Distribution und Update-Attestations

Das ist der Preis der Flexibilität. Die Frage, die wir beantworten müssen: **ist die Fähigkeit zur Key-Rotation des primären Keys es uns wert, diese Komplexität zu tragen?**

Aus aktueller Sicht: ja. Die strukturelle Schwachstelle einer nicht-rotierbaren Primary-Identity ist in einem System, das als langlebige Identitäts-Infrastruktur gedacht ist, ein echtes Problem. Die Multi-Key-Komplexität ist lösbar (bekannte Pfade aus Aries/ION/Veramo) und legt gleichzeitig das Fundament für weitere Features (Multi-Device, Passkey-Integration, Sebastians Liability-Modell).

## Hybrid-Vorschlag für Web of Trust

Basierend auf der bisherigen Exploration, hier ein konsistentes Gesamt-Modell — unter der Annahme, dass wir Ansatz A verfolgen:

### Drei-Ebenen-Architektur

**Ebene 1 — Root of Trust:**
- BIP39-Mnemonic (englische Standard-Wortliste)
- Cold-Backup auf Papier oder in Offline-Medium
- User sieht die 12 Wörter einmal bei Setup, schreibt sie auf, dann nie wieder
- Für die 5% der User, die Recovery via Mnemonic wollen oder brauchen

**Ebene 2 — Day-to-Day-Unlock:**
- User-gewähltes Passwort
- Argon2id mit OWASP-2024-Parametern
- zxcvbn-Prüfung: Score ≥ 3 erzwingen
- Login-Block-Pattern: Passwort entsperrt lokalen verschlüsselten Container
- Container enthält das langlebige Ed25519-Material
- Passwort-Wechsel möglich ohne DID-Wechsel (Ancestor-Proof)

**Ebene 3 — Guardian-Vouching (optional, aktivierbar):**
- User wählt M-von-N verifizierte Kontakte als Guardians
- Guardian-Vouching via signierte Attestations (NLnet WP2) — kein Shamir, keine Threshold-Kryptographie
- Recovery wenn beide — Passwort und Mnemonic — verloren sind
- Bei Ansatz A (did:peer:4): Guardians co-signieren DID-Document-Update, DID bleibt stabil
- Bei Ansatz B (did:key-Migration): Guardians signieren Equivalence-Proof zur neuen DID
- Integriert mit unserem WoT-Graphen — Guardians sind automatisch aus verifizierten Kontakten

### User-Erfahrung

**Setup:**
1. User öffnet App, erstellt Identität
2. App generiert BIP39-Mnemonic → zeigt ihn einmal
3. User bestätigt "Ich habe aufgeschrieben" oder "Später"
4. User wählt Passwort für Day-to-Day
5. (Optional) User wählt Guardians aus seinen verifizierten Kontakten

**Normaler Login:**
- Nur Passwort — wie jede andere App

**Recovery-Pfade:**
1. Passwort vergessen → Mnemonic eingeben → neues Passwort
2. Mnemonic verloren → Passwort reicht (Device-gebunden)
3. Beides verloren → Guardian-Recovery (3-von-5)
4. Total-Verlust ohne Guardians → Identität ist verloren, neue DID

### Was wir dabei aufgeben und was wir gewinnen

**Aufgegeben:**
- Einfachheit der aktuellen Spec (ein einziger Ableitungspfad)
- Klare "12 Wörter = alles, was du brauchst"-Story

**Gewonnen:**
- Mainstream-taugliche UX für normale User (nur Passwort)
- Gleichzeitig starke Sicherheit für Power-User (Mnemonic)
- Recovery-Pfad über Community (Guardians) — einzigartig für ein WoT-Projekt
- Passwort-Wechsel ohne DID-Wechsel
- Capability-Delegation via Hash-Derivation für Space-Sharing

## Offene Fragen

1. **Ist Hybrid-Architektur zu komplex für v1.0?** Mehrere Ebenen erhöhen Surface und Implementation-Aufwand. Müssen wir zuerst schlank starten und später erweitern?

2. **Wie verhält sich Login-Block-Indirektion zu unserem Broker-Modell?** CryptPad hat einen zentralen Server — unser Modell hat Broker. Wo wird der Login-Block gespeichert? Auf dem primären Broker? Lokal?

3. **Guardian-Recovery: Wieviele Guardians als Default?** 3-von-5 ist üblich, aber für kleinere Communities (Nachbarschaft) vielleicht anders.

4. **Threshold Secret Sharing vs. Threshold-Ed25519 vs. SSS über HKDF-Material**: Welche Technik passt am besten zu unserer Krypto-Architektur?

5. **Wie ändert sich die Guardian-Liste?** Wenn ein Guardian die Beziehung verlässt, muss dessen Share invalidiert werden. Das erfordert Re-Sharing unter den verbleibenden.

6. **Wallet-Datei-Transfer zwischen Geräten**: NextGraph macht das über QR-Code / USB. Unser Broker-Modell macht das anders. Wie integrieren wir?

7. **Wortlisten-Frage** (aus paralleler Diskussion): Bleiben wir bei der deutschen Positive-Liste, oder wechseln wir auf BIP39-Englisch-Standard für Interop?

8. **Passkey-Integration**: Wo passen Passkeys in dieses Modell? Als zusätzlicher Unlock-Pfad neben Passwort?

## Quellen und Referenzen

### Projekte

- [NextGraph Wallet Docs](https://docs.nextgraph.org/en/wallet/)
- [NextGraph FOSDEM 2026 Talk](https://fosdem.org/2026/schedule/event/J3ZBYC-nextgraph-sync-engine-sdk-reactive-orm/)
- [CryptPad Whitepaper](https://blog.cryptpad.org/images/whitepaper.pdf)
- [CryptPad Source](https://github.com/cryptpad/cryptpad)
- [Jazz Authentication](https://jazz.tools/docs/react/key-features/authentication/overview)
- [Argent Recovery](https://support.argent.xyz/hc/en-us/articles/360007338877)
- [Soul Wallet](https://www.soulwallet.io)
- [Keyhive (Ink & Switch)](https://www.inkandswitch.com/project/keyhive/)

### Akademische und Standards-Quellen

- [Vitalik: Social Recovery Wallets](https://vitalik.eth.limo/general/2021/01/11/recovery.html)
- [OPAQUE: Asymmetric Password-Authenticated Key Exchange (Jarecki et al. 2018)](https://eprint.iacr.org/2018/163)
- [SLIP-0010 (SatoshiLabs)](https://github.com/satoshilabs/slips/blob/master/slip-0010.md)
- [BIP39 German Wordlist PRs (alle abgelehnt)](https://github.com/bitcoin/bips/pull/1071)
- [OWASP Password Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html)

### Unsere zugehörigen Dokumente

- [Core 001: Identität und Schlüsselableitung](../01-wot-core/001-identitaet-und-schluesselableitung.md) — aktueller Stand
- [Identity Migration](identity-migration.md) — Schlüsselrotation
- [Security Analysis](security-analysis.md) — M6 Device-Revokation
