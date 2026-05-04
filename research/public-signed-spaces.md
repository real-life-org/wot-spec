# Public-Signed Spaces

> **Nicht normativ:** Dieses Dokument ist ein Architektur- und Implementierungsentwurf. Normative Anforderungen stehen erst in den Spec-Dokumenten, Schemas, Testvektoren und `CONFORMANCE.md`, nachdem eine TypeScript-Implementierung den Ansatz validiert hat.

Status: Draft / Proposal  
Zielphase: nach stabiler WoT-Demo-vNext-Migration, vor bzw. waehrend der Real-Life-Stack-Reference-App-Migration

## Motivation

Real-Life-Communities brauchen oeffentlich erreichbare Gruppen/Spaces, die sich wie eigene White-Label-Apps anfuehlen:

- eigene Domain, eigenes Branding, eigene Module;
- jeder mit Link oder Adresse kann Inhalte lesen;
- Schreiben bleibt kontrolliert;
- Live-Updates funktionieren auch fuer Besucher;
- kein zentrales Listing ist fuer den Anfang noetig.

Das passt zum Real-Life-Vernetzungskonzept: Initiativen werden sichtbar, behalten aber ihre Identitaet. Ein Space kann unter einer eigenen Domain erreichbar sein und trotzdem interoperabel mit dem WoT-Netzwerk bleiben.

Die aktuelle Gruppen-Spezifikation beschreibt primaer verschluesselte Memberspaces. Fuer oeffentliche Link-Spaces ist ein eigener Modus sinnvoll, weil ein oeffentlicher Leseschluessel keine tragfaehige Zugriffskontrolle bietet.

## Nicht-Ziele fuer diesen Draft

- Kein globales Gruppenverzeichnis.
- Keine normative Erweiterung der aktuellen vNext-Conformance.
- Keine Schemas oder Testvektoren in diesem Schritt.
- Keine Migration bestehender verschluesselter Gruppen.
- Kein Ersatz fuer E2EE-Spaces. Private und oeffentliche Spaces bleiben unterschiedliche Modi.

## Kernentscheidung

WoT sollte langfristig zwei Space-Modi unterscheiden:

| Modus | Lesen | Schreiben | Geeignet fuer |
|-------|-------|------------|---------------|
| `encrypted-members` | nur Mitglieder mit Content-Key | Mitglieder mit gueltiger Membership/Capability | private Gruppen, vertrauliche Zusammenarbeit |
| `public-signed` | jeder mit Link/Adresse | DIDs mit gueltiger Write-Capability | White-Label-Community-Spaces, oeffentliche Kalender, Karten, Feeds |

`public-signed` verzichtet fuer oeffentliche Inhalte auf Content-Verschluesselung. Authentizitaet und Schreibrechte werden durch Signaturen, Capabilities, Revocation und Moderation gesichert.

## Warum kein Public Read Key

Ein alternativer Ansatz waere, einen normalen verschluesselten Space mit einem oeffentlichen Read-Key im Link oder Descriptor auszuliefern. Das hat mehrere Probleme:

- Der Read-Key kann nicht gleichzeitig Schreib-Autoritaet sein.
- Live-Updates fuer Nicht-Mitglieder brauchen trotzdem einen oeffentlichen Update-Kanal.
- Key-Rotation funktioniert nur als Link-Rotation und nicht als echte Zugriffskontrolle.
- Wer den alten Key kennt, kann alte Inhalte weiter lesen.
- Spaetere Migration zu signierten Public Spaces waere teuer.

Wenn ein Space absichtlich oeffentlich lesbar ist, sollte das Protokoll ihn als oeffentlich lesbar modellieren und nicht als verschluesselt mit veroeffentlichtem Schluessel.

## Policy-Achsen

Oeffentliche Link-Spaces sollten Lesen, Schreiben und Beitritt getrennt modellieren:

```ts
type SpaceMode = 'encrypted-members' | 'public-signed'
type Visibility = 'private' | 'link' | 'listed'
type ReadAccess = 'members' | 'public'
type JoinAccess = 'invite' | 'request' | 'open' | 'closed'
```

Fuer `public-signed` ist `readAccess = 'public'`. `joinAccess` beschreibt, wie eine DID Schreibrechte bekommen kann:

| `joinAccess` | Bedeutung |
|--------------|-----------|
| `invite` | Admins oder berechtigte Members stellen Write-Capabilities aktiv aus |
| `request` | Besucher stellen Join-Requests, Admins akzeptieren oder lehnen ab |
| `open` | eingeloggte DIDs koennen automatisch eine Write-Capability erhalten |
| `closed` | keine neuen Write-Capabilities |

Schreibrechte sollten intern immer ueber Write-Capabilities geprueft werden, nicht ueber die blosse Mitgliedschaftsanzeige.

## Public Space Descriptor

Ein Link oder eine White-Label-Domain loest auf einen signierten Public Space Descriptor auf. Der Descriptor ist der Einstiegspunkt fuer Besucher und Clients.

Beispielhafte, nicht normative Struktur:

```json
{
  "spaceId": "7f3a2b10-4c5d-4e6f-8a7b-9c0d1e2f3a4b",
  "mode": "public-signed",
  "visibility": "link",
  "readAccess": "public",
  "joinAccess": "request",
  "name": "Transition Town Stuttgart",
  "description": "Lokale Gruppe fuer Wandel und Nachbarschaftsvernetzung",
  "modules": ["feed", "calendar", "map"],
  "branding": {
    "domain": "app.transitiontown-stuttgart.de",
    "logo": "https://example.org/logo.svg",
    "primaryColor": "#2f7d4f"
  },
  "brokerUrls": ["wss://broker.example.org"],
  "snapshotUrl": "https://storage.example.org/spaces/7f3a2b10/snapshot",
  "adminDids": ["did:key:z6Mk..."],
  "capabilityVerificationKeys": ["z6Mk..."],
  "policyGeneration": 1,
  "updatedAt": "2026-05-01T12:00:00.000Z"
}
```

Der Descriptor selbst sollte von einem autoritativen Space-/Admin-Key signiert werden. Details zu Key-Hierarchie, Rotation und Multi-Admin-Sicherheit bleiben offen.

## Read Flow

Fuer Besucher ohne Membership:

```text
Link/Domain oeffnen
  -> Public Space Descriptor laden
  -> Descriptor-Signatur pruefen
  -> Snapshot laden
  -> Snapshot-Signatur pruefen
  -> oeffentlichen Update-Stream abonnieren
  -> jedes Update signatur- und capability-pruefen
  -> gueltige Updates lokal anwenden
```

Der Client darf oeffentliche Updates nicht nur deshalb anwenden, weil sie vom Broker kommen. Der Broker transportiert; Autorisierung entsteht durch signierte Updates und gueltige Capabilities.

## Write Flow

Schreiben ist ein DID-signierter Vorgang mit gueltiger Write-Capability.

```text
Client erzeugt CRDT-/Log-Update
  -> Update mit DID signieren
  -> passende Write-Capability referenzieren oder beilegen
  -> an Broker senden
  -> Empfaenger pruefen Signatur, Capability, Revocation und Policy-Generation
  -> Update anwenden oder verwerfen
```

Eine Write-Capability kann als signiertes Objekt modelliert werden:

```json
{
  "type": "write-capability",
  "spaceId": "7f3a2b10-4c5d-4e6f-8a7b-9c0d1e2f3a4b",
  "subjectDid": "did:key:z6Mk...member",
  "role": "member",
  "permissions": ["item:create", "item:update:own", "comment:create"],
  "issuedBy": "did:key:z6Mk...admin",
  "issuedAt": "2026-05-01T12:00:00.000Z",
  "expiresAt": null,
  "policyGeneration": 1
}
```

Rollen sind Komfort. Die Sicherheitsentscheidung sollte aus `permissions`, Aussteller, Policy-Generation und Revocation entstehen.

## Join Modes

### Invite

```text
Admin waehlt DID aus
  -> Write-Capability ausstellen
  -> Capability per Inbox zustellen oder im oeffentlichen Capability-Log veroeffentlichen
  -> eingeladene DID kann schreiben
```

Geeignet fuer oeffentliche Webseiten mit Redaktionsteam oder kuratierten Projektgruppen.

### Request

```text
Besucher klickt "Mitmachen"
  -> Join-Request mit eigener DID signieren
  -> Admins erhalten Request
  -> Admin akzeptiert
  -> Write-Capability wird ausgestellt
```

Geeignet fuer oeffentliche Initiativen, bei denen Menschen sichtbar andocken koennen, aber Schreibrechte moderiert werden.

### Open

```text
Besucher authentifiziert sich mit DID
  -> automatische Write-Capability nach Space-Policy
  -> Schreiben ist moeglich, aber weiterhin DID-signiert und widerrufbar
```

Open-Write sollte nur mit Spam-Schutz, Rate-Limits und Moderation produktiv aktiviert werden. Fuer Real-Life-Kontexte koennen zusaetzliche Voraussetzungen sinnvoll sein, z.B. verifiziertes Profil oder Trust-Beziehung zu einem Member.

## Moderation und Revocation

`public-signed` braucht andere Rotation als private E2EE-Spaces:

- keine Content-Key-Rotation fuer Lesen;
- Capability-Revocation fuer Schreibrechte;
- Policy-Generation fuer Aenderungen an Rollen, Berechtigungen und Admin-Keys;
- Ban-/Blocklisten fuer Spam und Missbrauch;
- Moderator-Capabilities fuer Hide/Delete/Restore-Operationen.

Beispielhafte Revocation:

```json
{
  "type": "capability-revocation",
  "spaceId": "7f3a2b10-4c5d-4e6f-8a7b-9c0d1e2f3a4b",
  "subjectDid": "did:key:z6Mk...",
  "capabilityId": "cap-123",
  "effectiveAt": "2026-05-01T12:30:00.000Z",
  "reason": "spam"
}
```

Clients sollten Updates gegen den aktuellen Policy-/Revocation-State pruefen. Offene Frage bleibt, wie viel Historie nachtraeglich ausgeblendet werden kann, ohne CRDT-Konvergenz oder Auditierbarkeit zu brechen.

## Mapping zu Real Life Stack

Real Life Stack modelliert Gruppen als Scopes mit `Group.data`. Public-Signed-Spaces koennen in dieses Modell passen:

```ts
group.data = {
  scope: 'group',
  spaceMode: 'public-signed',
  visibility: 'link',
  readAccess: 'public',
  joinAccess: 'request',
  modules: ['feed', 'calendar', 'map'],
  branding: {
    domain: 'app.transitiontown-stuttgart.de',
    logo: 'https://example.org/logo.svg',
    primaryColor: '#2f7d4f'
  }
}
```

Eine White-Label-App ist dann eine App-Shell mit vorkonfiguriertem Public Space Descriptor. Besucher sehen den Space read-only. Eingeloggte DIDs koennen je nach Join-Modus Schreibrechte beantragen, erhalten oder nutzen.

## Umsetzung in der TypeScript-Implementierung

Vor einer normativen Spec sollten nur Extension Points eingebaut werden, die private E2EE-Spaces nicht blockieren:

- Space-/Group-Metadaten duerfen nicht mehr implizit annehmen, dass jeder Space `encrypted-members` ist.
- Policies sollten als Datenmodell vorbereitet werden: `spaceMode`, `visibility`, `readAccess`, `joinAccess`.
- Connector- und UI-Schichten sollten Read-only-Besucher sauber darstellen koennen.
- Write-Pfade sollten langfristig Capabilities statt impliziter Key-Membership pruefen koennen.

Die vollstaendige Runtime fuer `public-signed` sollte als eigener Implementierungs-Slice nach der stabilen WoT-Demo-vNext-Migration entstehen.

## Offene Fragen

- Welche Signatur- und Canonicalization-Formate nutzen Public Snapshots und Updates genau?
- Wie sieht die minimale Write-Capability fuer MVP aus?
- Gibt es einen Space-Capability-Signing-Key oder nur Admin-DIDs?
- Wie werden Admin-Key-Rotation und Multi-Admin-Sicherheit geloest?
- Wie werden Revocations in CRDT-Streams konsistent und auditierbar angewendet?
- Wie viel Moderation ist fuer `joinAccess = 'open'` Mindestanforderung?
- Welche Teile sollen spaeter in `03-wot-sync` normativ werden und welche bleiben Real-Life-Stack-spezifische Extension?

## Vorgeschlagener Pfad zur Normierung

1. Diesen Draft als nicht normativen PR diskutieren.
2. WoT-Demo-vNext-Migration stabil abschliessen.
3. Extension Points in der TypeScript-Implementierung vorbereiten.
4. Ersten `public-signed` Prototypen mit Descriptor, Public Snapshot und Live-Updates bauen.
5. Write-Capabilities fuer `invite`, danach `request`, danach `open` implementieren.
6. Danach Schemas, Testvektoren und Conformance-Anforderungen normativ ergaenzen.
