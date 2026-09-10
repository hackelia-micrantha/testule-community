# Testule Community

Public specification and distribution surface for Testule.

Testule provides portable testability contracts, normalized evidence, gap analysis, and bounded testing capabilities while delegating execution to ecosystem-native tools.

## Repository role

This repository is intentionally public. It contains the material required to understand, integrate with, verify, and consume Testule without exposing the canonical implementation source.

Public surface:

- accepted and draft RFCs that define Testule contracts;
- CLI and Unix-composability contracts;
- Evidence and streaming semantics;
- adapter-facing documentation intended as public contract;
- operator documentation and man pages;
- compatibility and release policy;
- immutable release artifacts, checksums, provenance, and SBOMs when releases are published;
- a binary-consumption Nix flake once the first immutable release exists.

Not published here:

- canonical implementation source;
- internal packages and implementation details;
- development-only tooling and fixtures;
- private security/adversarial corpora;
- release credentials or private CI state.

## Source and release authority

The canonical implementation is maintained separately. Public releases are projected into this repository as immutable, attributable artifacts. A release is authoritative only when its version, artifact digests, provenance, and published contract material agree.

The public contract is independently usable: consumers and third-party implementations should depend on documented Testule schemas/semantics rather than implementation internals.

## Current maturity

Testule is incubating. The current public interface is `v1alpha1`; incompatible contract changes remain possible and must cross an explicit version boundary when required.

There is not yet a published binary release. Until the first release projection lands, this repository is the public specification/distribution staging surface rather than a source-building package repository.

## Security boundary

Repository visibility is not a security control for material that was previously public. Historical Testule source should be treated as disclosed. The public/private split protects future implementation evolution and reduces unnecessary source exposure; it does not revoke already published history.

Package installation grants executable availability only. Filesystem, process, network, secret, device, and mutation authority remain explicit capability-host concerns.

## License

Public Testule specification and distribution material is published under Apache License 2.0 unless a file states otherwise.
