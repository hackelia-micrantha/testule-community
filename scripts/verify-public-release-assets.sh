#!/usr/bin/env bash
set -euo pipefail

repo=hackelia-micrantha/testule-community
version=$(tr -d '\r\n' < VERSION)
tag="v$version"
canonical_commit=879e6f7a0a74ece2c12fcc4a7b16d05387b832ea
release_dir="release/$tag"
runtime="testule-$version-linux-amd64.tar.gz"
contracts="testule-$version-public-contracts.tar.gz"
base="https://github.com/$repo/releases/download/$tag"

for cmd in curl python3 sha256sum cmp mktemp; do
  command -v "$cmd" >/dev/null || {
    echo "required command unavailable: $cmd" >&2
    exit 69
  }
done

work=$(mktemp -d)
cleanup() { rm -rf -- "$work"; }
trap cleanup EXIT

for name in "$runtime" "$contracts" SHA256SUMS provenance.json buildinfo.txt; do
  curl --fail --location --silent --show-error \
    --retry 2 \
    "$base/$name" \
    --output "$work/$name"
done

python3 scripts/verify-canonical-release.py \
  "$work" \
  "$version" \
  "$canonical_commit"

cmp "$work/SHA256SUMS" "$release_dir/SHA256SUMS"
cmp "$work/provenance.json" "$release_dir/provenance.json"
cmp "$work/buildinfo.txt" "$release_dir/buildinfo.txt"

expected_runtime=$(awk -v name="$runtime" '$2 == name {print $1}' "$release_dir/SHA256SUMS")
expected_contracts=$(awk -v name="$contracts" '$2 == name {print $1}' "$release_dir/SHA256SUMS")
[[ "$(sha256sum "$work/$runtime" | awk '{print $1}')" == "$expected_runtime" ]]
[[ "$(sha256sum "$work/$contracts" | awk '{print $1}')" == "$expected_contracts" ]]

echo "verified public Testule $version release assets"
