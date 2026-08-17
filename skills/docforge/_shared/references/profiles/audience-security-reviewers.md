# Security reviewer audience profile

Select the `security-reviewers` audience when readers need a reviewable
account of assets, trust boundaries, controls, residual risk, and the
evidence behind each conclusion. It is not a vulnerability assessment and
must not claim that a control is effective merely because related code
exists.

## Generated structure

```text
SECURITY.md                                # reporting scope and safe harbor
docs/security/
├── README.md
├── threat-model.md
├── data-handling.md                       # selected when data handling is evidenced
└── <surface-specific control document>    # selected by shape and evidence
```

Surface-specific documents cover API authentication, platform permissions,
or smart-contract economic invariants. Include only the controls that the
catalog selects; security documentation must retain its stated scope rather
than imply coverage of absent surfaces.

## Content ownership

### `SECURITY.md` and `README.md`

`SECURITY.md` owns supported scope, reporting, response expectations, and
safe harbor. The security index routes to the review documents that exist.
Neither asserts a threat, control, or risk acceptance owned by a child
document.

### Threat model

For every evidenced concern, connect asset, trust boundary, threat, control,
control evidence, residual risk, and risk disposition. Separate implemented
controls from assumptions, compensating controls, and external review
results. An unverified boundary or accepted-risk owner remains unresolved,
not inferred.

### Data and surface controls

Data handling owns classification, lifecycle, access, retention, and
deletion. API authentication, permissions, and economic invariants own their
respective public or privileged contracts. Link operational credential
handling and recovery constraints to their operations owner instead of
restating procedures.

## Evidence recipe

Follow the evidence loop in [`source-analysis.md`](../source-analysis.md):

1. Use the selected code graph to identify public interfaces, privileged
   paths, data stores, trust-boundary crossings, dependencies, and
   enforcement points.
2. Confirm control behavior with source, configuration, tests, and manifests.
3. Use history and existing security records for rationale or accepted-risk
   evidence.
4. Treat threat likelihood, severity, risk ownership, compliance status,
   secret inventory, and external test results as external evidence unless
   recorded.
