# Release projection

Testule releases originate from the private canonical implementation repository and are projected here as immutable public distribution artifacts.

## Release identity

One authoritative version/revision must bind all public release material:

- canonical source revision;
- release tag/version;
- `testule --version`;
- artifact names;
- man-page version/date metadata where applicable;
- SHA-256 checksums;
- provenance/attestation metadata;
- SBOM identity;
- Nix package metadata.

A projection is rejected when these disagree.

## Required public release contents

For each supported platform, publish the runtime archive containing at minimum:

```text
bin/testule
share/man/man1/testule.1
```

The release also publishes:

- SHA-256 checksum manifest;
- provenance/attestation binding the artifact to the canonical source revision and build workflow;
- SBOM where deterministic tooling supports it;
- release notes and compatibility/migration notes when required;
- the public specification snapshot applicable to the release.

## Post-package inspection

Release validation occurs against the constructed artifact, not only the source tree. The release fails if the public artifact includes unintended material such as:

- implementation source not explicitly classified public;
- credentials or secret material;
- private corpora or protected verifier fixtures;
- repository `.git` state;
- local caches/state;
- development-only tests and fixtures not needed at runtime;
- host-specific configuration or private paths.

## Promotion verification

Before any canonical payload is promoted into this public repository, verify the
already-built release bundle locally:

```sh
python3 scripts/verify-canonical-release.py \
  /path/to/canonical-release-payload \
  <version> \
  <canonical-40-char-commit>
```

The verifier is intentionally **artifact-only**. It never fetches the private
canonical repository. It requires exactly the canonical runtime archive,
public-contract archive, `SHA256SUMS`, `provenance.json`, and
`buildinfo.txt`; rejects unexpected archive members, links, traversal, and
extra payload files; verifies both archive digests; validates the exact
provenance identity; checks the projected contract manifest; and requires the
runtime and public-contract copies of `testule(1)` to be byte-identical.

For the first release, the intended version is `0.1.0-alpha.1`. Do not record
an artifact hash or public package derivation until the canonical
`v0.1.0-alpha.1` workflow has completed successfully and the verifier has
accepted its actual payload.

## Nix consumption

The public Nix flake is added with the first projected immutable binary release. It must consume public release artifacts and verify their hashes; it must not build from or fetch the private canonical source repository.

Expected consumer shape:

```nix
inputs.testule.url = "github:hackelia-micrantha/testule-community/<immutable-tag-or-rev>";
```

Consumers commit `flake.lock` and use the exported package/app surface. Cache-miss installation must remain possible without private credentials.

## Security

Repository visibility does not protect any source that was previously public. Historical Testule implementation source is treated as disclosed. The private-canonical topology is a forward-looking exposure boundary, not retroactive secrecy.

Signing/attestation keys or credentials are never copied into this repository. Prefer managed/keyless provenance when the release pipeline adds signing.
