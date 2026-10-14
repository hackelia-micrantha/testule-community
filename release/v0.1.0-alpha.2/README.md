# Testule 0.1.0-alpha.2 public artifact projection

Canonical implementation release:

- version: `0.1.0-alpha.2`
- canonical repository: `hackelia-micrantha/testule`
- canonical commit: `879e6f7a0a74ece2c12fcc4a7b16d05387b832ea`
- canonical release workflow: `38508113197`
- runtime platform: `linux-amd64`
- runtime SHA-256: `a5cabc19d233e84fbd880cdcdbcdc682f51141c31e39f0677ac1a144cdf02cec`
- public-contract SHA-256: `beeff1932d9b7725c16ee7e6dcf3d1d9c7b4dad1b9300009b9b2ed3f0603c626`
- projection-manifest SHA-256: `9c8e0e08941e40b2dc8604841e38f062fc6b4272782fd8e6dc7a81a362f957cc`

The canonical payload was independently retrieved from the authenticated
canonical workflow artifact and verified against `SHA256SUMS`, provenance,
archive structure, ELF runtime identity, man-page version identity, and the
projected contract manifest.

This commit is the public **artifact-distribution identity**. The binary Nix
package is qualified separately after these exact files are available from the
public release URL.

## Promotion

Run:

```sh
scripts/promote-public-release.sh \
  /path/to/testule-release-v0.1.0-alpha.2 \
  <this-merged-main-commit>
```

The helper creates/verifies the exact lightweight `v0.1.0-alpha.2` tag,
uploads exactly five assets to a draft prerelease, checks all GitHub-reported
SHA-256 digests while the release is still draft, and only then publishes it.

After publication run `scripts/verify-public-release-assets.sh` from this
commit. Package/cache-miss Nix qualification remains a separate downstream
gate in #4.
