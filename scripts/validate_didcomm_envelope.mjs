import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const { Message } = require("didcomm-node");
const { DIDComm } = await import("@veramo/did-comm");

const vector = await import("../test-vectors/phase-1-interop.json", { with: { type: "json" } });
const message = vector.default.didcomm_plaintext_envelope.message;
const packed = JSON.stringify(message);

const didResolver = { resolve: async () => null };
const secretsResolver = { get_secret: async () => null, find_secrets: async () => [] };

const [sicpaMessage, sicpaMeta] = await Message.unpack(packed, didResolver, secretsResolver, {});
const sicpaValue = sicpaMessage.as_value();
if (sicpaValue.typ !== "application/didcomm-plain+json" || sicpaMeta.encrypted !== false) {
  throw new Error("didcomm-node did not unpack WoT message as plaintext DIDComm");
}
console.log("didcomm-node ok");

const veramo = new DIDComm();
const mediaType = await veramo.getDidCommMessageMediaType({ message: packed });
const unpacked = await veramo.unpackDIDCommMessage({ message: packed }, { agent: {} });
if (mediaType !== "application/didcomm-plain+json" || unpacked.metaData.packing !== "none") {
  throw new Error("@veramo/did-comm did not unpack WoT message as plaintext DIDComm");
}
console.log("@veramo/did-comm ok");
