# Testule 0.1.0-alpha.2 public projection

Canonical implementation release:

- version: `0.1.0-alpha.2`
- canonical repository: `hackelia-micrantha/testule`
- canonical commit: `879e6f7a0a74ece2c12fcc4a7b16d05387b832ea`
- canonical release workflow: `38508113197`
- runtime platform: `linux-amd64`
- runtime SHA-256: `a5cabc19d233e84fbd880cdcdbcdc682f51141c31e39f0677ac1a144cdf02cec`
- public-contract SHA-256: `beeff1932d9b7725c16ee7e6dcf3d1d9c7b4dad1b9300009b9b2ed3f0603c626`
- projection-manifest SHA-256: `9c8e0e08941e40b2dc8604841e38f062fc6b4272782fd8e6dc7a81a362f957cc`

The canonical payload was independently retrieved through the authenticated
release workflow artifact and verified against `SHA256SUMS`, provenance,
archive structure, ELF runtime identity, man-page version identity, and the
projected contract manifest.

## Public promotion gate

The public release is not complete until the exact canonical runtime archive,
public-contract archive, `SHA256SUMS`, `provenance.json`, and
`buildinfo.txt` are uploaded to this repository's immutable
`v0.1.0-alpha.2` release surface.

The Nix flake deliberately fetches only that future public release URL. It does
not fetch or build canonical private source, and it does not point at the
private canonical release.


## Operator commands

Promote the exact verified canonical payload with
`scripts/promote-public-release.sh`, then prove the public/cache-miss boundary
with `scripts/verify-public-release.sh`. Do not merge the package PR merely
because release creation succeeded; public download plus `nix flake check`
must both pass.
