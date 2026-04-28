# Phase-1-Interop-Testvektoren

Diese Datei ergaenzt die Basis-Vektoren in `README.md`. Alle Schluessel sind oeffentlich bekannte Testwerte und duerfen niemals in Produktion verwendet werden.

## Gemeinsame Eingaben

```
Mnemonic: abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about
BIP39 Seed (64 Bytes):
5eb00bbddcf069084889a8ab9155568165f5c453ccb85e70811aaed6f6da5fc1
9a5ac40b389cd370d086206dec8aa6c43daea6690f20ad3d8d48b2d2ce9e38e4

DID: did:key:z6Mko3ZEjKJWQAM5nDXKoZ9jErvvxbWbYgS8KJXYpC5Hbu8a
kid: did:key:z6Mko3ZEjKJWQAM5nDXKoZ9jErvvxbWbYgS8KJXYpC5Hbu8a#sig-0
Ed25519 Public Key: 7fa6ae99f7fc28a61096ad3d62f91a76b5c2b39bab0decfaa16c1611e8944f17
X25519 Public Key: c8507873fd52a931a89550532a108125285259ff8dcd7af85c2c8317714a7944
X25519 Public Key (Base64URL): yFB4c_1SqTGolVBTKhCBJShSWf-NzXr4XCyDF3FKeUQ
X25519 Public Key (Multibase): z6LSqA7sbKGK3WVHP9SBcmv9ikp19iDNb1P5Q315kRPQrcTV
```

## 1. WoT Plaintext Envelope (DIDComm-kompatibel, Sync 003)

Dieser Vektor prueft nur die Envelope-Ebene. ECIES ist bewusst kein DIDComm-JWE und wird separat getestet.

```json
{"id":"550e8400-e29b-41d4-a716-446655440000","typ":"application/didcomm-plain+json","type":"https://web-of-trust.de/protocols/log-entry/1.0","from":"did:key:z6Mko3ZEjKJWQAM5nDXKoZ9jErvvxbWbYgS8KJXYpC5Hbu8a","to":["did:key:z6MkpTHR8VNsBxYAAWHut2Geadd9jSwuBV8xRoAnwWsdvktH"],"created_time":1776514800,"thid":"550e8400-e29b-41d4-a716-446655440000","body":{"docId":"7f3a2b10-4c5d-4e6f-8a7b-9c0d1e2f3a4b","payload":"abc"}}
```

Validiert mit etablierten DIDComm-v2-Libraries:

| Library | Version | Ergebnis |
|---|---:|---|
| `didcomm-node` (SICPA / didcomm-rust WASM) | 0.4.1 | `Message.unpack()` akzeptiert die Nachricht als Plaintext, `typ = application/didcomm-plain+json`, `encrypted = false` |
| `@veramo/did-comm` | 7.0.0 | `getDidCommMessageMediaType()` liefert `application/didcomm-plain+json`, `unpackDIDCommMessage()` liefert `packing = none` |

Hinweis: Veramo lehnt Plaintext Messages ohne `typ` ab. Deshalb ist `typ` im WoT-DIDComm-Envelope verpflichtend.

## 2. DID-Resolution (Identity 003)

Ein Bootstrap-DID-Dokument nach QR- oder Profil-Service-Kontakt:

```json
{"assertionMethod":["#sig-0"],"authentication":["#sig-0"],"id":"did:key:z6Mko3ZEjKJWQAM5nDXKoZ9jErvvxbWbYgS8KJXYpC5Hbu8a","keyAgreement":[{"controller":"did:key:z6Mko3ZEjKJWQAM5nDXKoZ9jErvvxbWbYgS8KJXYpC5Hbu8a","id":"#enc-0","publicKeyMultibase":"z6LSqA7sbKGK3WVHP9SBcmv9ikp19iDNb1P5Q315kRPQrcTV","type":"X25519KeyAgreementKey2020"}],"service":[{"id":"#inbox","serviceEndpoint":"wss://broker.example.com","type":"WoTInbox"}],"verificationMethod":[{"controller":"did:key:z6Mko3ZEjKJWQAM5nDXKoZ9jErvvxbWbYgS8KJXYpC5Hbu8a","id":"#sig-0","publicKeyMultibase":"z6Mko3ZEjKJWQAM5nDXKoZ9jErvvxbWbYgS8KJXYpC5Hbu8a","type":"Ed25519VerificationKey2020"}]}
```

```
SHA-256(JCS DID Document): 9f71bde97db9df9bc5fd14ab3c5a65dd3eb3e77fd1e74a43fe187a718015fefc
```

## 3. Attestation VC-JWS (Trust 001)

Payload ist das gültige Beispiel aus `schemas/examples/valid/attestation-vc-payload.json`, kanonisiert mit JCS und als `vc+jwt` signiert.

```
SHA-256(JCS Payload): 6343aadfd74d1e21310d8eda82fdc538a7b24cb736caedfd70b67be34d49548c
JWS Header: {"alg":"EdDSA","kid":"did:key:z6Mko3ZEjKJWQAM5nDXKoZ9jErvvxbWbYgS8KJXYpC5Hbu8a#sig-0","typ":"vc+jwt"}
```

JWS Compact:

```text
eyJhbGciOiJFZERTQSIsImtpZCI6ImRpZDprZXk6ejZNa28zWkVqS0pXUUFNNW5EWEtvWjlqRXJ2dnhiV2JZZ1M4S0pYWXBDNUhidThhI3NpZy0wIiwidHlwIjoidmMrand0In0.eyJAY29udGV4dCI6WyJodHRwczovL3d3dy53My5vcmcvbnMvY3JlZGVudGlhbHMvdjIiLCJodHRwczovL3dlYi1vZi10cnVzdC5kZS92b2NhYi92MSJdLCJjcmVkZW50aWFsU3ViamVjdCI6eyJjbGFpbSI6Imthbm4gZ3V0IHByb2dyYW1taWVyZW4iLCJpZCI6ImRpZDprZXk6ejZNa3BUSFI4Vk5zQnhZQUFXSHV0MkdlYWRkOWpTd3VCVjh4Um9BbndXc2R2a3RIIn0sImlzcyI6ImRpZDprZXk6ejZNa28zWkVqS0pXUUFNNW5EWEtvWjlqRXJ2dnhiV2JZZ1M4S0pYWXBDNUhidThhIiwiaXNzdWVyIjoiZGlkOmtleTp6Nk1rbzNaRWpLSldRQU01bkRYS29aOWpFcnZ2eGJXYllnUzhLSlhZcEM1SGJ1OGEiLCJuYmYiOjE3NzY3NjU2MDAsInN1YiI6ImRpZDprZXk6ejZNa3BUSFI4Vk5zQnhZQUFXSHV0MkdlYWRkOWpTd3VCVjh4Um9BbndXc2R2a3RIIiwidHlwZSI6WyJWZXJpZmlhYmxlQ3JlZGVudGlhbCIsIldvdEF0dGVzdGF0aW9uIl0sInZhbGlkRnJvbSI6IjIwMjYtMDQtMjFUMTA6MDA6MDBaIn0.semxZPGYdkExNWs5vWh76XaqlPvZsCE3sZLxFOQMg1J4oALgf2QV8rPv2Q6bMCIygzcmEWKolJG3eRJxZdOBAA
```

## 4. ECIES (Sync 001)

Deterministischer Testvektor fuer das sonst zufaellige ECIES-Verfahren. In Produktion MUSS der ephemere Private Key zufaellig sein.

```
Recipient X25519 Public Key (Base64URL): yFB4c_1SqTGolVBTKhCBJShSWf-NzXr4XCyDF3FKeUQ
Ephemeral Private Key (hex): 000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f
Ephemeral Public Key (Base64URL): j0DFrbaPJWJK5bIU6nZ6bslNgp09e14a0bpvPiE4KF8
Shared Secret (hex): 1179ea1cdc7219cdb7a1167398653a65d679845fd5d6af8028f9f48d2ac11302
HKDF Info: wot/ecies/v1
AES Key (hex): 5c9e63d8ba44c750ac09ffbc25ff6889a07fa784634a9d25104f519cc76b5b21
Nonce (hex): 1a1b1c1d1e1f202122232425
Plaintext: Hello ECIES WoT
Ciphertext + Auth Tag (Base64URL): 0DkOSxhxP_lROCSisq2DAbveWqoA_M2E2kidsoVFdw
```

ECIES-Nachrichtenformat:

```json
{"epk":"j0DFrbaPJWJK5bIU6nZ6bslNgp09e14a0bpvPiE4KF8","nonce":"GhscHR4fICEiIyQl","ciphertext":"0DkOSxhxP_lROCSisq2DAbveWqoA_M2E2kidsoVFdw"}
```

## 5. Deterministische Log-Nonce und Payload-Verschluesselung (Sync 001/002)

```
Space Content Key (hex): 0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef
deviceId: 550e8400-e29b-41d4-a716-446655440000
seq: 42
Nonce = SHA-256(deviceId || "|" || seq)[0:12]
Nonce (hex): 7ae069db68aeb3161aa67131
Nonce (Base64URL): euBp22iusxYapnEx
Plaintext: {"op":"set","path":["title"],"value":"Hello WoT"}
Ciphertext + Auth Tag (hex): e852936e45c1669415dcb240c0e6387e18d69140a7b7d67ddcb0afaee01d200185bf4e74da522a28916a1ec0044de043471cf72ac3e1deac8790bd6ad53d66557a
Full Blob (Nonce | Ciphertext | Tag, Base64URL): euBp22iusxYapnEx6FKTbkXBZpQV3LJAwOY4fhjWkUCnt9Z93LCvruAdIAGFv0502lIqKJFqHsAETeBDRxz3KsPh3qyHkL1q1T1mVXo
```

## 6. Log-Entry JWS (Sync 002)

Payload (JCS):

```json
{"authorKid":"did:key:z6Mko3ZEjKJWQAM5nDXKoZ9jErvvxbWbYgS8KJXYpC5Hbu8a#sig-0","data":"euBp22iusxYapnEx6FKTbkXBZpQV3LJAwOY4fhjWkUCnt9Z93LCvruAdIAGFv0502lIqKJFqHsAETeBDRxz3KsPh3qyHkL1q1T1mVXo","deviceId":"550e8400-e29b-41d4-a716-446655440000","docId":"7f3a2b10-4c5d-4e6f-8a7b-9c0d1e2f3a4b","keyGeneration":3,"seq":42,"timestamp":"2026-04-17T10:00:00Z"}
```

JWS Compact:

```text
eyJhbGciOiJFZERTQSIsImtpZCI6ImRpZDprZXk6ejZNa28zWkVqS0pXUUFNNW5EWEtvWjlqRXJ2dnhiV2JZZ1M4S0pYWXBDNUhidThhI3NpZy0wIn0.eyJhdXRob3JLaWQiOiJkaWQ6a2V5Ono2TWtvM1pFaktKV1FBTTVuRFhLb1o5akVydnZ4YldiWWdTOEtKWFlwQzVIYnU4YSNzaWctMCIsImRhdGEiOiJldUJwMjJpdXN4WWFwbkV4NkZLVGJrWEJacFFWM0xKQXdPWTRmaGpXa1VDbnQ5WjkzTEN2cnVBZElBR0Z2MDUwMmxJcUtKRnFIc0FFVGVCRFJ4ejNLc1BoM3F5SGtMMXExVDFtVlhvIiwiZGV2aWNlSWQiOiI1NTBlODQwMC1lMjliLTQxZDQtYTcxNi00NDY2NTU0NDAwMDAiLCJkb2NJZCI6IjdmM2EyYjEwLTRjNWQtNGU2Zi04YTdiLTljMGQxZTJmM2E0YiIsImtleUdlbmVyYXRpb24iOjMsInNlcSI6NDIsInRpbWVzdGFtcCI6IjIwMjYtMDQtMTdUMTA6MDA6MDBaIn0.lIwGioTDMKdkkAkKnMTr1Eup-fnU7CcDVPiYSIM1-vsN0i--losDm8fwkKE5Lyn5Kmgo78nSGv2CJ9lEQ2PyDw
```

## 7. Space Capability JWS (Sync 003)

```
spaceCapabilitySigningKey Seed (hex): 202122232425262728292a2b2c2d2e2f303132333435363738393a3b3c3d3e3f
spaceCapabilityVerificationKey (hex): 29acbae141bccaf0b22e1a94d34d0bc7361e526d0bfe12c89794bc9322966dd7
spaceCapabilityVerificationKey (Multibase): z6MkhFwXNFWosLeugvSf4wcL9t3uuRXueGSFTRgSvHhWj5G2
```

Payload (JCS):

```json
{"audience":"did:key:z6Mko3ZEjKJWQAM5nDXKoZ9jErvvxbWbYgS8KJXYpC5Hbu8a","generation":3,"issuedAt":"2026-04-22T10:00:00Z","permissions":["read","write"],"spaceId":"7f3a2b10-4c5d-4e6f-8a7b-9c0d1e2f3a4b","type":"capability","validUntil":"2026-10-22T10:00:00Z"}
```

JWS Compact:

```text
eyJhbGciOiJFZERTQSIsImtpZCI6IndvdDpzcGFjZTo3ZjNhMmIxMC00YzVkLTRlNmYtOGE3Yi05YzBkMWUyZjNhNGIjY2FwLTMiLCJ0eXAiOiJ3b3QtY2FwYWJpbGl0eStqd3QifQ.eyJhdWRpZW5jZSI6ImRpZDprZXk6ejZNa28zWkVqS0pXUUFNNW5EWEtvWjlqRXJ2dnhiV2JZZ1M4S0pYWXBDNUhidThhIiwiZ2VuZXJhdGlvbiI6MywiaXNzdWVkQXQiOiIyMDI2LTA0LTIyVDEwOjAwOjAwWiIsInBlcm1pc3Npb25zIjpbInJlYWQiLCJ3cml0ZSJdLCJzcGFjZUlkIjoiN2YzYTJiMTAtNGM1ZC00ZTZmLThhN2ItOWMwZDFlMmYzYTRiIiwidHlwZSI6ImNhcGFiaWxpdHkiLCJ2YWxpZFVudGlsIjoiMjAyNi0xMC0yMlQxMDowMDowMFoifQ.lqBuMxntI15vmJCnT9UTavTQqM_sxbL4fcrt_n_cSakXE4fy-EFvnXWAngNq5uFYqPbX_r8W-TE16Md97pfWAQ
```

## 8. Space Membership Messages (Sync 005)

Diese Vektoren fixieren die Feldnamen fuer Space-Invite, Member-Update, Key-Rotation und Invite-Key-Discovery. Die Beispiel-Keys `abc_123` / `def_456` sind Platzhalter fuer Base64URL-kodiertes Key-Material; kryptographische Gueltigkeit der Capability wird im Space-Capability-Vektor separat geprueft.

Invite-Key-Discovery:

```json
{"canonical_key_agreement_id":"#enc-0","profile_encryption_public_key_alias_must_match":true,"x25519_public_b64":"yFB4c_1SqTGolVBTKhCBJShSWf-NzXr4XCyDF3FKeUQ","x25519_public_multibase":"z6LSqA7sbKGK3WVHP9SBcmv9ikp19iDNb1P5Q315kRPQrcTV"}
```

Space-Invite Body:

```json
{"adminDids":["did:key:z6MkvLMiE11z8wXjNScxqjcMJHNfNyc8XqDT4aGzry4pFTTd"],"brokerUrls":["wss://broker.example.com"],"capability":"aaa.bbb.ccc","currentKeyGeneration":3,"spaceCapabilitySigningKey":"def_456","spaceContentKeys":[{"generation":3,"key":"abc_123"}],"spaceId":"7f3a2b10-4c5d-4e6f-8a7b-9c0d1e2f3a4b"}
```

Member-Update Body:

```json
{"action":"removed","effectiveKeyGeneration":4,"memberDid":"did:key:z6MkpTHR8VNsBxYAAWHut2Geadd9jSwuBV8xRoAnwWsdvktH","members":["did:key:z6Mko3ZEjKJWQAM5nDXKoZ9jErvvxbWbYgS8KJXYpC5Hbu8a"],"spaceId":"7f3a2b10-4c5d-4e6f-8a7b-9c0d1e2f3a4b"}
```

Key-Rotation Body:

```json
{"capability":"aaa.bbb.ccc","generation":4,"spaceCapabilitySigningKey":"def_456","spaceContentKey":"abc_123","spaceId":"7f3a2b10-4c5d-4e6f-8a7b-9c0d1e2f3a4b"}
```

## 9. Admin-Key-Ableitung (Sync 001/005)

```
spaceId: 7f3a2b10-4c5d-4e6f-8a7b-9c0d1e2f3a4b
HKDF Info: wot/space-admin/7f3a2b10-4c5d-4e6f-8a7b-9c0d1e2f3a4b/v1
Admin Ed25519 Seed: 6687124c044cdcc7b7468905582571fb4bb652ab9c5d58830a92a856e03dd2a6
Admin Public Key: ebf654f331fdbf131ca46ce2f28b269ceee064244e521b557a3e919bffe32c30
Admin DID: did:key:z6MkvLMiE11z8wXjNScxqjcMJHNfNyc8XqDT4aGzry4pFTTd
```

## 10. Personal-Doc-Key und Document-ID (Sync 006)

```
HKDF Info: wot/personal-doc/v1
Personal Doc Key: ed3b3cbec944063041a15cf14be4c2aecd87ec30f2085cd9f2f82333cfcd437c
Document-ID: ed3b3cbe-c944-0630-41a1-5cf14be4c2ae
```

## 11. SD-JWT VC Trust List (H01/H03)

Minimaler Draft-Vektor fuer eine Trust-List mit einem selectively-disclosable Eintrag.

Disclosure JSON (JCS):

```json
["salt-0001","entry",{"hopLimit":2,"id":"did:key:z6Mko3ZEjKJWQAM5nDXKoZ9jErvvxbWbYgS8KJXYpC5Hbu8a","liability":"4.0h","trustLevel":3}]
```

```
Disclosure (Base64URL): WyJzYWx0LTAwMDEiLCJlbnRyeSIseyJob3BMaW1pdCI6MiwiaWQiOiJkaWQ6a2V5Ono2TWtvM1pFaktKV1FBTTVuRFhLb1o5akVydnZ4YldiWWdTOEtKWFlwQzVIYnU4YSIsImxpYWJpbGl0eSI6IjQuMGgiLCJ0cnVzdExldmVsIjozfV0
Digest = BASE64URL(SHA-256(ASCII(disclosure))): IgJ4myRVC6HCY4dk1zsagaGdOlXsm_21Uj7EFPQ74sY
```

SD-JWT VC Compact Serialization:

```text
eyJhbGciOiJFZERTQSIsImtpZCI6ImRpZDprZXk6ejZNa28zWkVqS0pXUUFNNW5EWEtvWjlqRXJ2dnhiV2JZZ1M4S0pYWXBDNUhidThhI3NpZy0wIiwidHlwIjoidmMrc2Qtand0In0.eyJfc2RfYWxnIjoic2hhLTI1NiIsImVudHJpZXMiOlt7Il9zZCI6WyJJZ0o0bXlSVkM2SENZNGRrMXpzYWdhR2RPbFhzbV8yMVVqN0VGUFE3NHNZIl19XSwiZXhwIjoxODA4MDUwODAwLCJpYXQiOjE3NzY1MTQ4MDAsImlzcyI6ImRpZDprZXk6ejZNa28zWkVqS0pXUUFNNW5EWEtvWjlqRXJ2dnhiV2JZZ1M4S0pYWXBDNUhidThhIiwidmN0IjoiaHR0cHM6Ly9odW1hbm1vbmV5LmV4YW1wbGUvY3JlZGVudGlhbHMvVHJ1c3RMaXN0L3YxIiwidmVyc2lvbiI6MTJ9.yDMUg74umfxSnD7RJUSIj3NYu7ml6wSv9W7tLocVdPBIJ0hil-QuIT9lkAFSyGV9Qa2ctEBTon8wxNvbUwuRCg~WyJzYWx0LTAwMDEiLCJlbnRyeSIseyJob3BMaW1pdCI6MiwiaWQiOiJkaWQ6a2V5Ono2TWtvM1pFaktKV1FBTTVuRFhLb1o5akVydnZ4YldiWWdTOEtKWFlwQzVIYnU4YSIsImxpYWJpbGl0eSI6IjQuMGgiLCJ0cnVzdExldmVsIjozfV0~
```
