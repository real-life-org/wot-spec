#!/usr/bin/env python3
import base64
import hashlib
import json
from pathlib import Path

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ed25519, x25519
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF


ROOT = Path(__file__).resolve().parents[1]
VECTOR = ROOT / "test-vectors" / "phase-1-interop.json"
DEVICE_VECTOR = ROOT / "test-vectors" / "device-delegation.json"
B58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def b64u_decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def b64u_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def b58encode(data: bytes) -> str:
    num = int.from_bytes(data, "big")
    out = ""
    while num:
        num, rem = divmod(num, 58)
        out = B58_ALPHABET[rem] + out
    pad = len(data) - len(data.lstrip(b"\x00"))
    return "1" * pad + (out or "1")


def b58decode(value: str) -> bytes:
    num = 0
    for char in value:
        num = num * 58 + B58_ALPHABET.index(char)
    data = num.to_bytes((num.bit_length() + 7) // 8, "big")
    pad = len(value) - len(value.lstrip("1"))
    return b"\x00" * pad + data


def jcs(value) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def hkdf(ikm: bytes, info: str, length: int = 32) -> bytes:
    return HKDF(
        algorithm=hashes.SHA256(),
        length=length,
        salt=bytes(32),
        info=info.encode("ascii"),
    ).derive(ikm)


def ed_public(seed: bytes) -> bytes:
    return ed25519.Ed25519PrivateKey.from_private_bytes(seed).public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )


def x_public(seed: bytes) -> bytes:
    return x25519.X25519PrivateKey.from_private_bytes(seed).public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )


def did_key_ed(public_key: bytes) -> str:
    return "did:key:z" + b58encode(bytes.fromhex("ed01") + public_key)


def multibase_ed(public_key: bytes) -> str:
    return "z" + b58encode(bytes.fromhex("ed01") + public_key)


def ed_public_from_did_key(did_or_kid: str) -> bytes:
    did = did_or_kid.split("#", 1)[0]
    if not did.startswith("did:key:z"):
        raise ValueError("expected did:key")
    decoded = b58decode(did[len("did:key:z") :])
    if not decoded.startswith(bytes.fromhex("ed01")):
        raise ValueError("expected Ed25519 did:key")
    return decoded[2:]


def multibase_x(public_key: bytes) -> str:
    return "z" + b58encode(bytes.fromhex("ec01") + public_key)


def verify_jws(jws: str, public_key: bytes) -> None:
    header_b64, payload_b64, sig_b64 = jws.split(".")
    ed25519.Ed25519PublicKey.from_public_bytes(public_key).verify(
        b64u_decode(sig_b64), f"{header_b64}.{payload_b64}".encode("ascii")
    )


def decode_jws(jws: str) -> tuple[dict, dict]:
    header_b64, payload_b64, _ = jws.split(".")
    return json.loads(b64u_decode(header_b64)), json.loads(b64u_decode(payload_b64))


def iso_to_unix(value: str) -> int:
    from datetime import datetime

    return int(datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp())


def verify_delegated_attestation_bundle(bundle: dict, required_capability: str = "sign-attestation") -> None:
    assert bundle["type"] == "wot-delegated-attestation-bundle/v1"

    att_header, att_payload = decode_jws(bundle["attestationJws"])
    binding_header, binding_payload = decode_jws(bundle["deviceKeyBindingJws"])

    assert binding_header["alg"] == "EdDSA"
    assert binding_header["typ"] == "wot-device-key-binding+jwt"
    assert binding_payload["type"] == "device-key-binding"
    assert binding_header["kid"].split("#", 1)[0] == binding_payload["iss"]

    identity_pub = ed_public_from_did_key(binding_header["kid"])
    verify_jws(bundle["deviceKeyBindingJws"], identity_pub)

    assert binding_payload["sub"] == binding_payload["deviceKid"]
    assert att_header["kid"] == binding_payload["deviceKid"]
    assert binding_payload["devicePublicKeyMultibase"] == multibase_ed(ed_public_from_did_key(binding_payload["deviceKid"]))

    device_pub = ed_public_from_did_key(binding_payload["deviceKid"])
    verify_jws(bundle["attestationJws"], device_pub)

    assert att_payload["issuer"] == binding_payload["iss"]
    assert att_payload["iss"] == binding_payload["iss"]
    assert required_capability in binding_payload["capabilities"]
    assert "iat" in att_payload
    assert iso_to_unix(binding_payload["validFrom"]) <= att_payload["iat"] <= iso_to_unix(binding_payload["validUntil"])


def main() -> None:
    data = json.loads(VECTOR.read_text(encoding="utf-8"))
    identity = data["identity"]
    seed = bytes.fromhex(identity["bip39_seed_hex"])

    ed_seed = hkdf(seed, "wot/identity/ed25519/v1")
    ed_pub = ed_public(ed_seed)
    x_seed = hkdf(seed, "wot/encryption/x25519/v1")
    x_pub = x_public(x_seed)
    assert ed_seed.hex() == identity["ed25519_seed_hex"]
    assert ed_pub.hex() == identity["ed25519_public_hex"]
    assert did_key_ed(ed_pub) == identity["did"]
    assert x_seed.hex() == identity["x25519_seed_hex"]
    assert x_pub.hex() == identity["x25519_public_hex"]
    assert b64u_encode(x_pub) == identity["x25519_public_b64"]
    print("identity ok")

    did_doc = data["did_resolution"]
    assert did_doc["did_document"]["id"] == identity["did"]
    assert did_doc["did_document"]["verificationMethod"][0]["publicKeyMultibase"] == multibase_ed(ed_pub)
    assert did_doc["did_document"]["keyAgreement"][0]["publicKeyMultibase"] == multibase_x(x_pub)
    assert hashlib.sha256(jcs(did_doc["did_document"])).hexdigest() == did_doc["jcs_sha256"]
    print("did resolution ok")

    attestation = data["attestation_vc_jws"]
    header_b64, payload_b64, sig_b64 = attestation["jws"].split(".")
    assert json.loads(b64u_decode(header_b64)) == attestation["header"]
    assert json.loads(b64u_decode(payload_b64)) == attestation["payload"]
    assert hashlib.sha256(jcs(attestation["payload"])).hexdigest() == attestation["payload_jcs_sha256"]
    assert f"{header_b64}.{payload_b64}" == attestation["signing_input"]
    assert sig_b64 == attestation["signature_b64"]
    assert attestation["header"]["typ"] == "vc+jwt"
    assert attestation["header"]["kid"] == identity["kid"]
    assert attestation["payload"]["issuer"] == identity["did"]
    assert attestation["payload"]["iss"] == identity["did"]
    assert attestation["payload"]["credentialSubject"]["id"] == attestation["payload"]["sub"]
    verify_jws(attestation["jws"], ed_pub)
    print("attestation vc jws ok")

    ecies = data["ecies"]
    eph_public = b64u_decode(ecies["ephemeral_public_b64"])
    shared = x25519.X25519PrivateKey.from_private_bytes(x_seed).exchange(
        x25519.X25519PublicKey.from_public_bytes(eph_public)
    )
    assert shared.hex() == ecies["shared_secret_hex"]
    aes_key = hkdf(shared, ecies["hkdf_info"])
    assert aes_key.hex() == ecies["aes_key_hex"]
    plaintext = AESGCM(aes_key).decrypt(
        bytes.fromhex(ecies["nonce_hex"]), b64u_decode(ecies["ciphertext_b64"]), None
    )
    assert plaintext.decode("utf-8") == ecies["plaintext"]
    print("ecies ok")

    log_enc = data["log_payload_encryption"]
    nonce = hashlib.sha256(f"{log_enc['device_id']}|{log_enc['seq']}".encode("ascii")).digest()[:12]
    assert nonce.hex() == log_enc["nonce_hex"]
    ciphertext = AESGCM(bytes.fromhex(log_enc["space_content_key_hex"])).encrypt(
        nonce, log_enc["plaintext"].encode("utf-8"), None
    )
    assert ciphertext.hex() == log_enc["ciphertext_tag_hex"]
    assert b64u_encode(nonce + ciphertext) == log_enc["blob_b64"]
    print("log encryption ok")

    verify_jws(data["log_entry_jws"]["jws"], ed_pub)
    print("log jws ok")

    cap = data["space_capability_jws"]
    cap_pub = bytes.fromhex(cap["verification_key_hex"])
    verify_jws(cap["jws"], cap_pub)
    print("capability jws ok")

    admin = data["admin_key_derivation"]
    admin_seed = hkdf(seed, admin["hkdf_info"])
    admin_pub = ed_public(admin_seed)
    assert admin_seed.hex() == admin["ed25519_seed_hex"]
    assert admin_pub.hex() == admin["ed25519_public_hex"]
    assert did_key_ed(admin_pub) == admin["did"]
    print("admin key ok")

    personal = data["personal_doc"]
    personal_key = hkdf(seed, personal["hkdf_info"])
    assert personal_key.hex() == personal["key_hex"]
    raw_doc = personal_key[:16]
    doc_id = f"{raw_doc[:4].hex()}-{raw_doc[4:6].hex()}-{raw_doc[6:8].hex()}-{raw_doc[8:10].hex()}-{raw_doc[10:].hex()}"
    assert doc_id == personal["doc_id"]
    print("personal doc ok")

    sd = data["sd_jwt_vc_trust_list"]
    disclosure = b64u_encode(jcs(sd["disclosure"])).encode("ascii")
    digest = b64u_encode(hashlib.sha256(disclosure).digest())
    assert digest == sd["disclosure_digest"]
    verify_jws(sd["issuer_signed_jwt"], ed_pub)
    assert sd["sd_jwt_compact"] == f"{sd['issuer_signed_jwt']}~{disclosure.decode('ascii')}~"
    print("sd-jwt vc ok")

    device_data = json.loads(DEVICE_VECTOR.read_text(encoding="utf-8"))
    device = device_data["device"]
    device_seed = bytes.fromhex(device["seed_hex"])
    device_pub = ed_public(device_seed)
    assert device_pub.hex() == device["ed25519_public_hex"]
    assert did_key_ed(device_pub) == device["did"]
    assert multibase_ed(device_pub) == device["publicKeyMultibase"]

    binding = device_data["device_key_binding_jws"]
    assert decode_jws(binding["jws"]) == (binding["header"], binding["payload"])
    assert hashlib.sha256(jcs(binding["payload"])).hexdigest() == binding["payload_jcs_sha256"]
    verify_jws(binding["jws"], ed_pub)
    print("device key binding jws ok")

    delegated = device_data["delegated_attestation_bundle"]
    assert decode_jws(delegated["attestationJws"]) == (delegated["attestationHeader"], delegated["attestationPayload"])
    verify_delegated_attestation_bundle(delegated["bundle"])
    print("delegated attestation bundle ok")

    for name, invalid in device_data["invalid_cases"].items():
        try:
            verify_delegated_attestation_bundle(invalid["bundle"])
        except Exception:
            continue
        raise AssertionError(f"invalid delegated-attestation case accepted: {name}")
    print("delegated attestation invalid cases ok")


if __name__ == "__main__":
    main()
