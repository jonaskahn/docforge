# Contract system

_Last reviewed: {{YYYY-MM-DD}}_

_Repeat per contract in the system._

## {{Contract name}}

**Network(s):** {{deployed networks}}

**Upgrade boundary:** {{immutable | proxy-upgradeable | governance-gated}}

**Evidence status:** {{audits performed, by whom, when — or `unaudited`; never
assert a safety verdict this document cannot support}}

**Residual risk:** {{what remains accepted and unmitigated, stated plainly}}

| Storage item | Purpose |
|---|---|
| {{item}} | {{purpose}} |

**Privileged authorities**

| Authority | Can call | Held by |
|---|---|---|
| {{role}} | {{functions}} | {{account / multisig / governance}} |

Economic and security invariants: see
[economic-invariants.md](economic-invariants.md).
