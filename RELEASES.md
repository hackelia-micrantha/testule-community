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

The first successful canonical payload is `0.1.0-alpha.2`, built from canonical
commit `879e6f7a0a74ece2c12fcc4a7b16d05387b832ea`. Its runtime SHA-256 is
`a5cabc19d233e84fbd880cdcdbcdc682f51141c31e39f0677ac1a144cdf02cec`.
The public package may use this hash only after those exact bytes are uploaded
to this repository's immutable `v0.1.0-alpha.2` release surface.

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

## Public promotion commands

The remaining release mutation is intentionally explicit and fail closed. From a checkout of the exact reviewed public-package commit, with the verified canonical five-file payload available locally:

```sh
scripts/promote-public-release.sh \
  /path/to/testule-release-v0.1.0-alpha.2 \
  <exact-public-target-commit>
```

The helper re-runs the artifact-only verifier, byte-compares the checked-in checksum/provenance/build-info records, requires an exact existing public target commit, refuses to overwrite an existing release, and uploads exactly the five reviewed files.

Then qualify the public boundary without canonical-private credentials:

```sh
scripts/verify-public-release.sh
```

Qualification downloads all five assets from the public community release URL, re-runs the canonical payload verifier, compares checked-in metadata, rechecks archive SHA-256 values, and runs `nix flake check`. A machine without Nix may verify the public payload but cannot complete package acceptance.
