# Repository topology

Testule uses the Micrantha private-canonical/public-distribution pattern.

```text
private canonical implementation
hackelia-micrantha/testule
  - implementation source
  - internal packages
  - development tooling and fixtures
  - private security/adversarial material
  - release build authority
            |
            | explicit projection at reviewed release identity
            v
public specification/distribution
hackelia-micrantha/testule-community
  - RFCs and compatibility contracts
  - public adapter and Evidence semantics
  - operator/man documentation
  - release artifacts
  - checksums/provenance/SBOM
  - binary-consumption flake
            |
            | exact tag/revision + committed flake.lock
            v
consumers such as Dubnium/dotfiles
```

## Invariants

1. `testule` is the implementation and release authority; `testule-community` is never a second implementation authority.
2. Public consumers do not import canonical source-tree or internal package paths.
3. Public contracts are versioned independently enough to permit third-party implementations and conformance testing.
4. A release projection is immutable and attributable to an exact canonical source revision.
5. Public artifacts are inspected after packaging so implementation source, credentials, private corpora, `.git` state, development fixtures, and unintended local state are not published.
6. Checksums, provenance, SBOM, artifact names, CLI version, man-page version, and release tag describe one release identity.
7. Package installation grants executable availability only; it does not grant filesystem, network, process, secret, device, or mutation authority.
8. Cache-miss installation from the declared public surface must not require private repository credentials.
9. Previously public Testule source is treated as permanently disclosed. The split protects future implementation evolution; it does not attempt to revoke historical publication.

## Projection rule

Nothing is mirrored automatically merely because it exists in the canonical repository. The release/publication workflow owns an explicit allowlist of public material and fails closed when an unexpected path would be projected.

The allowlist initially includes:

- `docs/rfcs/**` public RFCs;
- public CLI/Evidence/adapter contract documentation;
- `man/man1/testule.1`;
- release notes and compatibility metadata;
- packaged runtime artifacts and their integrity/provenance metadata.

Development documentation, implementation source, internal packages, test fixtures/corpora, CI internals, and local tooling remain private unless explicitly reclassified.
