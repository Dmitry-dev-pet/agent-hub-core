# Security

Truthrail Core is designed so secret values and generic privileged execution are
outside the protocol.

Please do not report secret values in a public issue. If a vulnerability could expose
credentials, bypass `agent_routable`, broaden an execution envelope, or turn a
reviewed control plane into generic execution, use GitHub's private security advisory
workflow for this repository.

Security-sensitive protocol invariants:

- no secret values in WorkPacket/HandoffPacket/receipts;
- no implicit AI access to control-plane operations;
- `agent_routable: true` must be explicit;
- `executed` is not verification;
- authoritative live state must be re-read when freshness matters.
